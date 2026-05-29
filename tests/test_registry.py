import os
import json
import pytest
from src.registry import add_artifact_to_registry, get_cached_artifact, ArtifactMetadata

def test_add_and_get_cached_artifact(tmp_path):
    # Set up mock incident folder
    incident_folder = tmp_path / "INC-12345"
    incident_folder.mkdir()
    
    # Create a mock large file to catalog
    artifacts_dir = incident_folder / "artifacts"
    artifacts_dir.mkdir()
    mock_log = artifacts_dir / "large_logs.txt"
    mock_log.write_text("ERROR: Connection timed out after 30 seconds.")
    
    # 1. Add artifact
    rel_path = "artifacts/large_logs.txt"
    source_command = "MCP://cloud_logging/get_logs"
    source_arguments = {"project_id": "prod-db-999", "limit": 100}
    
    artifact = add_artifact_to_registry(
        incident_folder=str(incident_folder),
        file_path=str(mock_log),
        source_type="MCP",
        source_command=source_command,
        source_arguments=source_arguments
    )
    
    assert artifact.file_path == rel_path
    assert artifact.size_bytes == len("ERROR: Connection timed out after 30 seconds.")
    assert artifact.source_type == "MCP"
    assert artifact.source_command == source_command
    assert artifact.source_arguments == source_arguments
    assert len(artifact.checksum) == 64 # SHA-256 length
    
    # Verify file registry actually exists
    registry_path = incident_folder / "artifacts_registry.json"
    assert registry_path.exists()
    
    # 2. Query cache
    cached = get_cached_artifact(
        incident_folder=str(incident_folder),
        source_command=source_command,
        source_arguments=source_arguments
    )
    
    assert cached is not None
    assert cached.file_path == rel_path
    assert cached.checksum == artifact.checksum

def test_get_cached_artifact_missing(tmp_path):
    incident_folder = tmp_path / "INC-empty"
    incident_folder.mkdir()
    
    # Query nonexistent cache
    cached = get_cached_artifact(
        incident_folder=str(incident_folder),
        source_command="gcloud logging read",
        source_arguments={}
    )
    assert cached is None
