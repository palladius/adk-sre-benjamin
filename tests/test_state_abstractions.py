import os
import json
import pytest
from unittest.mock import patch
from src.storage import (
    FileStateManager,
    FileDiscoveryStorage,
    get_state_manager,
    get_discovery_storage,
    set_state_manager,
    set_discovery_storage
)

def test_file_state_manager(tmp_path, monkeypatch):
    monkeypatch.delenv("PROJECT_ID", raising=False)
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    state_file = tmp_path / "active_state.json"
    
    # 1. Initialize state manager with resolver
    manager = FileStateManager(state_file_path_resolver=lambda: str(state_file))
    
    # 2. Test default state loading
    with patch.dict(os.environ, {}, clear=True):
        state = manager.get_active_state()
        assert state["project_id"] == "sre-next"
    assert state["incident_id"] == "None"
    assert state["incident_status"] == "NEW"
    
    # 3. Test state updating and saving
    state["project_id"] = "test-project-123"
    state["incident_id"] = "INC-20260616-test"
    state["incident_status"] = "ONGOING"
    state["substatus_rca"] = True
    
    manager.save_active_state(state)
    
    # 4. Verify state persistence
    assert state_file.exists()
    
    # Reload and check
    manager_new = FileStateManager(state_file_path_resolver=lambda: str(state_file))
    reloaded_state = manager_new.get_active_state()
    assert reloaded_state["project_id"] == "test-project-123"
    assert reloaded_state["incident_id"] == "INC-20260616-test"
    assert reloaded_state["incident_status"] == "ONGOING"
    assert reloaded_state["substatus_rca"] is True

def test_file_discovery_storage(tmp_path):
    discover_dir = tmp_path / "discover"
    
    # 1. Initialize discovery storage with resolver
    storage = FileDiscoveryStorage(discover_dir_resolver=lambda: str(discover_dir))
    
    project_id = "test-project-abc"
    resources = [
        {"name": "vm-1", "type": "gce_vm", "vulnerable": False, "warning": None}
    ]
    markdown = "# Discovery Audit: test-project-abc\nEverything is secure."
    
    # 2. Save discovery data
    storage.save_discovery(project_id, resources, markdown)
    
    # 3. Verify files were written
    project_dir = discover_dir / "gcp-project" / project_id
    assert (project_dir / "discover.json").exists()
    assert (project_dir / "wiki.md").exists()
    
    # 4. Load discovery data back
    loaded_resources = storage.load_discovery_json(project_id)
    assert len(loaded_resources) == 1
    assert loaded_resources[0]["name"] == "vm-1"
    
    loaded_markdown = storage.load_discovery_markdown(project_id)
    assert "Everything is secure" in loaded_markdown

def test_storage_registry():
    # Test that registry sets and gets managers correctly
    mock_state_manager = object()
    mock_discovery_storage = object()
    
    original_state = get_state_manager()
    original_discovery = get_discovery_storage()
    
    try:
        set_state_manager(mock_state_manager)
        set_discovery_storage(mock_discovery_storage)
        
        assert get_state_manager() is mock_state_manager
        assert get_discovery_storage() is mock_discovery_storage
    finally:
        set_state_manager(original_state)
        set_discovery_storage(original_discovery)
