import os
import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

@dataclass
class ArtifactMetadata:
    file_path: str
    size_bytes: int
    created_at: str
    source_type: str
    source_command: str
    source_arguments: dict
    checksum: str

def calculate_sha256(filepath: str) -> str:
    """Calculates the SHA-256 checksum of a file in chunks to handle huge logs safely."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def _load_registry(incident_folder: str) -> list[dict]:
    registry_path = os.path.join(incident_folder, "artifacts_registry.json")
    if not os.path.exists(registry_path):
        return []
        
    try:
        with open(registry_path, "r") as f:
            return json.load(f)
    except Exception:
        return []

def _save_registry(incident_folder: str, registry_data: list[dict]):
    registry_path = os.path.join(incident_folder, "artifacts_registry.json")
    with open(registry_path, "w") as f:
        json.dump(registry_data, f, indent=2)

def add_artifact_to_registry(
    incident_folder: str,
    file_path: str,
    source_type: str,
    source_command: str,
    source_arguments: dict
) -> ArtifactMetadata:
    """Registers a downloaded or generated large file into the incident's artifacts index."""
    size_bytes = os.path.getsize(file_path)
    checksum = calculate_sha256(file_path)
    created_at = datetime.now(timezone.utc).isoformat()
    
    # Store standard relative path for cross-environment portability
    rel_path = os.path.relpath(file_path, incident_folder)
    
    artifact = ArtifactMetadata(
        file_path=rel_path,
        size_bytes=size_bytes,
        created_at=created_at,
        source_type=source_type,
        source_command=source_command,
        source_arguments=source_arguments,
        checksum=checksum
    )
    
    registry = _load_registry(incident_folder)
    
    # Append or overwrite duplicate paths to prevent stale logs index
    updated_registry = [item for item in registry if item.get("file_path") != rel_path]
    updated_registry.append(asdict(artifact))
    
    _save_registry(incident_folder, updated_registry)
    return artifact

def get_cached_artifact(
    incident_folder: str,
    source_command: str,
    source_arguments: dict
) -> ArtifactMetadata | None:
    """Retrieves a previously downloaded artifact if matching source signatures are found."""
    registry = _load_registry(incident_folder)
    
    for item in registry:
        if (
            item.get("source_command") == source_command and
            item.get("source_arguments") == source_arguments
        ):
            # Verify the cached file actually still exists physically on disk
            full_path = os.path.join(incident_folder, item["file_path"])
            if os.path.exists(full_path):
                return ArtifactMetadata(**item)
                
    return None
