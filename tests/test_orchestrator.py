import os
import pytest
from src.orchestrator import run_incident_flow

def test_orchestrator_incident_flow(tmp_path):
    # Setup mock event payload
    payload = {
        "event_type": "frontend_latency_slo_violated",
        "project_id": "prod-db-999"
    }
    
    # Run the top-down incident delegation workflow
    incident_id, folder_path = run_incident_flow(payload, base_dir=str(tmp_path))
    
    assert incident_id.startswith("INC-")
    assert os.path.exists(folder_path)
    
    # Verify folder structure is initialized
    state_file = os.path.join(folder_path, "state.md")
    timeline_file = os.path.join(folder_path, "timeline.md")
    audit_file = os.path.join(folder_path, "raw_audit.jsonl")
    
    assert os.path.exists(state_file)
    assert os.path.exists(timeline_file)
    assert os.path.exists(audit_file)
    
    # Check that Scribe successfully logged all top-down dispatches
    with open(timeline_file, "r") as f:
        timeline_content = f.read()
        
    assert "Incident ACTIVE" in timeline_content
    assert "Incident Broadcasted" in timeline_content
    assert "Credentials and monitoring quota verified" in timeline_content
    assert "Triage diagnostic strategy formulated" in timeline_content
