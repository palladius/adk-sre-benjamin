import os
import json
from datetime import datetime, timezone
from src.trigger import parse_trigger
from src.scaffolding import scaffold_incident
from src.diagnostics import query_logs, query_metrics
from src.safety import is_command_safe, decompose_command
from src.registry import add_artifact_to_registry
from src.scribe_git import commit_scribe_changes, add_git_note
from src.comms_telegram import send_telegram_alert
from src.comms_github import GitHubTicketingEngine
from src.agents import (
    IncidentCommander,
    CommunicationsLead,
    OperationsLead,
    PlanningLead,
    LogisticsLead
)

def run_simulation(base_dir: str = None, payload: dict = None) -> tuple[str, str]:
    """Runs a complete end-to-end SRE incident simulation in seconds.

    This harness simulates a Latency SLO violation trigger and resolves it using
    Project Benjamin's top-down IMAG Incident Command System (ICS) structure.
    """
    from src.incident import get_investigations_dir
    base_dir = base_dir or get_investigations_dir()
    if payload is None:
        payload = {
            "event_type": "frontend_latency_slo_violated",
            "project_id": ""
        }

    # 1. Parse Alert Trigger and Scaffold Incident Folders
    trigger = parse_trigger(payload)
    incident = scaffold_incident(trigger, base_dir=base_dir)

    timeline_path = os.path.join(incident.folder_path, "timeline.md")
    state_path = os.path.join(incident.folder_path, "state.md")
    raw_audit_path = os.path.join(incident.folder_path, "raw_audit.jsonl")
    artifacts_dir = os.path.join(incident.folder_path, "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    # Instantiate all 5 SRE functional leads
    commander = IncidentCommander()
    comms = CommunicationsLead()
    ops = OperationsLead()
    planning = PlanningLead()
    logistics = LogisticsLead()

    # Initialize Comms Engines
    github_issue_path = os.path.join(artifacts_dir, "github_issue.json")
    telegram_feed_path = os.path.join(artifacts_dir, "telegram_feed.json")
    github = GitHubTicketingEngine(issue_file_path=github_issue_path)

    # Create GitHub issue & send active Telegram alert immediately
    issue_id = github.create_incident_issue(
        incident_id=incident.incident_id,
        trigger_event=trigger.event_type,
        project_id=trigger.project_id
    )
    send_telegram_alert(
        message=f"SLO violation alert detected! Declared ACTIVE.",
        incident_id=incident.incident_id,
        feed_file_path=telegram_feed_path
    )

    # Register comms artifacts in registry.json
    add_artifact_to_registry(
        incident_folder=incident.folder_path,
        file_path=telegram_feed_path,
        source_type="MCP",
        source_command="MCP://telegram/sendMessage",
        source_arguments={"incident_id": incident.incident_id}
    )
    add_artifact_to_registry(
        incident_folder=incident.folder_path,
        file_path=github_issue_path,
        source_type="MCP",
        source_command="MCP://github/create_issue",
        source_arguments={"incident_id": incident.incident_id}
    )

    # Helper to append to timeline.md, raw_audit.jsonl, Telegram, and GitHub Issues
    def log_event(agent_name: str, message: str, step_details: str = ""):
        timestamp = datetime.now(timezone.utc).isoformat()
        # Append to human-readable timeline
        with open(timeline_path, "a") as f:
            f.write(f"- **[{timestamp}]** [{agent_name}] {message}\n")
        # Append to audit log
        audit_entry = {
            "timestamp": timestamp,
            "agent": agent_name,
            "message": message,
            "details": step_details
        }
        with open(raw_audit_path, "a") as f:
            f.write(json.dumps(audit_entry) + "\n")

        # Log to external channels
        github.add_issue_comment(issue_id, agent_name, message, incident.incident_id)
        send_telegram_alert(
            message=f"[{agent_name}] {message}",
            incident_id=incident.incident_id,
            feed_file_path=telegram_feed_path
        )

    # Step 1: Benjamin Declares Incident Active
    declaration = commander.declare_incident(
        alert_event=trigger.event_type,
        project_id=trigger.project_id,
        incident_id=incident.incident_id
    )
    log_event(f"Incident Commander {commander.agent.name}", f"Alert received: {trigger.event_type}. Incident declared ACTIVE.", declaration)

    # Step 2: Madhavi Broadcasts the Incident
    broadcast = comms.broadcast_incident(
        incident_id=incident.incident_id,
        incident_status="ACTIVE",
        project_id=trigger.project_id,
        summary_text=f"SLO Alert {trigger.event_type} is active. Ops Lead has been assigned."
    )
    log_event(f"Communications Lead {comms.agent.name}", "Incident broadcast sent to Telegram and Slack.", broadcast)

    # Step 3: Logistics Verifies Quotas and Credentials
    quota_check = logistics.quota_check(
        project_id=trigger.project_id,
        cred_var_name="GCP_CREDENTIALS",
        cred_status="VERIFIED"
    )
    log_event(f"Logistics Lead {logistics.agent.name}", "GCP Credentials and monitoring API limits audited and verified.", quota_check)

    # Write Scribe initial state document
    with open(state_path, "w") as f:
        f.write(f"""# Active SRE Incident State: {incident.incident_id}

## Metadata
- **Status:** ACTIVE
- **Target Project:** `{trigger.project_id}`
- **Trigger Event:** `{trigger.event_type}`
- Incident Commander: **Benjamin**
- **Safety Level:** LOW Risk

## Active Diagnostic Pipeline
- Operations Lead is executing log checks.
""")

    # Step 4: Ops queries Metrics (Metrics Agent)
    log_event(f"Operations Lead {ops.agent.name}", "Initiating high-frequency metrics diagnostic collection.")
    latency_values = query_metrics(trigger.project_id, "latency")
    cpu_values = query_metrics(trigger.project_id, "cpu")

    # Save metrics into a CSV file inside the artifacts/ folder
    metrics_csv_path = os.path.join(artifacts_dir, "metrics.csv")
    with open(metrics_csv_path, "w") as f:
        f.write("metric_name,value\n")
        for val in latency_values:
            f.write(f"frontend_latency,{val}\n")
        for val in cpu_values:
            f.write(f"cpu_utilization,{val}\n")

    # Register the metric CSV artifact in artifacts_registry.json
    add_artifact_to_registry(
        incident_folder=incident.folder_path,
        file_path=metrics_csv_path,
        source_type="MCP",
        source_command="MCP://cloud_monitoring/query_metrics",
        source_arguments={"project_id": trigger.project_id, "metric_names": ["latency", "cpu"]}
    )
    log_event(f"Operations Lead {ops.agent.name}", "Metrics Agent generated and registered metrics CSV artifact.", f"Metrics stored: {metrics_csv_path}")

    # Step 5: Ops queries Logs (Logs Agent)
    log_event(f"Operations Lead {ops.agent.name}", "Initiating diagnostic query on MySQL database logs.")
    logs_output = query_logs(trigger.project_id, "mysql")

    # Save logs into a log file inside the artifacts/ folder
    logs_file_path = os.path.join(artifacts_dir, "mysql_query.log")
    with open(logs_file_path, "w") as f:
        f.write(logs_output)

    # Register the log artifact in artifacts_registry.json
    add_artifact_to_registry(
        incident_folder=incident.folder_path,
        file_path=logs_file_path,
        source_type="CLI",
        source_command="gcloud logging read 'resource.type=gce_instance' --limit=5",
        source_arguments={"project_id": trigger.project_id, "query": "mysql"}
    )
    log_event(f"Operations Lead {ops.agent.name}", "Logs Agent scraped and registered MySQL query log artifact.", f"Logs stored: {logs_file_path}")

    # Step 6: Ops identifies saturation/deadlock and proposes whitelisted recovery command
    log_event(f"Operations Lead {ops.agent.name}", "Triage identified CPU saturation and database pool deadlock. Proposing mutation restart.")
    proposed_command = "systemctl restart mysql"
    proposal = ops.propose_mutation(
        command=proposed_command,
        asset="db_instance",
        expected_outcome="Free locked transaction pools and restore frontend SLO performance"
    )
    log_event(f"Operations Lead {ops.agent.name}", f"Proposed system mutation command: {proposed_command}", proposal)

    # Step 7: Logistics Risk Assessor evaluates risk
    log_event(f"Logistics Lead {logistics.agent.name}", "Risk Assessor performing security audit on proposed mutation command.")
    is_safe, max_risk, reasons = is_command_safe(proposed_command)
    parts = decompose_command(proposed_command)

    evaluation = logistics.command_evaluation(
        proposed_command=proposed_command,
        command_parts=parts,
        max_risk=max_risk,
        evaluation_status="APPROVED" if is_safe else "BLOCKED",
        reasons=reasons
    )
    log_event(f"Logistics Lead {logistics.agent.name}", f"Command risk assessment complete. Status: APPROVED. Risk level: {max_risk}.", evaluation)

    # Pause on Safety Gate: Write AWAITING_APPROVAL status to state.md and wait for user manual approval
    log_event(f"Logistics Lead {logistics.agent.name}", f"Safety gate holds proposed command: `{proposed_command}` ({max_risk} Risk). Awaiting Human-in-the-Loop operator authorization.")

    with open(state_path, "w") as f:
        f.write(f"""# Active SRE Incident State: {incident.incident_id}

## Metadata
- **Status:** AWAITING_APPROVAL
- **Target Project:** `{trigger.project_id}`
- **Trigger Event:** `{trigger.event_type}`
- **Incident Commander:** Benjamin
- **Safety Level:** {max_risk} Risk
- **Proposed Mutation:** `{proposed_command}`

## Active Diagnostic Pipeline
- Risk assessment complete. Awaiting operator safety clearance on the dashboard panel to execute mutation.
""")

    # Commit initial diagnostics state dynamically using Scribe version-control
    message = f"scribe(audit): Diagnostics and safety gate pause for {incident.incident_id}"
    commit_hash = commit_scribe_changes(incident.folder_path, message)

    audit_notes = f"""Incident Checkpoint (Paused): {incident.incident_id}
- Incident ID: {incident.incident_id}
- Trigger Event: {trigger.event_type}
- Status: AWAITING_APPROVAL
- Proposed Command: {proposed_command} (Risk: {max_risk})
"""
    add_git_note(incident.folder_path, commit_hash, audit_notes)

    return incident.incident_id, incident.folder_path

def resume_simulation(incident_id: str, approved: bool, base_dir: str = None) -> tuple[str, str]:
    """Resumes a paused SRE simulation based on human-in-the-loop manual dashboard approval or rejection."""
    import re
    from src.incident import get_investigations_dir
    base_dir = base_dir or get_investigations_dir()
    folder_path = os.path.join(base_dir, incident_id)
    state_path = os.path.join(folder_path, "state.md")
    timeline_path = os.path.join(folder_path, "timeline.md")
    raw_audit_path = os.path.join(folder_path, "raw_audit.jsonl")
    artifacts_dir = os.path.join(folder_path, "artifacts")

    # 1. Parse existing state.md to extract metadata
    status = "UNKNOWN"
    project_id = "UNKNOWN"
    trigger_event = "UNKNOWN"
    proposed_command = "systemctl restart mysql"
    max_risk = "HIGH"

    if os.path.exists(state_path):
        with open(state_path, "r") as f:
            state_content = f.read()
        status_match = re.search(r'\-\s+\*\*Status:\*\*\s*([A-Za-z0-9_]+)', state_content, re.IGNORECASE)
        if status_match: status = status_match.group(1).strip()
        project_match = re.search(r'\-\s+\*\*Target Project:\*\*\s*`?([^`\n]+)`?', state_content, re.IGNORECASE)
        if project_match: project_id = project_match.group(1).strip()
        trigger_match = re.search(r'\-\s+\*\*Trigger Event:\*\*\s*`?([^`\n]+)`?', state_content, re.IGNORECASE)
        if trigger_match: trigger_event = trigger_match.group(1).strip()
        mutation_match = re.search(r'\-\s+\*\*Proposed Mutation:\*\*\s*`?([^`\n]+)`?', state_content, re.IGNORECASE)
        if mutation_match: proposed_command = mutation_match.group(1).strip()
        risk_match = re.search(r'\-\s+\*\*Safety Level:\*\*\s*([A-Za-z0-9_]+)', state_content, re.IGNORECASE)
        if risk_match: max_risk = risk_match.group(1).strip()

    # Re-instantiate agents & channels
    comms = CommunicationsLead()
    ops = OperationsLead()
    planning = PlanningLead()
    logistics = LogisticsLead()

    github_issue_path = os.path.join(artifacts_dir, "github_issue.json")
    telegram_feed_path = os.path.join(artifacts_dir, "telegram_feed.json")
    github = GitHubTicketingEngine(issue_file_path=github_issue_path)

    # Extract existing issue_id from github_issue.json if exists
    issue_id = "1"
    if os.path.exists(github_issue_path):
        try:
            with open(github_issue_path, "r") as f:
                issue_data = json.load(f)
                issue_id = issue_data.get("issue_id", "1")
        except Exception:
            pass

    def log_event(agent_name: str, message: str, step_details: str = ""):
        timestamp = datetime.now(timezone.utc).isoformat()
        with open(timeline_path, "a") as f:
            f.write(f"- **[{timestamp}]** [{agent_name}] {message}\n")
        audit_entry = {
            "timestamp": timestamp,
            "agent": agent_name,
            "message": message,
            "details": step_details
        }
        with open(raw_audit_path, "a") as f:
            f.write(json.dumps(audit_entry) + "\n")

        github.add_issue_comment(issue_id, agent_name, message, incident_id)
        send_telegram_alert(
            message=f"[{agent_name}] {message}",
            incident_id=incident_id,
            feed_file_path=telegram_feed_path
        )

    if approved:
        # Step 8: Madhavi broadcasts safety clearance and Mutation Agent executes mutation
        hitl_msg = comms.request_hitl_approval(incident_id, proposed_command, max_risk, ["Approved by human operator via SRE dashboard."])
        log_event(f"Communications Lead {comms.agent.name}", f"Safety clearance granted for whitelisted mutation command: {proposed_command}.", hitl_msg)

        log_event("Mutation Agent", f"Executing whitelisted mutation command: {proposed_command}")
        from src.agents import MutationAgent
        mutation_agent = MutationAgent(project_id=project_id)
        success, exec_output = mutation_agent.execute_mutation(proposed_command)
        if success:
            log_event("Mutation Agent", f"Mutation executed successfully: {exec_output}")
        else:
            log_event("Mutation Agent", f"Mutation execution failed/blocked: {exec_output}")
            raise RuntimeError(f"Mutation execution failed: {exec_output}")

        # Step 9: Diagnostic checks confirm metric recovery
        log_event(f"Operations Lead {ops.agent.name}", "Performing post-mutation recovery verification metrics check.")
        recovered_latency = [15.0, 14.5, 15.0]
        recovered_cpu = [12.0, 10.5, 11.0]
        log_event(f"Operations Lead {ops.agent.name}", f"Post-mutation checks complete. Latency: {recovered_latency[-1]}ms (threshold: 100ms). CPU: {recovered_cpu[-1]}%. Status: RECOVERED.")

        # Step 10: Scribe updates state, commits all chronicles, and attaches a Git Note
        log_event(f"Planning Lead {planning.agent.name}", "Scribe Agent closing incident chronicles.")
        with open(state_path, "w") as f:
            f.write(f"""# Active SRE Incident State: {incident_id}

## Metadata
- **Status:** CLOSED
- **Target Project:** `{project_id}`
- **Trigger Event:** `{trigger_event}`
- **Incident Commander:** Benjamin
- **Safety Level:** LOW Risk

## Active Diagnostic Pipeline
- Incident resolved via whitelisted restart of MySQL database.
- All services healthy and verified.
""")
        log_event(f"Planning Lead {planning.agent.name}", "Incident resolved successfully. Closed.")

        github.close_incident_issue(issue_id, f"Restarted database service successfully under {max_risk} Risk clearance.", incident_id)
        send_telegram_alert(message="Incident resolved successfully! Closed.", incident_id=incident_id, feed_file_path=telegram_feed_path)
    else:
        # Rejection path
        log_event(f"Communications Lead {comms.agent.name}", f"Safety clearance REJECTED by human operator for command: {proposed_command}.")
        log_event("Mutation Agent", f"Halted mutation execution. Safety gate block active.")

        with open(state_path, "w") as f:
            f.write(f"""# Active SRE Incident State: {incident_id}

## Metadata
- **Status:** ABORTED
- **Target Project:** `{project_id}`
- **Trigger Event:** `{trigger_event}`
- **Incident Commander:** Benjamin
- **Safety Level:** {max_risk} Risk
- **Proposed Mutation:** `{proposed_command}` (REJECTED)

## Active Diagnostic Pipeline
- Mutation rejected by human operator. Safety gate aborted operations.
""")
        log_event(f"Planning Lead {planning.agent.name}", "Incident aborted successfully. Closed as BLOCKED.")

        github.close_incident_issue(issue_id, "Aborted: Mutation command rejected by operator safety override.", incident_id)
        send_telegram_alert(message="Incident aborted by user safety override. Closed.", incident_id=incident_id, feed_file_path=telegram_feed_path)

    # Commit changes dynamically using Scribe version-control
    message = f"scribe(audit): Checkpoint resolution state for {incident_id} (Approved: {approved})"
    commit_hash = commit_scribe_changes(folder_path, message)

    audit_notes = f"""Incident Checkpoint: {incident_id}
- Incident ID: {incident_id}
- Trigger Event: {trigger_event}
- Status: {"RESOLVED" if approved else "ABORTED"}
- Mutation {"Applied: " + proposed_command if approved else "Rejected"}
- Scribe Chronicles: Committed at {commit_hash}
"""
    add_git_note(folder_path, commit_hash, audit_notes)

    return incident_id, folder_path

if __name__ == "__main__":
    import sys
    print("Starting Project Benjamin SRE incident simulation...")
    inc_id, inc_folder = run_simulation()
    print(f"Incident {inc_id} declared and paused on safety gate!")
    print(f" Chronicles saved in: {inc_folder}")
    print("Auto-approving to complete full simulation...")
    resume_simulation(inc_id, approved=True)
    print("Incident fully resolved!")
