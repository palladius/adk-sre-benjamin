from dataclasses import dataclass

@dataclass
class Trigger:
    event_type: str
    project_id: str

def parse_trigger(payload: dict) -> Trigger:
    if "event_type" not in payload:
        raise ValueError("Missing event_type")
    
    event_type = payload["event_type"]
    if not event_type:
        raise ValueError("Empty event_type")
        
    project_id = payload.get("project_id", "")
    if not project_id:
        import os
        project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("PROJECT_ID") or "prod-db-999"
    return Trigger(event_type=event_type, project_id=project_id)
