import os
import json
import subprocess
import pytest
from src.scribe_git import find_repo_root

def test_full_e2e_simulation_flow(tmp_path):
    # Set up a mock Git repository to prevent polluting the actual repo and test clean Scribe commits
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Benjamin E2E Tester"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.email", "e2e-test@conductor.ai"], cwd=str(tmp_path), capture_output=True)
    
    # Must commit at least one file so git HEAD is valid
    placeholder = tmp_path / "placeholder.txt"
    placeholder.write_text("initial workspace seed")
    subprocess.run(["git", "add", "placeholder.txt"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial repository commit"], cwd=str(tmp_path), capture_output=True)
    
    # Import the E2E simulation functions
    from run_simulation import run_simulation, resume_simulation
    
    # 1. First Phase: Run the initial incident trigger and diagnostics up to the safety pause
    payload = {
        "event_type": "frontend_latency_slo_violated",
        "project_id": "prod-db-999"
    }
    incident_id, incident_folder = run_simulation(base_dir=str(tmp_path), payload=payload)
    
    # Assert incident directory and standard files were created
    assert incident_id.startswith("INC-")
    assert os.path.exists(incident_folder)
    
    state_path = os.path.join(incident_folder, "state.md")
    timeline_path = os.path.join(incident_folder, "timeline.md")
    raw_audit_path = os.path.join(incident_folder, "raw_audit.jsonl")
    registry_path = os.path.join(incident_folder, "artifacts_registry.json")
    
    assert os.path.exists(state_path)
    assert os.path.exists(timeline_path)
    assert os.path.exists(raw_audit_path)
    assert os.path.exists(registry_path)
    
    # Assert status is currently AWAITING_APPROVAL
    with open(state_path, "r") as f:
        initial_state = f.read()
    assert "AWAITING_APPROVAL" in initial_state
    
    # Verify artifacts were generated and registered correctly
    artifacts_dir = os.path.join(incident_folder, "artifacts")
    assert os.path.exists(artifacts_dir)
    
    # Check that query logs and metrics generated files
    files_in_artifacts = os.listdir(artifacts_dir)
    assert len(files_in_artifacts) >= 2
    
    # Verify artifacts_registry.json contents
    with open(registry_path, "r") as f:
        registry = json.load(f)
    
    assert len(registry) >= 2
    
    # Make sure lineage and provenance references are set
    sources = [item["source_type"] for item in registry]
    assert "CLI" in sources or "MCP" in sources
    
    # 2. Second Phase: Resume the simulation with operator manual approval
    resume_simulation(incident_id, approved=True, base_dir=str(tmp_path))
    
    # Read the timeline to ensure it records Benjamin, Madhavi, Logistics, Ops and the mutation
    with open(timeline_path, "r") as f:
        timeline_content = f.read()
        
    commander_name = os.getenv("COMMANDER_NAME") or "Benjamin"
    assert commander_name in timeline_content
    assert "Logistics" in timeline_content
    assert "Operations" in timeline_content or "Ops" in timeline_content
    assert "restart" in timeline_content.lower() or "mutation" in timeline_content.lower()
    assert "closed" in timeline_content.lower() or "resolved" in timeline_content.lower()
    
    # Verify final CLOSED status in state.md
    with open(state_path, "r") as f:
        final_state = f.read()
    assert "CLOSED" in final_state
    
    # Verify Scribe checkpoint commit was created and Git Notes were attached
    repo_root = find_repo_root(incident_folder)
    log_res = subprocess.run(["git", "log", "-1", "--format=%H"], cwd=repo_root, capture_output=True, text=True)
    latest_commit_hash = log_res.stdout.strip()
    
    notes_res = subprocess.run(["git", "notes", "show", latest_commit_hash], cwd=repo_root, capture_output=True, text=True)
    assert notes_res.returncode == 0
    assert "audit" in notes_res.stdout.lower() or "checkpoint" in notes_res.stdout.lower()

def test_rejection_e2e_simulation_flow(tmp_path):
    # Set up a second mock Git repository for rejection testing
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Benjamin E2E Tester"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.email", "e2e-test@conductor.ai"], cwd=str(tmp_path), capture_output=True)
    
    placeholder = tmp_path / "placeholder.txt"
    placeholder.write_text("initial workspace seed")
    subprocess.run(["git", "add", "placeholder.txt"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial commit"], cwd=str(tmp_path), capture_output=True)
    
    from run_simulation import run_simulation, resume_simulation
    incident_id, incident_folder = run_simulation(base_dir=str(tmp_path))
    
    # Resume with operator manual REJECTION
    resume_simulation(incident_id, approved=False, base_dir=str(tmp_path))
    
    state_path = os.path.join(incident_folder, "state.md")
    timeline_path = os.path.join(incident_folder, "timeline.md")
    
    with open(state_path, "r") as f:
        final_state = f.read()
    assert "ABORTED" in final_state
    
    with open(timeline_path, "r") as f:
        timeline_content = f.read()
    assert "rejected" in timeline_content.lower()
    assert "aborted" in timeline_content.lower()
