import os
from dataclasses import dataclass
from datetime import datetime, timezone
import secrets
from src.trigger import Trigger

@dataclass
class Incident:
    incident_id: str
    folder_path: str
    trigger: Trigger

def scaffold_incident(trigger: Trigger, base_dir: str = "investigations") -> Incident:
    # Incident ID generation using UTC time to match SRE standards
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    rand_hex = secrets.token_hex(2)
    incident_id = f"INC-{date_str}-{rand_hex}"
    
    folder_path = os.path.join(base_dir, incident_id)
    os.makedirs(folder_path, exist_ok=True)
    
    # Initialize investigation files
    raw_audit_path = os.path.join(folder_path, "raw_audit.jsonl")
    state_path = os.path.join(folder_path, "state.md")
    timeline_path = os.path.join(folder_path, "timeline.md")
    
    # Touch files to ensure they are created
    for file_path in [raw_audit_path, state_path, timeline_path]:
        with open(file_path, "a") as f:
            pass
            
    return Incident(incident_id=incident_id, folder_path=folder_path, trigger=trigger)
