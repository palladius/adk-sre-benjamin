import os
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable

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
    """Local filesystem backend for state management."""

    def __init__(self, state_file_path_resolver: Optional[Callable[[], str]] = None):
        """Initializes FileStateManager with an optional path resolver."""
        self.state_file_path_resolver = state_file_path_resolver

    def get_state_file_path(self) -> str:
        """Resolves the absolute path to the active state JSON file."""
        if self.state_file_path_resolver:
            return self.state_file_path_resolver()
        
        # Check if ACTIVE_STATE_FILE is overridden in src.server to preserve
        # test isolation when tests patch ACTIVE_STATE_FILE.
        try:
            import src.server
            if src.server.ACTIVE_STATE_FILE != "investigations/active_state.json":
                return src.server.ACTIVE_STATE_FILE
        except (ImportError, AttributeError):
            pass

        # Fallback to dynamic resolution
        from src.incident import get_investigations_dir
        return os.path.join(get_investigations_dir(), "active_state.json")

    def get_active_state(self) -> Dict[str, Any]:
        """Loads active state coordinates from the state file, falling back to defaults."""
        default_state = {
            "project_id": os.getenv("PROJECT_ID") or os.getenv("GCP_PROJECT_ID") or "sre-next",
            "incident_id": "None",
            "incident_status": "NEW",
            "substatus_rca": False,
            "substatus_mitigated": False,
            "substatus_fixed": False,
            "substatus_verified": False
        }
        
        try:
            import src.db as db
            if db.is_db_active():
                return db.get_active_state(default_state)
        except Exception as e:
            print(f"[Active State DB] Failed to read active state from DB: {e}")

        active_state_file = self.get_state_file_path()
        if os.path.exists(active_state_file):
            try:
                with open(active_state_file, "r") as f:
                    data = json.load(f)
                    # Ensure all required keys exist
                    for key, val in default_state.items():
                        if key not in data:
                            data[key] = val
                    return data
            except Exception as e:
                print(f"[Active State] Failed to read active state file: {e}")
                
        return default_state

    def save_active_state(self, state: Dict[str, Any]) -> None:
        """Saves updated active state coordinates to the active state json file."""
        try:
            import src.db as db
            if db.is_db_active():
                db.save_active_state(state)
        except Exception as e:
            print(f"[Active State DB] Failed to save active state to DB: {e}")

        active_state_file = self.get_state_file_path()
        dir_name = os.path.dirname(active_state_file)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        try:
            with open(active_state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"[Active State] Failed to write active state file: {e}")

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
    """Returns the globally configured StateManager instance."""
    global _state_manager
    if _state_manager is None:
        backend = os.getenv("STORAGE_BACKEND_STATE", "local").lower()
        if backend == "local":
            _state_manager = FileStateManager()
        else:
            raise ValueError(f"Unknown state storage backend: {backend}")
    return _state_manager

def set_state_manager(manager: BaseStateManager) -> None:
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

def set_discovery_storage(storage: BaseDiscoveryStorage) -> None:
    """Explicitly sets the global DiscoveryStorage instance."""
    global _discovery_storage
    _discovery_storage = storage
