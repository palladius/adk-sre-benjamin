import os
from datetime import datetime, timezone
from src.trigger import parse_trigger
from src.scaffolding import scaffold_incident
from src.agents import (
    IncidentCommander,
    CommunicationsLead,
    OperationsLead,
    PlanningLead,
    LogisticsLead
)

from src.incident import get_investigations_dir

def run_incident_flow(payload: dict, base_dir: str = None) -> tuple[str, str]:
    """Orchestrates the top-down IMAG Incident Command System (ICS) delegation workflow."""
    from src.observability import instrument_agents
    instrument_agents()
    
    base_dir = base_dir or get_investigations_dir()
    # 1. Parse Alert Trigger and Scaffold Incident Folders
    trigger = parse_trigger(payload)
    incident = scaffold_incident(trigger, base_dir=base_dir)
    
    # 2. Instantiate all primary functional SRE leads
    commander = IncidentCommander(incident_context=incident.incident_context)
    comms = CommunicationsLead(incident_context=incident.incident_context)
    ops = OperationsLead(incident_context=incident.incident_context)
    planning = PlanningLead(incident_context=incident.incident_context)
    logistics = LogisticsLead(incident_context=incident.incident_context)
    
    timeline_path = os.path.join(incident.folder_path, "timeline.md")
    state_path = os.path.join(incident.folder_path, "state.md")
    
    # helper to append structured timeline events
    def log_to_timeline(event_text: str):
        timestamp = datetime.now(timezone.utc).isoformat()
        with open(timeline_path, "a") as f:
            f.write(f"- **[{timestamp}]** {event_text}\n")
            
    # 3. Step 1: Incident Commander Declares Incident Active
    declaration = commander.declare_incident(
        alert_event=trigger.event_type,
        project_id=trigger.project_id,
        incident_id=incident.incident_id
    )
    log_to_timeline(f"Incident ACTIVE - Incident Commander {commander.agent.name} declared: {declaration.strip()}")
    
    # 4. Step 2: Communications Lead Broadcasts the Incident
    broadcast = comms.broadcast_incident(
        incident_id=incident.incident_id,
        incident_status="ACTIVE",
        project_id=trigger.project_id,
        summary_text=f"SLO Alert {trigger.event_type} is currently active."
    )
    log_to_timeline(f"Incident Broadcasted - {comms.agent.name} dispatched channel alerts: {broadcast.strip()}")
    
    # 5. Step 3: Logistics Verifies Quotas and Credentials
    quota_check = logistics.quota_check(
        project_id=trigger.project_id,
        cred_var_name="GCP_CREDENTIALS",
        cred_status="VERIFIED"
    )
    log_to_timeline(f"Credentials and monitoring quota verified by Logistics: {quota_check.strip()}")
    
    # 6. Step 4: Ops Agent Initiates Triaging
    triage = ops.triage_metric(
        metric_name="frontend_latency",
        value=480.0,
        threshold=100.0
    )
    log_to_timeline(f"Triage diagnostic strategy formulated by Operations: {triage.strip()}")
    
    # 7. Write Scribe initial state document
    with open(state_path, "w") as f:
        f.write(f"""# Active SRE Incident State: {incident.incident_id}

## Metadata
- **Status:** NEW
- **RCA Found:** False
- **Mitigated:** False
- **Fixed:** False
- **Verified:** False
- **Target Project:** `{trigger.project_id}`
- **Trigger Event:** `{trigger.event_type}`
- **Incident Commander:** {commander.agent.name}
- **Safety Level:** LOW Risk
- **Incident UUID:** `{incident.incident_context.incident_uuid}`

## Active Diagnostic Pipeline
- Operations Lead is executing log checks.
""")
        
    return incident.incident_id, incident.folder_path
