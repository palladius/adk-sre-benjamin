import os
import shutil
import pytest
from src.trigger import parse_trigger, Trigger
from src.scaffolding import scaffold_incident, Incident

def test_parse_trigger_valid():
    payload = {
        "event_type": "frontend_latency_slo_violated",
        "project_id": "prod-db-999"
    }
    trigger = parse_trigger(payload)
    assert trigger.event_type == "frontend_latency_slo_violated"
    assert trigger.project_id == "prod-db-999"

def test_parse_trigger_invalid():
    with pytest.raises(ValueError, match="Missing event_type"):
        parse_trigger({"project_id": "prod-db-999"})

    with pytest.raises(ValueError, match="Empty event_type"):
        parse_trigger({"event_type": ""})

def test_parse_trigger_fallback(monkeypatch):
    monkeypatch.setenv("GCP_PROJECT_ID", "env-gcp-project-test")
    
    payload = {
        "event_type": "frontend_latency_slo_violated",
        "project_id": ""
    }
    trigger = parse_trigger(payload)
    assert trigger.project_id == "env-gcp-project-test"
    
    # Empty payload project_id but PROJECT_ID set
    monkeypatch.delenv("GCP_PROJECT_ID")
    monkeypatch.setenv("PROJECT_ID", "env-project-456")
    trigger = parse_trigger(payload)
    assert trigger.project_id == "env-project-456"

def test_scaffold_incident(tmp_path):
    # Set up mock trigger
    trigger = Trigger(event_type="frontend_latency_slo_violated", project_id="prod-db-999")
    
    # Use tmp_path to avoid creating actual folders in test workspace
    incident = scaffold_incident(trigger, base_dir=str(tmp_path))
    
    assert incident.incident_id.startswith("INC-")
    assert len(incident.incident_id) > 12 # INC-YYYYMMDD-HEX
    
    assert os.path.exists(incident.folder_path)
    assert os.path.isdir(incident.folder_path)
    
    # Verify files created inside the folder
    raw_audit_path = os.path.join(incident.folder_path, "raw_audit.jsonl")
    state_path = os.path.join(incident.folder_path, "state.md")
    timeline_path = os.path.join(incident.folder_path, "timeline.md")
    
    assert os.path.exists(raw_audit_path)
    assert os.path.exists(state_path)
    assert os.path.exists(timeline_path)
