import os
import json
import tempfile
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable


def _default_active_state() -> Dict[str, Any]:
    return {
        "project_id": os.getenv("PROJECT_ID") or os.getenv("GCP_PROJECT_ID") or "sre-next",
        "incident_id": "None",
        "incident_status": "NEW",
        "substatus_rca": False,
        "substatus_mitigated": False,
        "substatus_fixed": False,
        "substatus_verified": False,
    }


class BaseStateManager(ABC):
    """Abstract base class for state management."""

    @abstractmethod
    def get_active_state(self) -> Dict[str, Any]:
        """Loads active state coordinates, falling back to defaults if not present."""
        pass

    @abstractmethod
    def save_active_state(self, state: Dict[str, Any]) -> None:
        """Saves updated active state coordinates."""
        pass


class FileStateManager(BaseStateManager):
    """Pure local filesystem backend for state management with atomic writes."""

    def __init__(self, state_file_path_resolver: Optional[Callable[[], str]] = None):
        """Initializes FileStateManager with an optional path resolver."""
        self.state_file_path_resolver = state_file_path_resolver

    def get_state_file_path(self) -> str:
        """Resolves the path to the active state JSON file."""
        if self.state_file_path_resolver:
            return self.state_file_path_resolver()

        try:
            import src.server
            return src.server.get_active_state_file()
        except (ImportError, AttributeError):
            pass

        from src.incident import get_investigations_dir
        return os.path.join(get_investigations_dir(), "active_state.json")

    def get_active_state(self) -> Dict[str, Any]:
        """Loads active state coordinates strictly from the local state file, falling back to defaults."""
        default_state = _default_active_state()
        active_state_file = self.get_state_file_path()
        if os.path.exists(active_state_file):
            try:
                with open(active_state_file, "r") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    for key, val in default_state.items():
                        if key not in data:
                            data[key] = val
                    return data
            except Exception as e:
                print(f"[Active State] Failed to read active state file: {e}")

        return default_state

    def save_active_state(self, state: Dict[str, Any]) -> None:
        """Atomically writes updated active state coordinates to the active state JSON file."""
        active_state_file = self.get_state_file_path()
        dir_name = os.path.dirname(os.path.abspath(active_state_file))
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        try:
            fd, tmp_path = tempfile.mkstemp(prefix=".active_state_", suffix=".tmp", dir=dir_name or ".")
            try:
                with os.fdopen(fd, "w") as f:
                    json.dump(state, f, indent=2)
                    f.flush()
                os.replace(tmp_path, active_state_file)
            except Exception:
                if os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
                raise
        except Exception as e:
            print(f"[Active State] Failed to write active state file: {e}")


class DatabaseStateManager(BaseStateManager):
    """Database backend (Cloud SQL PostgreSQL) for state management with local filesystem fallback."""

    def __init__(self, fallback_manager: Optional[BaseStateManager] = None):
        self.fallback_manager = fallback_manager or FileStateManager()

    def get_active_state(self) -> Dict[str, Any]:
        default_state = _default_active_state()
        try:
            import src.db as db
            if db.is_db_active():
                res = db.get_active_state(None, raise_on_error=True)
                if res is not None:
                    for key, val in default_state.items():
                        if key not in res:
                            res[key] = val
                    return res
                # Row not yet in DB (first boot): check fallback file before returning defaults
                return self.fallback_manager.get_active_state()
        except Exception as e:
            print(f"[DatabaseStateManager] Failed to read active state from DB, falling back to file: {e}")
        return self.fallback_manager.get_active_state()

    def save_active_state(self, state: Dict[str, Any]) -> None:
        # Mirror to local file first (pure filesystem, no second DB write)
        self.fallback_manager.save_active_state(state)
        import src.db as db
        if db.is_db_active():
            try:
                ok = db.save_active_state(state)
            except Exception as e:
                print(f"[DatabaseStateManager] Failed to save active state to DB: {e}")
                raise RuntimeError(f"Failed to persist active state to database (persisted locally only): {e}") from e
            if not ok:
                raise RuntimeError("Failed to persist active state to database (persisted locally only)")


class BaseDiscoveryStorage(ABC):
    """Abstract base class for discovery storage."""

    @abstractmethod
    def save_discovery(self, project_id: str, resources: List[Dict[str, Any]], markdown_content: str) -> None:
        """Saves discovery JSON and Markdown data for the project."""
        pass

    @abstractmethod
    def load_discovery_json(self, project_id: str) -> List[Dict[str, Any]]:
        """Loads discovery resources list for the project."""
        pass

    @abstractmethod
    def load_discovery_markdown(self, project_id: str) -> str:
        """Loads discovery markdown/wiki content for the project."""
        pass


class FileDiscoveryStorage(BaseDiscoveryStorage):
    """Local filesystem backend for discovery storage."""

    def __init__(self, discover_dir_resolver: Optional[Callable[[], str]] = None):
        """Initializes FileDiscoveryStorage with an optional directory resolver."""
        self.discover_dir_resolver = discover_dir_resolver

    def get_discover_dir(self) -> str:
        """Resolves the base discovery directory."""
        if self.discover_dir_resolver:
            return self.discover_dir_resolver()

        from src.incident import get_discover_dir
        return get_discover_dir()

    def get_project_dir(self, project_id: str) -> str:
        """Gets the project discovery directory path."""
        return os.path.join(self.get_discover_dir(), "gcp-project", project_id)

    def save_discovery(self, project_id: str, resources: List[Dict[str, Any]], markdown_content: str) -> None:
        """Saves discovery JSON and Markdown data locally."""
        project_dir = self.get_project_dir(project_id)
        os.makedirs(project_dir, exist_ok=True)

        json_path = os.path.join(project_dir, "discover.json")
        with open(json_path, "w") as f:
            json.dump(resources, f, indent=2)

        md_path = os.path.join(project_dir, "wiki.md")
        with open(md_path, "w") as f:
            f.write(markdown_content)

    def load_discovery_json(self, project_id: str) -> List[Dict[str, Any]]:
        """Loads discovery resources list locally."""
        project_dir = self.get_project_dir(project_id)
        json_path = os.path.join(project_dir, "discover.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Discovery Storage] Failed to load discovery JSON for {project_id}: {e}")
        return []

    def load_discovery_markdown(self, project_id: str) -> str:
        """Loads discovery markdown/wiki content locally."""
        project_dir = self.get_project_dir(project_id)
        md_path = os.path.join(project_dir, "wiki.md")
        if os.path.exists(md_path):
            try:
                with open(md_path, "r") as f:
                    return f.read()
            except Exception as e:
                print(f"[Discovery Storage] Failed to load discovery markdown for {project_id}: {e}")
        return ""


# Pluggable Storage Registry
_state_manager: Optional[BaseStateManager] = None
_discovery_storage: Optional[BaseDiscoveryStorage] = None


def get_state_manager() -> BaseStateManager:
    """Returns the configured StateManager instance.
    If an explicit manager was pinned via set_state_manager(), returns it; otherwise
    dynamically resolves DatabaseStateManager vs FileStateManager from current env and DB state.
    """
    global _state_manager
    if _state_manager is not None:
        return _state_manager

    raw_backend = os.getenv("STORAGE_BACKEND_STATE")
    if raw_backend is not None:
        backend = raw_backend.strip().lower()
        if backend in ("local", "file", "filesystem"):
            return FileStateManager()
        elif backend in ("db", "database", "postgres", "postgresql", "cloud", "auto"):
            return DatabaseStateManager()
        else:
            raise ValueError(f"Unknown state storage backend: {backend}")

    # Default ("auto"): use DatabaseStateManager when DB is active or running in production, otherwise FileStateManager
    import src.db as db
    from src.incident import resolve_benjamin_env
    is_prod = resolve_benjamin_env() == "production"

    if db.is_db_active() or is_prod:
        return DatabaseStateManager()
    return FileStateManager()


def set_state_manager(manager: Optional[BaseStateManager]) -> None:
    """Explicitly sets the global StateManager instance."""
    global _state_manager
    _state_manager = manager


def get_discovery_storage() -> BaseDiscoveryStorage:
    """Returns the globally configured DiscoveryStorage instance."""
    global _discovery_storage
    if _discovery_storage is None:
        backend = os.getenv("STORAGE_BACKEND_DISCOVERY", "local").lower()
        if backend == "local":
            _discovery_storage = FileDiscoveryStorage()
        else:
            raise ValueError(f"Unknown discovery storage backend: {backend}")
    return _discovery_storage


def set_discovery_storage(storage: Optional[BaseDiscoveryStorage]) -> None:
    """Explicitly sets the global DiscoveryStorage instance."""
    global _discovery_storage
    _discovery_storage = storage
