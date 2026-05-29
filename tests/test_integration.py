import os
import subprocess
import pytest
from src.trigger import Trigger
from src.scaffolding import scaffold_incident
from src.orchestrator import run_incident_flow
from src.scribe_git import commit_scribe_changes

def test_git_versioning_and_timeline_updates(tmp_path):
    # Enable a mock git repository in tmp_path to test automated scribe commits
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Conductor Test"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@conductor.ai"], cwd=str(tmp_path), capture_output=True)
    
    # We must create an initial commit so that there is a HEAD reference
    initial_file = tmp_path / "init.txt"
    initial_file.write_text("initial repo state")
    subprocess.run(["git", "add", "init.txt"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial commit"], cwd=str(tmp_path), capture_output=True)
    
    payload = {
        "event_type": "frontend_latency_slo_violated",
        "project_id": "prod-db-999"
    }
    
    # Run orchestration flow in this git-enabled tmp_path folder
    incident_id, folder_path = run_incident_flow(payload, base_dir=str(tmp_path))
    
    # Commit changes dynamically using our new scribe_git module!
    message = f"scribe(audit): Checkpoint initial state for {incident_id}"
    commit_hash = commit_scribe_changes(folder_path, message)
    
    assert len(commit_hash) == 40
    
    # Verify commit log contains our checkpoint
    log_res = subprocess.run(["git", "log", "-1", "--format=%s"], cwd=str(tmp_path), capture_output=True, text=True)
    assert message in log_res.stdout
