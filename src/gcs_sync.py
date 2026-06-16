import os
import subprocess
import threading
import time
from src.incident import get_discover_dir

# Global sync state
_sync_status = "OFFLINE"
_sync_lock = threading.Lock()

def _resolve_rails_env() -> str:
    """Resolves friendly environment names to standard Rails environments."""
    env = os.getenv("SRE_ENV")
    if not env and "PYTEST_CURRENT_TEST" in os.environ:
        env = "test"
    if not env:
        env = os.getenv("RAILS_ENV") or "development"
    env = env.lower().strip()
    if env in ("prod", "production"):
        return "production"
    elif env in ("test", "testing"):
        return "test"
    else:
        return "development"

def _load_gcs_config() -> dict:
    """Loads GCS config from etc/gcs.yaml if present."""
    config_path = os.path.join("etc", "gcs.yaml")
    if os.path.exists(config_path):
        try:
            import yaml
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            if isinstance(config, dict):
                return config
        except Exception as e:
            print(f"[GCS Sync] Error loading etc/gcs.yaml: {e}")
    return {}

def get_gcs_folder_path() -> str:
    """Returns the configured or default GCS folder path/prefix within the bucket."""
    rails_env = _resolve_rails_env()
    config = _load_gcs_config()
    if rails_env in config:
        env_config = config[rails_env]
        if isinstance(env_config, dict):
            folder_val = env_config.get("gcs_folder")
            if folder_val:
                folder_str = str(folder_val).strip("'\"/ ")
                if folder_str:
                    return f"{folder_str}/"
    return f"discovery/{rails_env}/"

def get_gcs_bucket_name() -> str:
    """Returns the configured or default GCS bucket name."""
    bucket = os.getenv("GCS_BUCKET")
    if bucket:
        return bucket.strip("'\"")
    
    rails_env = _resolve_rails_env()
    config = _load_gcs_config()
    if rails_env in config:
        env_config = config[rails_env]
        if isinstance(env_config, dict):
            bucket_val = env_config.get("gcs_bucket")
            if bucket_val:
                return str(bucket_val).strip("'\"")

    project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("PROJECT_ID")
    if project_id:
        proj = project_id.strip("'\"")
        return f"{proj}-sre-benjamin-discovery"
    return ""

def is_gcs_enabled() -> bool:
    """Checks if GCS sync is enabled and a bucket name is resolved."""
    if os.getenv("MOCK_TOOLING", "false").lower() == "true":
        return False
    
    rails_env = _resolve_rails_env()
    if rails_env == "test":
        return False

    config = _load_gcs_config()
    if rails_env in config:
        env_config = config[rails_env]
        if isinstance(env_config, dict) and "gcs_enabled" in env_config:
            if not env_config["gcs_enabled"]:
                return False
            return bool(get_gcs_bucket_name())
    
    # Default behavior if YAML or key is not present
    if rails_env == "production":
        return bool(get_gcs_bucket_name())
    return False


def get_sync_status() -> str:
    """Returns the current GCS Sync status (OFFLINE, IDLE, SYNCING, SUCCESS, FAILED)."""
    global _sync_status
    if not is_gcs_enabled():
        return "OFFLINE"
    return _sync_status

def set_sync_status(status: str):
    """Sets the GCS Sync status thread-safely."""
    global _sync_status
    with _sync_lock:
        _sync_status = status

class GcsSyncManager:
    @staticmethod
    def run_command(args: list[str]) -> bool:
        """Helper to run a subprocess command safely returning success status."""
        try:
            # Propagate secure authentication variables if impersonation is active
            env = os.environ.copy()
            res = subprocess.run(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                timeout=30
            )
            if res.returncode != 0:
                print(f"[GCS Sync] Command {' '.join(args)} failed with returncode {res.returncode}. Stderr: {res.stderr.strip()}")
                return False
            return True
        except Exception as e:
            print(f"[GCS Sync] Exception running {' '.join(args)}: {e}")
            return False

    @classmethod
    def check_bucket_exists(cls, bucket_name: str) -> bool:
        """Checks if the bucket exists using gsutil ls."""
        return cls.run_command(["gsutil", "ls", "-b", f"gs://{bucket_name}"])

    @classmethod
    def create_bucket(cls, bucket_name: str) -> bool:
        """Creates the bucket using gsutil mb."""
        project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("PROJECT_ID") or "sre-next"
        project_id = project_id.strip("'\"")
        print(f"[GCS Sync] Bucket gs://{bucket_name} does not exist. Creating in project {project_id}...")
        return cls.run_command(["gsutil", "mb", "-p", project_id, f"gs://{bucket_name}"])

    @classmethod
    def check_gcs_has_files(cls, bucket_name: str) -> bool:
        """Returns True if GCS folder has any files present."""
        gcs_folder = get_gcs_folder_path()
        try:
            res = subprocess.run(
                ["gsutil", "ls", f"gs://{bucket_name}/{gcs_folder}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15
            )
            # If gsutil output has files, it will return 0 and list items
            return res.returncode == 0 and bool(res.stdout.strip())
        except Exception:
            return False

    @classmethod
    def do_sync_from_gcs(cls) -> bool:
        """Performs rsync from GCS to local directory."""
        if not is_gcs_enabled():
            return False
        
        bucket_name = get_gcs_bucket_name()
        gcs_folder = get_gcs_folder_path()
        set_sync_status("SYNCING")
        
        # Ensure bucket is prepared
        if not cls.check_bucket_exists(bucket_name):
            if not cls.create_bucket(bucket_name):
                set_sync_status("FAILED")
                return False

        # If GCS has no files, we should do initial upload instead of download (to prevent deleting local cache)
        if not cls.check_gcs_has_files(bucket_name):
            print(f"[GCS Sync] GCS folder gs://{bucket_name}/{gcs_folder} is empty. Syncing local to GCS instead...")
            return cls.do_sync_to_gcs()

        print(f"[GCS Sync] Pulling discovery cache from gs://{bucket_name}/{gcs_folder}...")
        local_dir = get_discover_dir()
        os.makedirs(local_dir, exist_ok=True)
        
        success = cls.run_command([
            "gsutil", "rsync", "-r", "-d",
            f"gs://{bucket_name}/{gcs_folder}",
            f"{local_dir}/"
        ])
        
        if success:
            set_sync_status("SUCCESS")
            print("[GCS Sync] Pulled successfully.")
            return True
        else:
            set_sync_status("FAILED")
            return False

    @classmethod
    def do_sync_to_gcs(cls) -> bool:
        """Performs rsync from local directory to GCS."""
        if not is_gcs_enabled():
            return False
        
        bucket_name = get_gcs_bucket_name()
        gcs_folder = get_gcs_folder_path()
        set_sync_status("SYNCING")
        
        # Ensure bucket is prepared
        if not cls.check_bucket_exists(bucket_name):
            if not cls.create_bucket(bucket_name):
                set_sync_status("FAILED")
                return False

        print(f"[GCS Sync] Pushing local discovery cache to gs://{bucket_name}/{gcs_folder}...")
        local_dir = get_discover_dir()
        os.makedirs(local_dir, exist_ok=True)
        
        success = cls.run_command([
            "gsutil", "rsync", "-r", "-d",
            f"{local_dir}/",
            f"gs://{bucket_name}/{gcs_folder}"
        ])
        
        if success:
            set_sync_status("SUCCESS")
            print("[GCS Sync] Pushed successfully.")
            return True
        else:
            set_sync_status("FAILED")
            return False

    @classmethod
    def trigger_sync_background(cls, direction: str = "from"):
        """Triggers GCS sync in a non-blocking background daemon thread."""
        if not is_gcs_enabled():
            return
            
        def run():
            if direction == "from":
                cls.do_sync_from_gcs()
            else:
                cls.do_sync_to_gcs()
                
        t = threading.Thread(target=run, daemon=True)
        t.start()
