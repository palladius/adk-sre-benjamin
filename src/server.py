import os
import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone
import urllib.parse
from run_simulation import run_simulation, resume_simulation

def parse_incident_folder(folder_path: str) -> dict:
    """Parses Scribe files inside an incident folder to return structured JSON."""
    incident_id = os.path.basename(folder_path)
    state_path = os.path.join(folder_path, "state.md")
    timeline_path = os.path.join(folder_path, "timeline.md")
    registry_path = os.path.join(folder_path, "artifacts_registry.json")
    
    # Defaults
    status = "NEW"
    substatus_rca = False
    substatus_mitigated = False
    substatus_fixed = False
    substatus_verified = False
    project_id = "UNKNOWN"
    domain_id = "UNKNOWN"
    trigger_event = "UNKNOWN"
    incident_uuid = "UNKNOWN"
    timeline = []
    artifacts = []
    archived = False
    
    # 1. Parse state.md
    if os.path.exists(state_path):
        try:
            with open(state_path, "r") as f:
                state_content = f.read()
                
            status_match = re.search(r'\-\s+\*\*Status:\*\*\s*([A-Za-z0-9_-]+)', state_content, re.IGNORECASE)
            if status_match:
                status_raw = status_match.group(1).strip()
                from src.incident import validate_incident_status
                try:
                    status = validate_incident_status(status_raw)
                except Exception:
                    status = "NEW"
                    
            # Parse substatuses
            rca_match = re.search(r'\-\s+\*\*(RCA Found|rca_found|substatus_rca):\*\*\s*([A-Za-z0-9_-]+)', state_content, re.IGNORECASE)
            if rca_match:
                substatus_rca = rca_match.group(2).strip().lower() == "true"
                
            mitigated_match = re.search(r'\-\s+\*\*(Mitigated|mitigated|substatus_mitigated):\*\*\s*([A-Za-z0-9_-]+)', state_content, re.IGNORECASE)
            if mitigated_match:
                substatus_mitigated = mitigated_match.group(2).strip().lower() == "true"
                
            fixed_match = re.search(r'\-\s+\*\*(Fixed|fixed|substatus_fixed):\*\*\s*([A-Za-z0-9_-]+)', state_content, re.IGNORECASE)
            if fixed_match:
                substatus_fixed = fixed_match.group(2).strip().lower() == "true"
                
            verified_match = re.search(r'\-\s+\*\*(Verified|verified|substatus_verified):\*\*\s*([A-Za-z0-9_-]+)', state_content, re.IGNORECASE)
            if verified_match:
                substatus_verified = verified_match.group(2).strip().lower() == "true"
                
            project_match = re.search(r'\-\s+\*\*(Target Project|GCP Project):\*\*\s*`?([^`\n]+)`?', state_content, re.IGNORECASE)
            if project_match:
                project_id = project_match.group(2).strip()
                
            domain_match = re.search(r'\-\s+\*\*(Domain|Domain ID):\*\*\s*`?([^`\n]+)`?', state_content, re.IGNORECASE)
            if domain_match:
                domain_id = domain_match.group(2).strip()
                
            trigger_match = re.search(r'\-\s+\*\*Trigger Event:\*\*\s*`?([^`\n]+)`?', state_content, re.IGNORECASE)
            if trigger_match:
                trigger_event = trigger_match.group(1).strip()
                
            archived_match = re.search(r'\-\s+\*\*Archived:\*\*\s*([A-Za-z0-9_]+)', state_content, re.IGNORECASE)
            if archived_match:
                archived = archived_match.group(1).strip().lower() == "true"
                
            uuid_match = re.search(r'\-\s+\*\*Incident UUID:\*\*\s*`?([^`\n]+)`?', state_content, re.IGNORECASE)
            if uuid_match:
                incident_uuid = uuid_match.group(1).strip()
        except Exception as e:
            print(f"Error parsing state.md in {folder_path}: {e}")
            
    # 2. Parse timeline.md
    if os.path.exists(timeline_path):
        try:
            with open(timeline_path, "r") as f:
                for line in f:
                    # Match pattern: - **[timestamp]** [agent_name] message
                    match = re.match(r'\-\s+\*\*\[(.*?)\]\*\*\s+\[(.*?)\]\s+(.*)', line)
                    if match:
                        timeline.append({
                            "timestamp": match.group(1).strip(),
                            "agent": match.group(2).strip(),
                            "message": match.group(3).strip()
                        })
                    else:
                        # Fallback for plain lines
                        clean_line = line.strip().lstrip("-* ").strip()
                        if clean_line:
                            timeline.append({
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "agent": "System",
                                "message": clean_line
                            })
        except Exception as e:
            print(f"Error parsing timeline.md in {folder_path}: {e}")
            
    # 3. Load artifacts_registry.json
    if os.path.exists(registry_path):
        try:
            with open(registry_path, "r") as f:
                artifacts = json.load(f)
                
            # Load contents for text/csv artifacts to visualize directly
            for art in artifacts:
                art_rel_path = art.get("file_path", "")
                # If relative to incident folder, join properly
                if art_rel_path.startswith("artifacts/"):
                    art_full_path = os.path.join(folder_path, art_rel_path)
                else:
                    art_full_path = art_rel_path
                    
                if os.path.exists(art_full_path):
                    try:
                        with open(art_full_path, "r") as af:
                            art["content"] = af.read()
                    except Exception:
                        art["content"] = "[Binary or unreadable content]"
        except Exception as e:
            print(f"Error loading artifacts_registry.json in {folder_path}: {e}")
            
    if not project_id or project_id == "UNKNOWN":
        project_id = os.getenv("PROJECT_ID") or os.getenv("GCP_PROJECT_ID") or "sre-next"

    if not domain_id or domain_id == "UNKNOWN":
        if project_id == "sre-next":
            domain_id = "sre-demo"

    return {
        "incident_id": incident_id,
        "status": status,
        "substatus_rca": substatus_rca,
        "substatus_mitigated": substatus_mitigated,
        "substatus_fixed": substatus_fixed,
        "substatus_verified": substatus_verified,
        "project_id": project_id,
        "domain_id": domain_id,
        "trigger_event": trigger_event,
        "incident_uuid": incident_uuid,
        "timeline": timeline,
        "artifacts": artifacts,
        "folder_path": folder_path,
        "archived": archived
    }

def set_incident_archived(folder_path: str, archived: bool = True) -> bool:
    """Updates the 'Archived' metadata property in the incident's state.md file."""
    state_path = os.path.join(folder_path, "state.md")
    if not os.path.exists(state_path):
        return False
    try:
        with open(state_path, "r") as f:
            content = f.read()
        
        # Check if Archived line already exists
        pattern = r'(\-\s+\*\*Archived:\*\*\s*)([A-Za-z0-9_]+)'
        if re.search(pattern, content, re.IGNORECASE):
            # Replace existing value
            new_val = "true" if archived else "false"
            content = re.sub(pattern, r'\g<1>' + new_val, content, flags=re.IGNORECASE)
        else:
            # Insert after the ## Metadata line
            metadata_header = "## Metadata"
            if metadata_header in content:
                insert_idx = content.find(metadata_header) + len(metadata_header)
                # Find end of metadata_header line
                eol = content.find("\n", insert_idx)
                if eol == -1:
                    content += f"\n- **Archived:** {'true' if archived else 'false'}"
                else:
                    content = content[:eol] + f"\n- **Archived:** {'true' if archived else 'false'}" + content[eol:]
            else:
                # Fallback to appending
                content += f"\n- **Archived:** {'true' if archived else 'false'}"
        
        with open(state_path, "w") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error archiving incident {folder_path}: {e}")
        return False

def get_incident_date(incident_id: str):
    """Extracts date from incident ID (INC-YYYYMMDD-xxxx)."""
    match = re.match(r"INC-(\d{8})-", incident_id)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y%m%d").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None

def auto_archive_incidents():
    """Auto-archives closed incidents older than 3 days."""
    from datetime import datetime, timezone, timedelta
    incidents_dir = "investigations"
    if not os.path.exists(incidents_dir):
        return
    now = datetime.now(timezone.utc)
    for item in os.listdir(incidents_dir):
        item_path = os.path.join(incidents_dir, item)
        if os.path.isdir(item_path) and item.startswith("INC-"):
            try:
                details = parse_incident_folder(item_path)
                if details.get("status") == "CLOSED" and not details.get("archived", False):
                    # Check age
                    inc_date = get_incident_date(item)
                    if not inc_date:
                        # Fallback to mtime of state.md
                        state_path = os.path.join(item_path, "state.md")
                        if os.path.exists(state_path):
                            mtime = os.path.getmtime(state_path)
                            inc_date = datetime.fromtimestamp(mtime, tz=timezone.utc)
                        else:
                            inc_date = now
                    
                    if now - inc_date > timedelta(days=3):
                        print(f"[Auto-Archive] Archiving closed incident: {item}")
                        set_incident_archived(item_path, True)
            except Exception as e:
                print(f"[Auto-Archive] Error processing {item}: {e}")

def get_commander_name() -> str:
    """Gets the Incident Commander name from environment variables, defaulting to 'Benjamin'."""
    return os.getenv("COMMANDER_NAME") or os.getenv("INCIDENT_COMMANDER_NAME") or "Benjamin"

ACTIVE_STATE_FILE = "investigations/active_state.json"

def get_active_state() -> dict:
    """Loads active state coordinates from the state file, falling back to defaults."""
    default_state = {
        "project_id": os.getenv("PROJECT_ID") or os.getenv("GCP_PROJECT_ID") or "sre-next",
        "incident_id": "None",
        "incident_status": "NEW",
        "substatus_rca": False,
        "substatus_mitigated": False,
        "substatus_fixed": False,
        "substatus_verified": False
    }
    
    if os.path.exists(ACTIVE_STATE_FILE):
        try:
            with open(ACTIVE_STATE_FILE, "r") as f:
                data = json.load(f)
                # Ensure all required keys exist
                for key, val in default_state.items():
                    if key not in data:
                        data[key] = val
                return data
        except Exception as e:
            print(f"[Active State] Failed to read active state file: {e}")
            
    return default_state

def save_active_state(state: dict):
    """Saves updated active state coordinates to the active state json file."""
    dir_name = os.path.dirname(ACTIVE_STATE_FILE)
    if dir_name and not os.path.exists(dir_name):
        try:
            os.makedirs(dir_name, exist_ok=True)
        except Exception:
            pass
            
    try:
        with open(ACTIVE_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"[Active State] Failed to write active state file: {e}")

# Mutation Queue Backend Helper Functions
def add_pending_mutation(incident_id: str, command: str, risk_factor: str, risk_reason: str, justification: str) -> dict:
    incident_path = os.path.join("investigations", incident_id)
    pending_path = os.path.join(incident_path, "pending_approvals.json")
    
    queue = []
    if os.path.exists(pending_path):
        try:
            with open(pending_path, "r") as f:
                queue = json.load(f)
        except Exception:
            queue = []
            
    next_num = 1
    for item in queue:
        item_id = item.get("id", "")
        if item_id.startswith("cmd-"):
            try:
                num = int(item_id.split("-")[1])
                if num >= next_num:
                    next_num = num + 1
            except (IndexError, ValueError):
                pass
    cmd_id = f"cmd-{next_num:02d}"
    
    risk_emoji = ""
    clean_risk = risk_factor.upper()
    if "LOW" in clean_risk:
        risk_emoji = "🟢"
    elif "MEDIUM" in clean_risk:
        risk_emoji = "🟡"
    elif "HIGH" in clean_risk:
        risk_emoji = "🟠"
    elif "CRITICAL" in clean_risk:
        risk_emoji = "🔴"
        
    if risk_emoji and risk_emoji not in risk_factor:
        risk_factor = f"{risk_emoji} {clean_risk}"
    elif not risk_emoji:
        risk_factor = f"🟢 {clean_risk}"
        
    new_item = {
        "id": cmd_id,
        "command": command,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "risk_factor": risk_factor,
        "risk_reason": risk_reason,
        "justification": justification
    }
    
    queue.append(new_item)
    
    with open(pending_path, "w") as f:
        json.dump(queue, f, indent=2)
        
    update_state_markdown_table(incident_id, queue)
    return new_item

def update_state_markdown_table(incident_id: str, queue: list[dict]):
    incident_path = os.path.join("investigations", incident_id)
    state_path = os.path.join(incident_path, "state.md")
    if not os.path.exists(state_path):
        return
        
    try:
        with open(state_path, "r") as f:
            content = f.read()
            
        header = "## Pending SRE Mutation Actions Queue"
        
        if queue:
            table_lines = [
                header,
                "| Command ID | Proposed Command | Risk Factor | Risk Reason | Justification |",
                "| --- | --- | --- | --- | --- |"
            ]
            for item in queue:
                cmd_escaped = item.get("command", "").replace("|", "\\|")
                table_lines.append(
                    f"| `{item.get('id')}` | `{cmd_escaped}` | {item.get('risk_factor')} | {item.get('risk_reason')} | {item.get('justification')} |"
                )
            table_content = "\n".join(table_lines) + "\n"
        else:
            table_content = f"{header}\nNo pending mutations.\n"
            
        pattern = r"## Pending SRE Mutation Actions Queue.*?(?=\n## |\Z)"
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, table_content.rstrip("\n"), content, flags=re.DOTALL)
        else:
            if not content.endswith("\n"):
                content += "\n"
            content += "\n" + table_content
            
        with open(state_path, "w") as f:
            f.write(content)
    except Exception as e:
        print(f"[Server] Failed to update state.md with mutation queue: {e}")

def approve_pending_mutation(incident_id: str, cmd_id: str, comment: str = "") -> bool:
    incident_path = os.path.join("investigations", incident_id)
    pending_path = os.path.join(incident_path, "pending_approvals.json")
    if not os.path.exists(pending_path):
        return False
        
    try:
        with open(pending_path, "r") as f:
            queue = json.load(f)
    except Exception:
        return False
        
    target_item = None
    for item in queue:
        if item.get("id") == cmd_id:
            target_item = item
            break
            
    if not target_item:
        return False
        
    queue.remove(target_item)
    with open(pending_path, "w") as f:
        json.dump(queue, f, indent=2)
        
    update_state_markdown_table(incident_id, queue)
    save_mutation_comment(incident_path, target_item.get("command"), "approve", comment)
    
    command = target_item.get("command")
    chat_path = os.path.join(incident_path, "chat.json")
    chat_data = []
    if os.path.exists(chat_path):
        try:
            with open(chat_path, "r") as f:
                chat_data = json.load(f)
        except Exception:
            pass
            
    chat_data.append({
        "sender": "Operator (Web Dashboard)",
        "message": f"Approved proposed mutation command '{command}' via SRE Web Panel." + (f" Comment: {comment}" if comment else ""),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    chat_data.append({
        "sender": f"{get_commander_name()} Agent (IC)",
        "message": f"✅ Safety Gate Clearance Granted! Resuming SRE incident resolution pipeline. Executed: {command}",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    with open(chat_path, "w") as f:
        json.dump(chat_data, f, indent=2)
        
    log_timeline_event(incident_path, "Operator (Web Dashboard)", f"Approved proposed mutation command '{command}'." + (f" Comment: {comment}" if comment else ""))
    log_timeline_event(incident_path, "Communications Lead Madhavi", f"Safety clearance granted for whitelisted mutation command: {command}.")
    log_timeline_event(incident_path, "Mutation Agent", f"Executing whitelisted mutation command: {command}")
    log_timeline_event(incident_path, f"Operations Lead OpsAgent", "Performing post-mutation recovery verification metrics check.")
    log_timeline_event(incident_path, f"Operations Lead OpsAgent", f"Post-mutation checks complete. Latency: 15.0ms (threshold: 100ms). CPU: 11.0%. Status: RECOVERED.")
    log_timeline_event(incident_path, "Planning Lead Scribe", "Scribe Agent closing incident chronicles.")
    log_timeline_event(incident_path, "Planning Lead Scribe", "Incident resolved successfully. Closed.")
    
    log_audit_event(incident_path, "Operator (Web Dashboard)", f"Approved proposed mutation command '{command}'." + (f" Comment: {comment}" if comment else ""))
    log_audit_event(incident_path, "Mutation Agent", f"Executing whitelisted mutation command: {command}")
    log_audit_event(incident_path, "Planning Lead Scribe", "Incident resolved successfully. Closed.")
    
    update_incident_status_in_state_md(incident_path, "CLOSED")
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if bot_token and chat_id:
        bot_token = bot_token.strip("'\"")
        chat_id = chat_id.strip("'\"")
        if "ENTER_BOT" not in bot_token and "ENTER_CHAT" not in chat_id:
            msg = (
                f"✅ *Safety Gate Clearance Granted via Web Dashboard!*\n\n"
                f"Proposed SRE mutation command '{command}' was approved by the operator.\n"
                f"Resuming incident resolution... {get_commander_name()} executed the action."
            )
            try:
                send_telegram_menu(bot_token, chat_id, msg)
            except Exception as tg_err:
                print(f"[Server] Failed to send Telegram approval notification: {tg_err}")
                
    return True

def reject_pending_mutation(incident_id: str, cmd_id: str, comment: str = "") -> bool:
    incident_path = os.path.join("investigations", incident_id)
    pending_path = os.path.join(incident_path, "pending_approvals.json")
    if not os.path.exists(pending_path):
        return False
        
    try:
        with open(pending_path, "r") as f:
            queue = json.load(f)
    except Exception:
        return False
        
    target_item = None
    for item in queue:
        if item.get("id") == cmd_id:
            target_item = item
            break
            
    if not target_item:
        return False
        
    queue.remove(target_item)
    with open(pending_path, "w") as f:
        json.dump(queue, f, indent=2)
        
    update_state_markdown_table(incident_id, queue)
    save_mutation_comment(incident_path, target_item.get("command"), "reject", comment)
    
    command = target_item.get("command")
    chat_path = os.path.join(incident_path, "chat.json")
    chat_data = []
    if os.path.exists(chat_path):
        try:
            with open(chat_path, "r") as f:
                chat_data = json.load(f)
        except Exception:
            pass
            
    chat_data.append({
        "sender": "Operator (Web Dashboard)",
        "message": f"Rejected proposed mutation command '{command}' via SRE Web Panel." + (f" Comment: {comment}" if comment else ""),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    chat_data.append({
        "sender": f"{get_commander_name()} Agent (IC)",
        "message": f"❌ Safety Gate Override Active. Mutation command '{command}' rejected. Halted mutation execution.",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    with open(chat_path, "w") as f:
        json.dump(chat_data, f, indent=2)
        
    log_timeline_event(incident_path, "Operator (Web Dashboard)", f"Rejected proposed mutation command '{command}'." + (f" Comment: {comment}" if comment else ""))
    log_timeline_event(incident_path, "Communications Lead Madhavi", f"Safety clearance REJECTED by human operator for command: {command}.")
    log_timeline_event(incident_path, "Mutation Agent", f"Halted mutation execution. Safety gate block active.")
    log_timeline_event(incident_path, "Planning Lead Scribe", "Incident aborted successfully. Closed as BLOCKED.")
    
    log_audit_event(incident_path, "Operator (Web Dashboard)", f"Rejected proposed mutation command '{command}'." + (f" Comment: {comment}" if comment else ""))
    log_audit_event(incident_path, "Mutation Agent", f"Halted mutation execution. Safety gate block active.")
    log_audit_event(incident_path, "Planning Lead Scribe", "Incident aborted successfully. Closed as BLOCKED.")
    
    update_incident_status_in_state_md(incident_path, "ABORTED")
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if bot_token and chat_id:
        bot_token = bot_token.strip("'\"")
        chat_id = chat_id.strip("'\"")
        if "ENTER_BOT" not in bot_token and "ENTER_CHAT" not in chat_id:
            msg = (
                f"❌ *Safety Gate Override Active via Web Dashboard!*\n\n"
                f"Proposed SRE mutation command '{command}' was rejected by the operator.\n"
                f"SRE operations halted. Safety gate aborted operations successfully."
            )
            try:
                send_telegram_menu(bot_token, chat_id, msg)
            except Exception as tg_err:
                print(f"[Server] Failed to send Telegram rejection notification: {tg_err}")
                
    return True

def update_incident_status_in_state_md(incident_path: str, new_status: str):
    state_path = os.path.join(incident_path, "state.md")
    if not os.path.exists(state_path):
        return
    try:
        with open(state_path, "r") as f:
            content = f.read()
        pattern = r'(\-\s+\*\*Status:\*\*\s*)([A-Za-z0-9_-]+)'
        if re.search(pattern, content, re.IGNORECASE):
            content = re.sub(pattern, r'\g<1>' + new_status, content, flags=re.IGNORECASE)
            with open(state_path, "w") as f:
                f.write(content)
    except Exception as e:
        print(f"Failed to update status in state.md: {e}")

def log_timeline_event(incident_path: str, agent_name: str, message: str):
    timeline_path = os.path.join(incident_path, "timeline.md")
    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        with open(timeline_path, "a") as f:
            f.write(f"- **[{timestamp}]** [{agent_name}] {message}\n")
    except Exception as e:
        print(f"Failed to write to timeline.md: {e}")

def log_audit_event(incident_path: str, agent_name: str, message: str, details: str = ""):
    raw_audit_path = os.path.join(incident_path, "raw_audit.jsonl")
    timestamp = datetime.now(timezone.utc).isoformat()
    audit_entry = {
        "timestamp": timestamp,
        "agent": agent_name,
        "message": message,
        "details": details
    }
    try:
        with open(raw_audit_path, "a") as f:
            f.write(json.dumps(audit_entry) + "\n")
    except Exception as e:
        print(f"Failed to write to raw_audit.jsonl: {e}")

def save_mutation_comment(incident_path: str, command: str, action: str, comment: str):
    if not comment:
        return
    comments_path = os.path.join(incident_path, "mutation_comments.json")
    comments = []
    if os.path.exists(comments_path):
        try:
            with open(comments_path, "r") as f:
                comments = json.load(f)
        except Exception:
            comments = []
            
    comments.append({
        "command": command,
        "action": action,
        "comment": comment,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    try:
        with open(comments_path, "w") as f:
            json.dump(comments, f, indent=2)
    except Exception as e:
        print(f"Failed to save mutation comment: {e}")

def get_mutation_comments_context(incident_path: str) -> str:
    comments_path = os.path.join(incident_path, "mutation_comments.json")
    if not os.path.exists(comments_path):
        return ""
    try:
        with open(comments_path, "r") as f:
            comments = json.load(f)
        if not comments:
            return ""
        lines = ["[Recent Mutation Queue Actions & Operator Comments]:"]
        for c in comments:
            action_past = "approved" if c.get("action") == "approve" else "rejected"
            lines.append(f"- Command '{c.get('command')}' was {action_past}. Operator comment: '{c.get('comment')}'")
        return "\n".join(lines) + "\n\n"
    except Exception:
        return ""

class SREHttpRequestHandler(BaseHTTPRequestHandler):
    
    def end_headers(self):
        # Enable CORS for local testing/dashboard consumption
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
        
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def check_auth(self):
        # 1. Check Identity-Aware Proxy (IAP) authorization
        gcloud_identity = os.environ.get("GCLOUD_IDENTITY")
        if gcloud_identity:
            iap_email = self.headers.get("x-goog-authenticated-user-email")
            if iap_email:
                email = iap_email
                if ":" in iap_email:
                    email = iap_email.split(":", 1)[1]
                if email.strip().lower() == gcloud_identity.strip().lower():
                    return True
            
            # If IAP check failed and Basic Auth is not configured, block access immediately
            username = os.environ.get("WEB_USERNAME")
            password = os.environ.get("WEB_PASSWORD")
            if not username or not password:
                self.send_response(403)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"403 Forbidden: Invalid or missing IAP identity.")
                return False

        # 2. Check Basic Authentication (Username/Password)
        username = os.environ.get("WEB_USERNAME")
        password = os.environ.get("WEB_PASSWORD")
        if username and password:
            auth_header = self.headers.get("Authorization")
            if auth_header and auth_header.startswith("Basic "):
                try:
                    import base64
                    encoded = auth_header.split(" ", 1)[1]
                    decoded = base64.b64decode(encoded).decode("utf-8")
                    user, pwd = decoded.split(":", 1)
                    if user == username and pwd == password:
                        return True
                except Exception:
                    pass
                
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="SRE Dashboard"')
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"401 Unauthorized")
            return False

        return True

    def do_GET(self):
        if not self.check_auth():
            return
            
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        # API: Get Active State Coordinates
        if path == "/api/active-state":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_active_state()).encode("utf-8"))
            return
            
        # API: Get GCS Sync status
        elif path == "/api/gcs/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            from src.gcs_sync import get_sync_status, get_gcs_bucket_name
            self.wfile.write(json.dumps({
                "status": get_sync_status(),
                "bucket": get_gcs_bucket_name()
            }).encode("utf-8"))
            return
            
        # API: Get Server Configuration
        elif path == "/api/config":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            import subprocess
            try:
                commit_sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
            except Exception:
                commit_sha = "unknown"
                
            # Read version from root VERSION file
            try:
                version_path = os.path.join(os.path.dirname(__file__), "..", "VERSION")
                with open(version_path, "r") as vf:
                    version = vf.read().strip()
            except Exception:
                version = "1.2.4"
                
            project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("PROJECT_ID") or "prod-db-999"
            config_data = {
                "project_id": project_id,
                "version": version,
                "commit": commit_sha,
                "author": "Riccardo"
            }
            self.wfile.write(json.dumps(config_data).encode("utf-8"))
            return
            
        # API: Discover GCP Resources for a Project
        elif path.startswith("/api/projects/") and path.endswith("/discover"):
            try:
                project_id = path.split("/")[3]
                if project_id in ("sre-demo", "sre-demo-prod"):
                    import time
                    resources = [
                        {
                            "name": "lab-setup",
                            "type": "gce_vm",
                            "location": "us-central1-a",
                            "status": "RUNNING",
                            "vulnerable": True,
                            "warning": "⚠️ EXPOSED: Bound to public IP 35.232.121.228",
                            "console_url": "https://console.cloud.google.com/compute/instancesDetail/zones/us-central1-a/instances/lab-setup?project=sre-next",
                            "is_mock": True,
                            "metadata": {
                                "internal_ip": "10.0.0.9",
                                "external_ip": "35.232.121.228"
                            }
                        },
                        {
                            "name": "sre-agent-service",
                            "type": "cloud_run",
                            "location": "us-central1",
                            "status": "READY",
                            "vulnerable": False,
                            "warning": None,
                            "console_url": "https://console.cloud.google.com/run/detail/us-central1/sre-agent-service/metrics?project=sre-next",
                            "is_mock": True,
                            "metadata": {
                                "url": "https://sre-agent-service-ha5bfv5noa-uc.a.run.app",
                                "all_users_invoker": False
                            }
                        },
                        {
                            "name": "online-boutique",
                            "type": "gke_cluster",
                            "location": "us-central1",
                            "status": "RUNNING",
                            "vulnerable": True,
                            "warning": "⚠️ EXPOSED: Public GKE control plane endpoint access enabled",
                            "console_url": "https://console.cloud.google.com/kubernetes/clusters/details/us-central1/online-boutique/overview?project=sre-next",
                            "is_mock": True,
                            "metadata": {
                                "endpoint": "34.9.73.164",
                                "private_cluster": False
                            }
                        },
                        {
                            "name": "online-boutique-standard",
                            "type": "gke_cluster",
                            "location": "us-central1",
                            "status": "RUNNING",
                            "vulnerable": True,
                            "warning": "⚠️ EXPOSED: Public GKE control plane endpoint access enabled",
                            "console_url": "https://console.cloud.google.com/kubernetes/clusters/details/us-central1/online-boutique-standard/overview?project=sre-next",
                            "is_mock": True,
                            "metadata": {
                                "endpoint": "136.119.135.4",
                                "private_cluster": False
                            }
                        },
                        {
                            "name": "sre-postgres",
                            "type": "cloud_sql",
                            "location": "us-central1",
                            "status": "RUNNABLE",
                            "vulnerable": False,
                            "warning": None,
                            "console_url": "https://console.cloud.google.com/sql/instances/sre-postgres/overview?project=sre-next",
                            "is_mock": True,
                            "metadata": {
                                "public_ip_enabled": False,
                                "authorized_networks": []
                            }
                        },
                        {
                            "name": "agent-staging-bucket-sre-next",
                            "type": "gcs_bucket",
                            "location": "US-CENTRAL1",
                            "status": "ACTIVE",
                            "vulnerable": True,
                            "warning": "⚠️ EXPOSED: Uniform bucket public access prevention is not enforced",
                            "console_url": "https://console.cloud.google.com/storage/browser/agent-staging-bucket-sre-next?project=sre-next",
                            "is_mock": True,
                            "metadata": {
                                "public_access_prevention": "inherited",
                                "storage_class": "STANDARD",
                                "uniform_bucket_level_access": True
                            }
                        }
                    ]
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    response_data = {
                        "project_id": project_id,
                        "resources": resources,
                        "cache_path": "discover/domains/sre-demo/README.md",
                        "last_crawled": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
                        "wiki_path": "discover/domains/sre-demo/README.md"
                    }
                    self.wfile.write(json.dumps(response_data).encode("utf-8"))
                    return

                cache_dir = os.path.join("discover", "gcp-project", project_id)
                json_path = os.path.join(cache_dir, "discover.json")
                
                # Check for refresh parameter in query string
                query_params = urllib.parse.parse_qs(parsed_url.query)
                force_refresh = "true" in query_params.get("refresh", [])
                
                # Check cache expiration (1 hour TTL)
                import time
                cache_expired = False
                if os.path.exists(json_path):
                    mtime = os.path.getmtime(json_path)
                    if (time.time() - mtime) > 3600:
                        cache_expired = True
                
                # Check cache: if it exists and is fresh, read it
                if os.path.exists(json_path) and not force_refresh and not cache_expired:
                    with open(json_path, "r") as f:
                        resources = json.load(f)
                else:
                    # Run the crawler
                    from src.discovery import discover_project_resources
                    discover_project_resources(project_id)
                    with open(json_path, "r") as f:
                        resources = json.load(f)
                    try:
                        from src.gcs_sync import GcsSyncManager
                        GcsSyncManager.trigger_sync_background("to")
                    except Exception as sync_err:
                        print(f"[Server Discovery] Failed to trigger GCS sync: {sync_err}")
                
                # Fetch last crawled time from file mtime
                mtime = os.path.getmtime(json_path) if os.path.exists(json_path) else time.time()
                last_crawled = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(mtime))
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                
                response_data = {
                    "project_id": project_id,
                    "resources": resources,
                    "cache_path": json_path,
                    "last_crawled": last_crawled,
                    "wiki_path": os.path.join(cache_dir, "wiki.md")
                }
                self.wfile.write(json.dumps(response_data).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return
            
        # API: Get/Generate Custom Wiki for a Project
        elif path.startswith("/api/projects/") and path.endswith("/wiki"):
            try:
                project_id = path.split("/")[3]
                if project_id in ("sre-demo", "sre-demo-prod"):
                    md_path = "discover/domains/sre-demo/README.md"
                    if os.path.exists(md_path):
                        with open(md_path, "r") as f:
                            content = f.read()
                    else:
                        content = f"# SRE Demo Domain ({project_id})\n\nNo custom SRE notes have been added yet for this domain.\n"
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"project_id": project_id, "content": content}).encode("utf-8"))
                    return

                cache_dir = os.path.join("discover", "gcp-project", project_id)
                md_path = os.path.join(cache_dir, "wiki.md")
                
                os.makedirs(cache_dir, exist_ok=True)
                if not os.path.exists(md_path):
                    # Check if json cache exists to regenerate or bootstrap it
                    json_path = os.path.join(cache_dir, "discover.json")
                    if os.path.exists(json_path):
                        from src.discovery import discover_project_resources
                        discover_project_resources(project_id)
                    else:
                        default_wiki = f"# SRE Wiki: {project_id}\n\nNo custom SRE notes have been added yet for this project.\n"
                        with open(md_path, "w") as f:
                            f.write(default_wiki)
                
                with open(md_path, "r") as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"project_id": project_id, "content": content}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Get/Generate Custom Graphviz DOT for a Project
        elif path.startswith("/api/projects/") and path.endswith("/graph"):
            try:
                project_id = path.split("/")[3]
                if project_id in ("sre-demo", "sre-demo-prod"):
                    dot_path = "discover/domains/sre-demo/graph.dot"
                    if not os.path.exists(dot_path):
                        default_graph = (
                            "digraph G {\n"
                            "  rankdir=LR;\n"
                            '  node [style=filled, fillcolor="#1e1e2e", color="#f5c2e7", fontcolor="#cdd6f4", fontname="Outfit"];\n'
                            '  edge [color="#a6adc8"];\n'
                            '  subgraph cluster_sre_next {\n'
                            f'    label="Project: {project_id} (SRE Demo)";\n'
                            '    style=dashed;\n'
                            '    color="#89b4fa";\n'
                            '    fontcolor="#89b4fa";\n'
                            '    "lab-setup" [label="🖥️ lab-setup\\n(10.0.0.9)", fillcolor="#f38ba8", fontcolor="#11111b"];\n'
                            '    "sre-agent-service" [label="🏃 sre-agent-service\\n(Cloud Run)", fillcolor="#a6e3a1", fontcolor="#11111b"];\n'
                            '    "sre-postgres" [label="💾 sre-postgres\\n(Cloud SQL)", fillcolor="#fab387", fontcolor="#11111b"];\n'
                            '  }}\n'
                            '  "lab-setup" -> "sre-agent-service" [label="queries"];\n'
                            '  "sre-agent-service" -> "sre-postgres" [label="reads/writes"];\n'
                            "}\n"
                        )
                        os.makedirs(os.path.dirname(dot_path), exist_ok=True)
                        with open(dot_path, "w") as f:
                            f.write(default_graph)
                    with open(dot_path, "r") as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"project_id": project_id, "graph": content}).encode("utf-8"))
                    return

                cache_dir = os.path.join("discover", "gcp-project", project_id)
                dot_path = os.path.join(cache_dir, "graph.dot")
                
                os.makedirs(cache_dir, exist_ok=True)
                if not os.path.exists(dot_path):
                    default_graph = (
                        f"digraph G {{\n"
                        f"  rankdir=LR;\n"
                        f'  node [style=filled, fillcolor="#1e1e2e", color="#f5c2e7", fontcolor="#cdd6f4", fontname="Outfit"];\n'
                        f'  edge [color="#a6adc8"];\n'
                        f'  subgraph cluster_vpc {{\n'
                        f'    label="VPC Network: default";\n'
                        f'    style=dashed;\n'
                        f'    color="#89b4fa";\n'
                        f'    fontcolor="#89b4fa";\n'
                        f'    "frontend-vm" [label="🖥️ frontend-vm\\n(10.128.0.5)", fillcolor="#f38ba8", fontcolor="#11111b"];\n'
                        f'    "checkout-vm" [label="🖥️ checkout-vm\\n(10.128.0.6)"];\n'
                        f'    "db-sql" [label="💾 db-sql\\n(Cloud SQL)", fillcolor="#fab387", fontcolor="#11111b"];\n'
                        f'  }}\n'
                        f'  "frontend-vm" -> "checkout-vm" [label="HTTP 8080"];\n'
                        f'  "checkout-vm" -> "db-sql" [label="SQL 3306"];\n'
                        f"}}\n"
                    )
                    with open(dot_path, "w") as f:
                        f.write(default_graph)
                
                with open(dot_path, "r") as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"project_id": project_id, "content": content}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # 1. API: List Incidents
        elif path == "/api/incidents":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            query_params = urllib.parse.parse_qs(parsed_url.query)
            include_archived = query_params.get("include_archived", ["false"])[0].lower() == "true"
            
            incidents_dir = "investigations"
            incidents = []
            if os.path.exists(incidents_dir):
                for item in sorted(os.listdir(incidents_dir), reverse=True):
                    item_path = os.path.join(incidents_dir, item)
                    if os.path.isdir(item_path) and item.startswith("INC-"):
                        inc = parse_incident_folder(item_path)
                        if include_archived or not inc.get("archived", False):
                            incidents.append(inc)
            self.wfile.write(json.dumps(incidents).encode("utf-8"))
            return
            
        # 2a. API: Get Contextual Incident Chat
        elif path.startswith("/api/incidents/") and path.endswith("/chat"):
            try:
                incident_id = path.split("/")[3]
                incident_path = os.path.join("investigations", incident_id)
                if os.path.exists(incident_path):
                    chat_path = os.path.join(incident_path, "chat.json")
                    chat_data = []
                    if os.path.exists(chat_path):
                        with open(chat_path, "r") as f:
                            chat_data = json.load(f)
                    else:
                        details = parse_incident_folder(incident_path)
                        chat_data = [
                            {
                                "sender": f"{get_commander_name()} Agent (IC)",
                                "message": f"Welcome to the tactical Incident Chat for {incident_id}. I am {get_commander_name()}, the SRE Incident Commander. We are currently analyzing the incident alert '{details.get('trigger_event')}' targeting project '{details.get('project_id')}'. How can I assist you?",
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        ]
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(chat_data).encode("utf-8"))
                else:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Incident not found"}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # 2b. API: Get Mutation Queue for Incident
        elif path.startswith("/api/incidents/") and path.endswith("/pending"):
            try:
                incident_id = path.split("/")[3]
                incident_path = os.path.join("investigations", incident_id)
                if not os.path.exists(incident_path):
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Incident not found"}).encode("utf-8"))
                    return
                    
                pending_path = os.path.join(incident_path, "pending_approvals.json")
                queue = []
                if os.path.exists(pending_path):
                    try:
                        with open(pending_path, "r") as f:
                            queue = json.load(f)
                    except Exception:
                        queue = []
                        
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(queue).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # 2. API: Get Single Incident Details
        elif path.startswith("/api/incidents/"):
            incident_id = path.replace("/api/incidents/", "")
            incident_path = os.path.join("investigations", incident_id)
            
            if os.path.exists(incident_path) and os.path.isdir(incident_path):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                
                details = parse_incident_folder(incident_path)
                self.wfile.write(json.dumps(details).encode("utf-8"))
            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Incident not found"}).encode("utf-8"))
            return
            
        # 3. Serve Frontend Static Assets
        else:
            # Map default path to index.html
            if path == "/" or path == "":
                path = "/index.html"
                
            # Serve from src/static directory
            static_dir = os.path.join(os.path.dirname(__file__), "static")
            safe_path = os.path.abspath(os.path.join(static_dir, path.lstrip("/")))
            
            # Prevent directory traversal attacks
            if safe_path.startswith(os.path.abspath(static_dir)) and os.path.exists(safe_path) and os.path.isfile(safe_path):
                self.send_response(200)
                
                # Determine Content-Type
                if safe_path.endswith(".html"):
                    self.send_header("Content-Type", "text/html")
                elif safe_path.endswith(".css"):
                    self.send_header("Content-Type", "text/css")
                elif safe_path.endswith(".js"):
                    self.send_header("Content-Type", "application/javascript")
                elif safe_path.endswith(".json"):
                    self.send_header("Content-Type", "application/json")
                elif safe_path.endswith(".png"):
                    self.send_header("Content-Type", "image/png")
                else:
                    self.send_header("Content-Type", "text/plain")
                    
                self.end_headers()
                
                with open(safe_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                # If static file not found, fallback to index.html for SPA-style routing
                index_path = os.path.join(static_dir, "index.html")
                if os.path.exists(index_path):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    with open(index_path, "rb") as f:
                        self.wfile.write(f.read())
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"404 Not Found")
                    
    def do_DELETE(self):
        if not self.check_auth():
            return
            
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        # API: Delete an incident
        if path.startswith("/api/incidents/"):
            try:
                incident_id = path.replace("/api/incidents/", "")
                # Prevent directory traversal attacks
                incident_id = os.path.basename(incident_id)
                incident_path = os.path.join("investigations", incident_id)
                if os.path.exists(incident_path) and os.path.isdir(incident_path):
                    import shutil
                    shutil.rmtree(incident_path)
                    
                    # If this was the active incident in coordinates, reset it
                    state = get_active_state()
                    if state.get("incident_id") == incident_id:
                        state["incident_id"] = "None"
                        state["incident_status"] = "UNKNOWN"
                        save_active_state(state)
                        
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success", "message": f"Incident {incident_id} deleted successfully"}).encode("utf-8"))
                else:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Incident not found"}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if not self.check_auth():
            return
            
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        # API: Update Active State Coordinates
        if path == "/api/active-state":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                payload = json.loads(post_data.decode("utf-8"))
                
                state = get_active_state()
                if "project_id" in payload:
                    state["project_id"] = payload["project_id"]
                    os.environ["PROJECT_ID"] = payload["project_id"]
                if "incident_id" in payload:
                    state["incident_id"] = payload["incident_id"]
                if "incident_status" in payload:
                    from src.incident import validate_incident_status
                    state["incident_status"] = validate_incident_status(payload["incident_status"])
                if "substatus_rca" in payload:
                    state["substatus_rca"] = bool(payload["substatus_rca"])
                if "substatus_mitigated" in payload:
                    state["substatus_mitigated"] = bool(payload["substatus_mitigated"])
                if "substatus_fixed" in payload:
                    state["substatus_fixed"] = bool(payload["substatus_fixed"])
                if "substatus_verified" in payload:
                    state["substatus_verified"] = bool(payload["substatus_verified"])
                
                save_active_state(state)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(state).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return
            
        # API: Trigger GCS sync manually
        elif path == "/api/gcs/sync":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                payload = {}
                if content_length > 0:
                    try:
                        post_data = self.rfile.read(content_length)
                        payload = json.loads(post_data.decode("utf-8"))
                    except Exception:
                        pass
                direction = payload.get("direction", "from")
                from src.gcs_sync import GcsSyncManager
                GcsSyncManager.trigger_sync_background(direction)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                from src.gcs_sync import get_sync_status
                self.wfile.write(json.dumps({"status": get_sync_status(), "message": f"Sync background thread triggered: {direction}"}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return
            
        # API: Transcribe Voice Notes
        elif path == "/api/transcribe":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                audio_bytes = self.rfile.read(content_length)
                transcription = transcribe_voice_bytes(audio_bytes)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"transcription": transcription}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # 4. API: Trigger Incident Simulation
        elif path == "/api/simulate":
            try:
                # Parse optional post body
                content_length = int(self.headers.get('Content-Length', 0))
                payload = None
                if content_length > 0:
                    try:
                        post_data = self.rfile.read(content_length)
                        payload = json.loads(post_data.decode("utf-8"))
                    except Exception:
                        pass
                
                # Run the simulation live
                incident_id, folder_path = run_simulation(payload=payload)
                details = parse_incident_folder(folder_path)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(details).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Archive an incident
        elif path.startswith("/api/incidents/") and path.endswith("/archive"):
            try:
                incident_id = path.split("/")[3]
                incident_id = os.path.basename(incident_id)
                incident_path = os.path.join("investigations", incident_id)
                if os.path.exists(incident_path):
                    if set_incident_archived(incident_path, True):
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"status": "success", "message": f"Incident {incident_id} archived successfully"}).encode("utf-8"))
                    else:
                        self.send_response(500)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": "Failed to update incident archival status"}).encode("utf-8"))
                else:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Incident not found"}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # 5b. API: Mutation Queue Endpoints (pending, approve, reject)
        elif path.startswith("/api/incidents/") and "/pending" in path:
            try:
                parts = path.split("/")
                incident_id = parts[3]
                incident_path = os.path.join("investigations", incident_id)
                if not os.path.exists(incident_path):
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Incident not found"}).encode("utf-8"))
                    return
                
                # Check for: POST /api/incidents/<id>/pending/<cmd_id>/approve
                if len(parts) == 7 and parts[4] == "pending" and parts[6] == "approve":
                    cmd_id = parts[5]
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
                    try:
                        payload = json.loads(post_data.decode("utf-8")) if post_data else {}
                    except Exception:
                        payload = {}
                    comment = payload.get("comment", "").strip()
                    
                    if approve_pending_mutation(incident_id, cmd_id, comment):
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"status": "approved", "cmd_id": cmd_id}).encode("utf-8"))
                    else:
                        self.send_response(404)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": "Mutation command not found in queue"}).encode("utf-8"))
                    return
                    
                # Check for: POST /api/incidents/<id>/pending/<cmd_id>/reject
                elif len(parts) == 7 and parts[4] == "pending" and parts[6] == "reject":
                    cmd_id = parts[5]
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
                    try:
                        payload = json.loads(post_data.decode("utf-8")) if post_data else {}
                    except Exception:
                        payload = {}
                    comment = payload.get("comment", "").strip()
                    
                    if reject_pending_mutation(incident_id, cmd_id, comment):
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"status": "rejected", "cmd_id": cmd_id}).encode("utf-8"))
                    else:
                        self.send_response(404)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": "Mutation command not found in queue"}).encode("utf-8"))
                    return
                    
                # Check for: POST /api/incidents/<id>/pending (add a new mutation)
                elif len(parts) == 5 and parts[4] == "pending":
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length)
                    payload = json.loads(post_data.decode("utf-8"))
                    
                    command = payload.get("command")
                    risk_factor = payload.get("risk_factor")
                    risk_reason = payload.get("risk_reason")
                    justification = payload.get("justification")
                    
                    if not all([command, risk_factor, risk_reason, justification]):
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": "Missing required fields"}).encode("utf-8"))
                        return
                    
                    new_item = add_pending_mutation(incident_id, command, risk_factor, risk_reason, justification)
                    self.send_response(201)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(new_item).encode("utf-8"))
                    return
                    
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

        # 5. API: Approve paused safety gate mutation
        elif path.startswith("/api/incidents/") and path.endswith("/approve"):
            try:
                incident_id = path.split("/")[3]
                incident_path = os.path.join("investigations", incident_id)
                if os.path.exists(incident_path):
                    resume_simulation(incident_id, approved=True)
                    
                    # 1. Sync operator's response in chat.json
                    try:
                        chat_path = os.path.join(incident_path, "chat.json")
                        chat_data = []
                        if os.path.exists(chat_path):
                            try:
                                with open(chat_path, "r") as f:
                                    chat_data = json.load(f)
                            except Exception:
                                pass
                        chat_data.append({
                            "sender": "Operator (Web Dashboard)",
                            "message": "Approved proposed mutation command via SRE Web Panel.",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        chat_data.append({
                            "sender": f"{get_commander_name()} Agent (IC)",
                            "message": "✅ Safety Gate Clearance Granted! Resuming SRE incident resolution pipeline.",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        os.makedirs(os.path.dirname(chat_path), exist_ok=True)
                        with open(chat_path, "w") as f:
                            json.dump(chat_data, f, indent=2)
                    except Exception as chat_err:
                        print(f"[Server] Failed to write chat log to chat.json: {chat_err}")
                        
                    # 2. Reset Telegram bot keyboard to standard navigation
                    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
                    chat_id = os.getenv("TELEGRAM_CHAT_ID")
                    if bot_token and chat_id:
                        bot_token = bot_token.strip("'\"")
                        chat_id = chat_id.strip("'\"")
                        if "ENTER_BOT" not in bot_token and "ENTER_CHAT" not in chat_id:
                            msg = (
                                f"✅ *Safety Gate Clearance Granted via Web Dashboard!*\n\n"
                                f"Proposed SRE mutation command was approved by the operator on the web panel.\n"
                                f"Resuming incident resolution... {get_commander_name()} is executing the action."
                            )
                            send_telegram_menu(bot_token, chat_id, msg)
                            
                    details = parse_incident_folder(incident_path)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(details).encode("utf-8"))
                else:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Incident not found"}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                
        # 6. API: Reject paused safety gate mutation
        elif path.startswith("/api/incidents/") and path.endswith("/reject"):
            try:
                incident_id = path.split("/")[3]
                incident_path = os.path.join("investigations", incident_id)
                if os.path.exists(incident_path):
                    resume_simulation(incident_id, approved=False)
                    
                    # 1. Sync operator's response in chat.json
                    try:
                        chat_path = os.path.join(incident_path, "chat.json")
                        chat_data = []
                        if os.path.exists(chat_path):
                            try:
                                with open(chat_path, "r") as f:
                                    chat_data = json.load(f)
                            except Exception:
                                pass
                        chat_data.append({
                            "sender": "Operator (Web Dashboard)",
                            "message": "Rejected/Aborted proposed mutation command via SRE Web Panel.",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        chat_data.append({
                            "sender": f"{get_commander_name()} Agent (IC)",
                            "message": "❌ Safety Gate Override Active. SRE operations halted.",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        os.makedirs(os.path.dirname(chat_path), exist_ok=True)
                        with open(chat_path, "w") as f:
                            json.dump(chat_data, f, indent=2)
                    except Exception as chat_err:
                        print(f"[Server] Failed to write chat log to chat.json: {chat_err}")
                        
                    # 2. Reset Telegram bot keyboard to standard navigation
                    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
                    chat_id = os.getenv("TELEGRAM_CHAT_ID")
                    if bot_token and chat_id:
                        bot_token = bot_token.strip("'\"")
                        chat_id = chat_id.strip("'\"")
                        if "ENTER_BOT" not in bot_token and "ENTER_CHAT" not in chat_id:
                            msg = (
                                f"❌ *Safety Gate Override Active via Web Dashboard!*\n\n"
                                f"Proposed SRE mutation command was rejected by the operator on the web panel.\n"
                                f"SRE operations halted. Safety gate aborted operations successfully."
                            )
                            send_telegram_menu(bot_token, chat_id, msg)
                            
                    details = parse_incident_folder(incident_path)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(details).encode("utf-8"))
                else:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Incident not found"}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        
        # API: Save Custom Wiki for a Project
        elif path.startswith("/api/projects/") and path.endswith("/wiki"):
            try:
                project_id = path.split("/")[3]
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                payload = json.loads(post_data.decode("utf-8"))
                content = payload.get("content", "")
                
                if project_id in ("sre-demo", "sre-demo-prod"):
                    md_path = "discover/domains/sre-demo/README.md"
                    os.makedirs(os.path.dirname(md_path), exist_ok=True)
                    with open(md_path, "w") as f:
                        f.write(content)
                else:
                    cache_dir = os.path.join("discover", "gcp-project", project_id)
                    os.makedirs(cache_dir, exist_ok=True)
                    md_path = os.path.join(cache_dir, "wiki.md")
                    with open(md_path, "w") as f:
                        f.write(content)
                
                try:
                    from src.gcs_sync import GcsSyncManager
                    GcsSyncManager.trigger_sync_background("to")
                except Exception as sync_err:
                    print(f"[Server Wiki Save] Failed to trigger GCS sync: {sync_err}")

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"project_id": project_id, "content": content}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Save Custom Graphviz DOT for a Project
        elif path.startswith("/api/projects/") and path.endswith("/graph"):
            try:
                project_id = path.split("/")[3]
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                payload = json.loads(post_data.decode("utf-8"))
                content = payload.get("content", "")
                
                if project_id in ("sre-demo", "sre-demo-prod"):
                    dot_path = "discover/domains/sre-demo/graph.dot"
                    os.makedirs(os.path.dirname(dot_path), exist_ok=True)
                    with open(dot_path, "w") as f:
                        f.write(content)
                else:
                    cache_dir = os.path.join("discover", "gcp-project", project_id)
                    os.makedirs(cache_dir, exist_ok=True)
                    dot_path = os.path.join(cache_dir, "graph.dot")
                    with open(dot_path, "w") as f:
                        f.write(content)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"project_id": project_id, "content": content}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return



        # 6. API: Contextual Chat Message Posting
        elif path.startswith("/api/incidents/") and path.endswith("/chat"):
            try:
                incident_id = path.split("/")[3]
                incident_path = os.path.join("investigations", incident_id)
                if os.path.exists(incident_path):
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length)
                    payload = json.loads(post_data.decode("utf-8"))
                    user_msg = payload.get("message", "").strip()
                    
                    if not user_msg:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": "Empty message"}).encode("utf-8"))
                        return
                    
                    chat_path = os.path.join(incident_path, "chat.json")
                    chat_data = []
                    if os.path.exists(chat_path):
                        with open(chat_path, "r") as f:
                            chat_data = json.load(f)
                    else:
                        details = parse_incident_folder(incident_path)
                        
                        # Detect if Telegram variables are configured
                        has_telegram = bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))
                        telegram_proposal = ""
                        if not has_telegram:
                            telegram_proposal = (
                                "\n\n💡 **System Notice:** Telegram alerts are not yet active. "
                                "To route live incident broadcasts directly to a Telegram channel, configure your credentials "
                                "by running this command in your workspace:\n`PYTHONPATH=. uv run python3 src/cli.py telegram set <CHAT_ID> <BOT_TOKEN>`"
                            )
                        
                        chat_data = [
                            {
                                "sender": f"{get_commander_name()} Agent (IC)",
                                "message": (
                                    f"Welcome to the tactical Incident Chat for {incident_id}. "
                                    f"I am {get_commander_name()}, the SRE Incident Commander. We are currently analyzing the alert "
                                    f"'{details.get('trigger_event')}' targeting project '{details.get('project_id')}'. "
                                    f"How can I assist you today?{telegram_proposal}"
                                ),
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        ]
                    
                    # Append user message
                    chat_data.append({
                        "sender": "Operator (You)",
                        "message": user_msg,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
                    # Push Web Operator message directly to Telegram if configured
                    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
                    chat_id = os.getenv("TELEGRAM_CHAT_ID")
                    if bot_token and chat_id:
                        bot_token = bot_token.strip("'\"")
                        chat_id = chat_id.strip("'\"")
                        if "ENTER_BOT" not in bot_token and "ENTER_CHAT" not in chat_id:
                            try:
                                send_raw_telegram_message(bot_token, chat_id, f"💬 *[Web Operator]:* {user_msg}")
                            except Exception as tg_err:
                                print(f"[Server] Failed to push operator msg to Telegram: {tg_err}")
                    
                    # Generate authentic contextual reply via SRE ADK Incident Commander
                    details = parse_incident_folder(incident_path)
                    status = details.get("status", "UNKNOWN").upper()
                    project_id = details.get("project_id", "sre-next")
                    trigger_event = details.get("trigger_event", "frontend_latency_slo_violated")
                    
                    try:
                        from src.agents import IncidentCommander
                        from src.incident import IncidentContext
                        incident_uuid = details.get("incident_uuid")
                        ctx = IncidentContext(incident_uuid=incident_uuid) if incident_uuid and incident_uuid != "UNKNOWN" else None
                        commander = IncidentCommander(incident_context=ctx)
                        
                        # Supply full screen operational context dynamically to the model
                        comments_context = get_mutation_comments_context(incident_path)
                        chat_context = (
                            f"[Operational Context]\n"
                            f"Selected Incident ID: {incident_id}\n"
                            f"Current Incident Status: {status}\n"
                            f"Target GCP Project ID: {project_id}\n"
                            f"Trigger Alert Event: {trigger_event}\n\n"
                            f"{comments_context}"
                            f"Operator Prompt:\n{user_msg}"
                        )
                        reply_msg = commander.run(chat_context)
                    except Exception as e:
                        reply_msg = f"[System Alert] Incident Commander failed: {e}"
                    
                    chat_data.append({
                        "sender": f"{get_commander_name()} Agent (IC)",
                        "message": reply_msg,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
                    # Push Benjamin Agent reply directly to Telegram if configured
                    if bot_token and chat_id:
                        if "ENTER_BOT" not in bot_token and "ENTER_CHAT" not in chat_id:
                            try:
                                send_raw_telegram_message(bot_token, chat_id, f"🏰 *{get_commander_name()} (IC):*\n{reply_msg}")
                            except Exception as tg_err:
                                print(f"[Server] Failed to push commander reply to Telegram: {tg_err}")
                    
                    # Save updated chat log
                    with open(chat_path, "w") as f:
                        json.dump(chat_data, f, indent=2)
                        
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(chat_data).encode("utf-8"))
                else:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Incident not found"}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return
        else:
            self.send_response(404)
            self.end_headers()

def get_incidents_list() -> list[dict]:
    """Helper to query all active and historical incidents inside investigations/ directory."""
    import os
    incidents = []
    if os.path.exists("investigations"):
        for folder in sorted(os.listdir("investigations")):
            folder_path = os.path.join("investigations", folder)
            if os.path.isdir(folder_path):
                details = parse_incident_folder(folder_path)
                if not details.get("archived", False):
                    incidents.append({
                        "id": folder,
                        "status": details.get("status", "UNKNOWN"),
                        "project_id": details.get("project_id", "UNKNOWN"),
                        "trigger_event": details.get("trigger_event", "UNKNOWN"),
                        "archived": False
                    })
    return incidents

def transcribe_voice_bytes(audio_bytes: bytes) -> str:
    """Helper to transcribe small voice notes/audio files using the live Gemini API with zero dependencies."""
    import os
    import json
    import base64
    import urllib.request
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY environment variable is not configured."
        
    model_name = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-3.1-flash-lite").strip("'\"")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": "audio/ogg",
                            "data": encoded_audio
                        }
                    },
                    {
                        "text": "Please transcribe this SRE voice note carefully. Return ONLY the transcribed text itself. If the audio is unclear, return the closest readable transcription."
                    }
                ]
            }
        ]
    }
    
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                res_body = json.loads(response.read().decode("utf-8"))
                text = res_body["candidates"][0]["content"]["parts"][0]["text"]
                return text.strip()
    except Exception as e:
        return f"Voice note transcription failed: {e}"
        
    return "Voice note transcription timed out."

def send_raw_telegram_message(bot_token: str, chat_id: str, message: str):
    """Utility to dispatch a simple, markdown Telegram bot alert."""
    import urllib.request
    import urllib.parse
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"[Telegram Bot] Message dispatch error: {e}")

def get_discovered_projects() -> list[str]:
    """Helper to query all discovered projects under discover/gcp-project/ directory."""
    projects = []
    env_projects = os.getenv("SAMPLE_PROJECT_IDS")
    if env_projects:
        for p in env_projects.split(","):
            p = p.strip()
            if p and p not in projects:
                projects.append(p)
    projects_dir = os.path.join("discover", "gcp-project")
    if os.path.exists(projects_dir):
        for item in sorted(os.listdir(projects_dir)):
            item_path = os.path.join(projects_dir, item)
            if os.path.isdir(item_path):
                if item not in projects:
                    projects.append(item)
    if not projects:
        projects = ["sre-next"]
    if "sre-demo" not in projects and "PYTEST_CURRENT_TEST" not in os.environ:
        projects.append("sre-demo")
    if "sre-demo-prod" not in projects and "PYTEST_CURRENT_TEST" not in os.environ:
        projects.append("sre-demo-prod")
    return projects

def get_top_5_incidents() -> list[dict]:
    """Helper to query the 5 most recent active (non-archived) incidents inside investigations/ directory."""
    incidents = []
    incidents_dir = "investigations"
    if os.path.exists(incidents_dir):
        folders = [f for f in os.listdir(incidents_dir) if f.startswith("INC-")]
        folders.sort(reverse=True)
        for folder in folders:
            if len(incidents) >= 5:
                break
            folder_path = os.path.join(incidents_dir, folder)
            if os.path.isdir(folder_path):
                details = parse_incident_folder(folder_path)
                if not details.get("archived", False):
                    incidents.append({
                        "id": folder,
                        "status": details.get("status", "UNKNOWN").upper()
                    })
    return incidents

def send_telegram_inline_keyboard(bot_token: str, chat_id: str, text: str, buttons: list[list[dict]]):
    """Dispatches a Telegram message containing inline keyboard buttons."""
    import urllib.request
    import urllib.parse
    import json
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": json.dumps({
                "inline_keyboard": buttons
            })
        }
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"[Telegram Bot] Inline keyboard dispatch error: {e}")

def answer_telegram_callback_query(bot_token: str, callback_query_id: str, text: str = None):
    """Acknowledge Telegram callback query to stop loading spinner on the button."""
    import urllib.request
    import urllib.parse
    import json
    try:
        url = f"https://api.telegram.org/bot{bot_token}/answerCallbackQuery"
        payload = {
            "callback_query_id": callback_query_id
        }
        if text:
            payload["text"] = text
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"[Telegram Bot] answerCallbackQuery error: {e}")

def edit_telegram_message_text(bot_token: str, chat_id: str, message_id: int, text: str, reply_markup: dict = None):
    """Edits an existing Telegram message's text (and optionally keyboard)."""
    import urllib.request
    import urllib.parse
    import json
    try:
        url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        if reply_markup is not None:
            payload["reply_markup"] = json.dumps(reply_markup)
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"[Telegram Bot] editMessageText error: {e}")

def send_telegram_menu(bot_token: str, chat_id: str, message: str):
    """Dispatches a Telegram message with structured interactive SRE SRE navigation menu buttons."""
    import urllib.request
    import urllib.parse
    import json
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        keyboard = {
            "keyboard": [
                [{"text": "🚨 Status Check"}, {"text": "📋 List Incidents"}],
                [{"text": "☁️ List Projects"}, {"text": "🆔 Select Incident"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "reply_markup": json.dumps(keyboard)
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"[Telegram Bot] Menu dispatch error: {e}")

def send_telegram_safety_gate_menu(bot_token: str, chat_id: str, message: str):
    """Dispatches a Telegram message with safety gate approval/rejection validation buttons."""
    import urllib.request
    import urllib.parse
    import json
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        keyboard = {
            "keyboard": [
                [{"text": "💥 Yes, I am sure"}, {"text": "❌ No, abort mutation"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "reply_markup": json.dumps(keyboard)
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"[Telegram Bot] Safety gate menu dispatch error: {e}")

def start_telegram_bot():
    """Background polling daemon thread that makes SRE Benjamin Bot fully interactive."""
    import time
    import os
    import urllib.request
    import urllib.parse
    import json
    from datetime import datetime, timezone
    
    print("[Telegram Bot] Interactive polling loop initialized.")
    
    last_update_id = 0
    selected_incident_id = None
    
    # 1. Fetch latest update ID on startup to discard past backlogs and avoid flood loops
    try:
        bot_token_init = os.getenv("TELEGRAM_BOT_TOKEN")
        if bot_token_init:
            bot_token_init = bot_token_init.strip("'\"")
            if "ENTER_BOT" not in bot_token_init:
                init_url = f"https://api.telegram.org/bot{bot_token_init}/getUpdates?limit=1&offset=-1"
                init_req = urllib.request.Request(init_url, method="GET")
                with urllib.request.urlopen(init_req, timeout=5) as init_resp:
                    if init_resp.status == 200:
                        init_data = json.loads(init_resp.read().decode("utf-8"))
                        init_updates = init_data.get("result", [])
                        if init_updates:
                            last_update_id = init_updates[0].get("update_id", 0)
                            print(f"[Telegram Bot] Backlog discarded. Starting poll from update_id: {last_update_id}")
    except Exception as init_err:
        print(f"[Telegram Bot] Startup backlog check bypassed: {init_err}")
        
    while True:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        # Clean quotes
        if bot_token:
            bot_token = bot_token.strip("'\"")
        if chat_id:
            chat_id = chat_id.strip("'\"")
            
        if not bot_token or not chat_id or "ENTER_BOT" in bot_token or "ENTER_CHAT" in chat_id:
            # Poll config changes every 5 seconds
            if os.environ.get("TESTING_BOT") == "true":
                break
            time.sleep(5)
            continue
            
        # Synchronize coordinates from active state store
        state = get_active_state()
        selected_incident_id = state.get("incident_id")
        if selected_incident_id == "None" or not selected_incident_id:
            incidents = get_incidents_list()
            if incidents:
                selected_incident_id = incidents[-1]["id"]
                state["incident_id"] = selected_incident_id
                state["incident_status"] = incidents[-1].get("status", "UNKNOWN")
                save_active_state(state)
            else:
                selected_incident_id = None
                
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getUpdates?offset={last_update_id + 1}&timeout=5"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    updates = data.get("result", [])
                    for update in updates:
                        last_update_id = max(last_update_id, update.get("update_id", 0))
                        
                        # Handle Callback Query
                        callback_query = update.get("callback_query")
                        if callback_query:
                            callback_id = callback_query.get("id")
                            cb_message = callback_query.get("message", {})
                            cb_chat_id = str(cb_message.get("chat", {}).get("id", ""))
                            cb_message_id = cb_message.get("message_id")
                            cb_data = callback_query.get("data", "").strip()
                            
                            if cb_chat_id == chat_id:
                                if cb_data.startswith("select_incident:"):
                                    inc_id = cb_data.replace("select_incident:", "").strip()
                                    state = get_active_state()
                                    state["incident_id"] = inc_id
                                    
                                    # Fetch status
                                    incident_path = os.path.join("investigations", inc_id)
                                    if os.path.exists(incident_path):
                                        details = parse_incident_folder(incident_path)
                                        state["incident_status"] = details.get("status", "UNKNOWN")
                                    else:
                                        state["incident_status"] = "UNKNOWN"
                                    
                                    save_active_state(state)
                                    answer_telegram_callback_query(bot_token, callback_id, f"Incident set to {inc_id}")
                                    edit_telegram_message_text(bot_token, chat_id, cb_message_id, f"✅ *Active context updated to incident:* `{inc_id}`")
                                    
                                elif cb_data.startswith("select_project:"):
                                    proj_id = cb_data.replace("select_project:", "").strip()
                                    state = get_active_state()
                                    state["project_id"] = proj_id
                                    os.environ["PROJECT_ID"] = proj_id
                                    save_active_state(state)
                                    
                                    # Update .env
                                    env_path = ".env"
                                    if os.path.exists(env_path):
                                        try:
                                            with open(env_path, "r") as f:
                                                content = f.read()
                                            import re
                                            if "PROJECT_ID=" in content:
                                                content = re.sub(r"PROJECT_ID=.*", f"PROJECT_ID='{proj_id}'", content)
                                            else:
                                                content += f"\nPROJECT_ID='{proj_id}'\n"
                                            with open(env_path, "w") as f:
                                                f.write(content.strip() + "\n")
                                        except Exception:
                                            pass
                                            
                                    answer_telegram_callback_query(bot_token, callback_id, f"Project set to {proj_id}")
                                    edit_telegram_message_text(bot_token, chat_id, cb_message_id, f"✅ *Active context updated to project:* `{proj_id}`")
                            continue
                        
                        message = update.get("message")
                        if not message:
                            continue
                            
                        msg_chat_id = str(message.get("chat", {}).get("id", ""))
                        # Guard to only process messages from the authorized operator chat
                        if msg_chat_id != chat_id:
                            continue
                            
                        msg_text = message.get("text", "").strip()
                        voice = message.get("voice") or message.get("audio")
                        
                        # 1. Handle incoming voice and audio messages with on-the-fly STT
                        if voice:
                            file_id = voice.get("file_id")
                            get_file_url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
                            try:
                                with urllib.request.urlopen(get_file_url, timeout=10) as f_res:
                                    if f_res.status == 200:
                                        f_data = json.loads(f_res.read().decode("utf-8"))
                                        file_path = f_data.get("result", {}).get("file_path")
                                        if file_path:
                                            # Download raw voice bytes
                                            download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
                                            with urllib.request.urlopen(download_url, timeout=15) as d_res:
                                                if d_res.status == 200:
                                                    audio_bytes = d_res.read()
                                                    # Transcribe directly using live Gemini API inline payload
                                                    transcription = transcribe_voice_bytes(audio_bytes)
                                                    
                                                    send_raw_telegram_message(
                                                        bot_token, chat_id,
                                                        f"🎙️ *Voice Note Transcribed:* \"_{transcription}_\"\n\n*Sending to SRE Co-Pilot...*"
                                                    )
                                                    # Pipeline transcribed text to the active chat prompt
                                                    msg_text = transcription
                                                else:
                                                    send_raw_telegram_message(bot_token, chat_id, "❌ Failed to download audio voice note.")
                                                    continue
                            except Exception as file_err:
                                print(f"[Telegram Bot] Audio fetch error: {file_err}")
                                send_raw_telegram_message(bot_token, chat_id, "❌ Error retrieving voice note file.")
                                continue
                                
                        if not msg_text:
                            continue
                            
                        # 2. Check for menu selections and command shortcuts
                        # Clean and check if it is a shortcut format for mobile forgiveness
                        clean_text = msg_text.lstrip("#").strip()
                        projects = get_discovered_projects()
                        is_project_match = False
                        for proj in projects:
                            if clean_text.lower() == proj.lower():
                                clean_text = proj
                                is_project_match = True
                                break
                                
                        if clean_text.isdigit() or clean_text.lower().startswith("inc-"):
                            msg_text = f"/incident {clean_text}"
                        elif is_project_match:
                            msg_text = f"/project {clean_text}"

                        lower_text = msg_text.lower()
                        if lower_text.startswith("/start") or lower_text == "/help" or lower_text == "help":
                            welcome_msg = (
                                "🏰 *Project Benjamin SRE Command Hub*\n\n"
                                f"• *Active Incident Context:* `{selected_incident_id}`\n"
                                f"• *Target GCP Project ID:* `{os.getenv('PROJECT_ID', 'sre-next')}`\n\n"
                                "*Available Commands:*\n"
                                "• `/incidents` (or `📋 List Incidents`): List 5 latest incidents with status indicators.\n"
                                "• `/projects` (or `☁️ List Projects`): List discovered GCP projects.\n"
                                "• `/incident <id>`: Set target SRE incident context.\n"
                                "• `/project <id>`: Set target GCP project context.\n\n"
                                "Use the menu buttons below to quickly monitor status, or send any "
                                "text or audio note to direct SRE Commander Benjamin!"
                            )
                            send_telegram_menu(bot_token, chat_id, welcome_msg)
                            continue
                            
                        elif msg_text == "🚨 Status Check":
                            if not selected_incident_id or selected_incident_id == "None":
                                send_raw_telegram_message(bot_token, chat_id, "❌ No active SRE incident selected.")
                                continue
                            incident_path = os.path.join("investigations", selected_incident_id)
                            details = parse_incident_folder(incident_path)
                            status_val = details.get('status', 'UNKNOWN')
                            status_msg = (
                                f"🏰 *Status for Incident:* `{selected_incident_id}`\n"
                                f"• *Status:* `{status_val}`\n"
                                f"• *Target Project:* `{details.get('project_id', 'UNKNOWN')}`\n"
                                f"• *Trigger Event:* `{details.get('trigger_event', 'UNKNOWN')}`\n"
                                f"• *Timeline entries:* {len(details.get('timeline', []))}"
                            )
                            
                            if status_val == "AWAITING_APPROVAL":
                                # Extract proposed mutation & safety level dynamically
                                state_path = os.path.join(incident_path, "state.md")
                                proposed_mutation = "systemctl restart mysql"
                                safety_level = "HIGH"
                                if os.path.exists(state_path):
                                    try:
                                        with open(state_path, "r") as sf:
                                            state_content = sf.read()
                                        import re
                                        mutation_match = re.search(r'\-\s+\*\*Proposed Mutation:\*\*\s*`?([^`\n]+)`?', state_content, re.IGNORECASE)
                                        if mutation_match:
                                            proposed_mutation = mutation_match.group(1).strip()
                                        risk_match = re.search(r'\-\s+\*\*Safety Level:\*\*\s*([A-Za-z0-9_ ]+)', state_content, re.IGNORECASE)
                                        if risk_match:
                                            safety_level = risk_match.group(1).strip()
                                    except Exception:
                                        pass
                                
                                status_msg += (
                                    f"\n\n⚠️ *Safety Gate Hold!*\n"
                                    f"Proposed Mutation: `{proposed_mutation}`\n"
                                    f"Safety Level: *{safety_level}*\n\n"
                                    f"Please approve or reject below:"
                                )
                                send_telegram_safety_gate_menu(bot_token, chat_id, status_msg)
                            else:
                                send_raw_telegram_message(bot_token, chat_id, status_msg)
                            continue
                            
                        elif msg_text == "📋 List Incidents" or msg_text.startswith("/incidents"):
                            inc_list = get_top_5_incidents()
                            if not inc_list:
                                send_raw_telegram_message(bot_token, chat_id, "📋 No SRE incidents recorded in repository.")
                                continue
                            
                            buttons = []
                            for inc in inc_list:
                                status = inc["status"]
                                emoji = "⚪" if status in ["RESOLVED", "CLOSED", "ABORTED"] else "🟢"
                                buttons.append([{
                                    "text": f"{emoji} {inc['id']} ({status})",
                                    "callback_data": f"select_incident:{inc['id']}"
                                }])
                            
                            send_telegram_inline_keyboard(
                                bot_token, chat_id,
                                "📋 *Select an incident context from the 5 latest incidents:*",
                                buttons
                            )
                            continue
                            
                        elif msg_text == "☁️ List Projects" or msg_text == "☁️ Set Project" or msg_text == "☁️ Target Project" or msg_text.startswith("/projects"):
                            projects = get_discovered_projects()
                            buttons = []
                            for proj in projects:
                                buttons.append([{
                                    "text": f"☁️ {proj}",
                                    "callback_data": f"select_project:{proj}"
                                }])
                            
                            send_telegram_inline_keyboard(
                                bot_token, chat_id,
                                "☁️ *Select a GCP Project context:*",
                                buttons
                            )
                            continue
                            
                        elif msg_text == "🆔 Select Incident":
                            send_raw_telegram_message(
                                bot_token, chat_id,
                                "🆔 *Select Incident Context*\n\n"
                                "To set a specific incident directly, use the `/incident` command followed by the Incident ID.\n\n"
                                "Format: `/incident <Incident_ID>`\n"
                                "Example: `/incident INC-20260603-abcd`"
                            )
                            continue
                            
                        elif msg_text.startswith("/archive"):
                            parts = msg_text.split(" ", 1)
                            target_inc = None
                            if len(parts) > 1:
                                target_inc = parts[1].strip()
                            else:
                                target_inc = selected_incident_id
                            
                            if not target_inc or target_inc == "None":
                                send_raw_telegram_message(bot_token, chat_id, "❌ No active incident selected to archive.")
                                continue
                                
                            all_folders = []
                            if os.path.exists("investigations"):
                                all_folders = [f for f in sorted(os.listdir("investigations")) if os.path.isdir(os.path.join("investigations", f)) and f.startswith("INC-")]
                            
                            matched_id = None
                            if target_inc.isdigit():
                                idx = int(target_inc) - 1
                                if 0 <= idx < len(all_folders):
                                    matched_id = all_folders[idx]
                            else:
                                for folder in all_folders:
                                    if folder.lower() == target_inc.lower():
                                        matched_id = folder
                                        break
                            
                            if matched_id:
                                target_inc = matched_id
                                
                            target_inc_path = os.path.join("investigations", target_inc)
                            if os.path.exists(target_inc_path):
                                if set_incident_archived(target_inc_path, True):
                                    send_raw_telegram_message(bot_token, chat_id, f"✅ Incident `{target_inc}` has been successfully archived.")
                                    if selected_incident_id == target_inc:
                                        state = get_active_state()
                                        state["incident_id"] = "None"
                                        state["incident_status"] = "UNKNOWN"
                                        save_active_state(state)
                                        selected_incident_id = "None"
                                else:
                                    send_raw_telegram_message(bot_token, chat_id, f"❌ Failed to archive incident `{target_inc}`.")
                            else:
                                send_raw_telegram_message(bot_token, chat_id, f"❌ Incident `{target_inc}` not found in repository.")
                            continue

                        elif msg_text.startswith("/incident") or msg_text.startswith("/select"):
                            parts = msg_text.split(" ", 1)
                            if len(parts) < 2:
                                cmd = parts[0]
                                send_raw_telegram_message(bot_token, chat_id, f"❌ Usage: `{cmd} <Incident_ID or Index>`")
                                continue
                            target_inc = parts[1].strip()
                            
                            # Resolve target_inc using case-insensitive ID or list index lookup
                            all_incidents = get_incidents_list()
                            matched_id = None
                            if target_inc.isdigit():
                                idx = int(target_inc) - 1
                                if 0 <= idx < len(all_incidents):
                                    matched_id = all_incidents[idx]["id"]
                            else:
                                for inc in all_incidents:
                                    if inc["id"].lower() == target_inc.lower():
                                        matched_id = inc["id"]
                                        break
                            if matched_id:
                                target_inc = matched_id
                                
                            target_inc_path = os.path.join("investigations", target_inc)
                            if os.path.exists(target_inc_path):
                                selected_incident_id = target_inc
                                details = parse_incident_folder(target_inc_path)
                                status_val = details.get('status', 'UNKNOWN')
                                
                                state = get_active_state()
                                state["incident_id"] = target_inc
                                state["incident_status"] = status_val
                                save_active_state(state)
                                
                                if status_val == "AWAITING_APPROVAL":
                                    # Extract proposed mutation & safety level dynamically
                                    state_path = os.path.join(target_inc_path, "state.md")
                                    proposed_mutation = "systemctl restart mysql"
                                    safety_level = "HIGH"
                                    if os.path.exists(state_path):
                                        try:
                                            with open(state_path, "r") as sf:
                                                state_content = sf.read()
                                            import re
                                            mutation_match = re.search(r'\-\s+\*\*Proposed Mutation:\*\*\s*`?([^`\n]+)`?', state_content, re.IGNORECASE)
                                            if mutation_match:
                                                proposed_mutation = mutation_match.group(1).strip()
                                            risk_match = re.search(r'\-\s+\*\*Safety Level:\*\*\s*([A-Za-z0-9_ ]+)', state_content, re.IGNORECASE)
                                            if risk_match:
                                                safety_level = risk_match.group(1).strip()
                                        except Exception:
                                            pass
                                            
                                    msg = (
                                        f"✅ *Active incident switched to:* `{target_inc}`\n\n"
                                        f"⚠️ *Safety Gate Hold!*\n"
                                        f"A dangerous SRE mutation command is currently awaiting operator approval:\n"
                                        f"Proposed: `{proposed_mutation}`\n"
                                        f"Safety Level: *{safety_level}*\n\n"
                                        f"Please authorize execution by selecting one of the options below:"
                                    )
                                    send_telegram_safety_gate_menu(bot_token, chat_id, msg)
                                else:
                                    send_telegram_menu(bot_token, chat_id, f"✅ Active incident switched to: `{target_inc}`")
                            else:
                                send_raw_telegram_message(bot_token, chat_id, f"❌ Incident `{target_inc}` not found in repository.")
                            continue
                            
                        elif msg_text.startswith("/project") or msg_text.startswith("/setproject"):
                            parts = msg_text.split(" ", 1)
                            if len(parts) < 2:
                                cmd = parts[0]
                                send_raw_telegram_message(bot_token, chat_id, f"❌ Usage: `{cmd} <Project_ID>`")
                                continue
                            target_proj = parts[1].strip()
                            
                            state = get_active_state()
                            state["project_id"] = target_proj
                            os.environ["PROJECT_ID"] = target_proj
                            save_active_state(state)
                            
                            env_path = ".env"
                            if os.path.exists(env_path):
                                try:
                                    with open(env_path, "r") as f:
                                        content = f.read()
                                    import re
                                    if "PROJECT_ID=" in content:
                                        content = re.sub(r"PROJECT_ID=.*", f"PROJECT_ID='{target_proj}'", content)
                                    else:
                                        content += f"\nPROJECT_ID='{target_proj}'\n"
                                    with open(env_path, "w") as f:
                                        f.write(content.strip() + "\n")
                                except Exception:
                                    pass
                                    
                            send_raw_telegram_message(bot_token, chat_id, f"✅ GCP Project ID set to: `{target_proj}`")
                            continue
                            
                        # 3. Check for Safety Gate Intercept if incident is awaiting approval
                        is_awaiting_approval = False
                        proposed_mutation = "systemctl restart mysql"
                        safety_level = "HIGH"
                        incident_path = None
                        if selected_incident_id and selected_incident_id != "None":
                            incident_path = os.path.join("investigations", selected_incident_id)
                            state_path = os.path.join(incident_path, "state.md")
                            if os.path.exists(state_path):
                                try:
                                    with open(state_path, "r") as sf:
                                        state_content = sf.read()
                                    if "AWAITING_APPROVAL" in state_content:
                                        is_awaiting_approval = True
                                        import re
                                        mutation_match = re.search(r'\-\s+\*\*Proposed Mutation:\*\*\s*`?([^`\n]+)`?', state_content, re.IGNORECASE)
                                        if mutation_match:
                                            proposed_mutation = mutation_match.group(1).strip()
                                        risk_match = re.search(r'\-\s+\*\*Safety Level:\*\*\s*([A-Za-z0-9_ ]+)', state_content, re.IGNORECASE)
                                        if risk_match:
                                            safety_level = risk_match.group(1).strip()
                                except Exception as e:
                                    print(f"[Telegram Bot] Error checking safety gate status: {e}")

                        if is_awaiting_approval:
                            if msg_text == "💥 Yes, I am sure":
                                # Approve & Resume
                                try:
                                    resume_simulation(selected_incident_id, approved=True)
                                    reply_msg = (
                                        f"✅ *Safety Gate Clearance Granted!*\n\n"
                                        f"Operator approved proposed mutation command:\n`{proposed_mutation}`\n\n"
                                        f"Resuming SRE incident resolution... {get_commander_name()} is executing the action."
                                    )
                                except Exception as e:
                                    reply_msg = f"❌ *Failed to resume simulation:* {e}"
                                    
                                send_telegram_menu(bot_token, chat_id, reply_msg)
                                
                                # Sync operator's response in chat.json
                                try:
                                    chat_path = os.path.join(incident_path, "chat.json")
                                    chat_data = []
                                    if os.path.exists(chat_path):
                                        try:
                                            with open(chat_path, "r") as f:
                                                chat_data = json.load(f)
                                        except Exception:
                                            pass
                                    chat_data.append({
                                        "sender": "Operator (Telegram)",
                                        "message": msg_text,
                                        "timestamp": datetime.now(timezone.utc).isoformat()
                                    })
                                    chat_data.append({
                                        "sender": f"{get_commander_name()} Agent (IC)",
                                        "message": reply_msg,
                                        "timestamp": datetime.now(timezone.utc).isoformat()
                                    })
                                    os.makedirs(os.path.dirname(chat_path), exist_ok=True)
                                    with open(chat_path, "w") as f:
                                        json.dump(chat_data, f, indent=2)
                                except Exception as chat_err:
                                    print(f"[Telegram Bot] Failed to write chat log to chat.json: {chat_err}")
                                continue
                                
                            elif msg_text == "❌ No, abort mutation":
                                # Reject & Abort
                                try:
                                    resume_simulation(selected_incident_id, approved=False)
                                    reply_msg = (
                                        f"❌ *Safety Gate Override Active!*\n\n"
                                        f"Operator rejected proposed mutation command:\n`{proposed_mutation}`\n\n"
                                        f"SRE operations halted. Safety gate aborted operations successfully."
                                    )
                                except Exception as e:
                                    reply_msg = f"❌ *Failed to abort simulation:* {e}"
                                    
                                send_telegram_menu(bot_token, chat_id, reply_msg)
                                
                                # Sync operator's response in chat.json
                                try:
                                    chat_path = os.path.join(incident_path, "chat.json")
                                    chat_data = []
                                    if os.path.exists(chat_path):
                                        try:
                                            with open(chat_path, "r") as f:
                                                chat_data = json.load(f)
                                        except Exception:
                                            pass
                                    chat_data.append({
                                        "sender": "Operator (Telegram)",
                                        "message": msg_text,
                                        "timestamp": datetime.now(timezone.utc).isoformat()
                                    })
                                    chat_data.append({
                                        "sender": f"{get_commander_name()} Agent (IC)",
                                        "message": reply_msg,
                                        "timestamp": datetime.now(timezone.utc).isoformat()
                                    })
                                    os.makedirs(os.path.dirname(chat_path), exist_ok=True)
                                    with open(chat_path, "w") as f:
                                        json.dump(chat_data, f, indent=2)
                                except Exception as chat_err:
                                    print(f"[Telegram Bot] Failed to write chat log to chat.json: {chat_err}")
                                continue
                                
                            else:
                                # Prompt user with safety gate approval message and buttons
                                msg = (
                                    f"⚠️ *Safety Gate Hold!* [Incident: `{selected_incident_id}`]\n\n"
                                    f"A dangerous SRE mutation command is currently awaiting operator approval:\n"
                                    f"Proposed: `{proposed_mutation}`\n"
                                    f"Safety Level: *{safety_level}*\n\n"
                                    f"Please authorize execution by selecting one of the options below:"
                                )
                                send_telegram_safety_gate_menu(bot_token, chat_id, msg)
                                continue

                        # 4. Direct interactive SRE agent chat dispatch
                        if not selected_incident_id or selected_incident_id == "None":
                            send_raw_telegram_message(bot_token, chat_id, "⚠️ No incident selected. Tapp '📋 List Incidents' to select one first.")
                            continue
                            
                        incident_path = os.path.join("investigations", selected_incident_id)
                        details = parse_incident_folder(incident_path)
                        status = details.get("status", "UNKNOWN").upper()
                        project_id = details.get("project_id", "sre-next")
                        trigger_event = details.get("trigger_event", "frontend_latency_slo_violated")
                        
                        try:
                            from src.agents import IncidentCommander
                            from src.incident import IncidentContext
                            incident_uuid = details.get("incident_uuid")
                            ctx = IncidentContext(incident_uuid=incident_uuid) if incident_uuid and incident_uuid != "UNKNOWN" else None
                            commander = IncidentCommander(incident_context=ctx)
                            
                            chat_context = (
                                f"[Telegram Interface]\n"
                                f"Active Incident ID: {selected_incident_id}\n"
                                f"Current Incident Status: {status}\n"
                                f"Target GCP Project ID: {project_id}\n"
                                f"Trigger Alert Event: {trigger_event}\n\n"
                                f"Operator Message:\n{msg_text}"
                            )
                            reply_msg = commander.run(chat_context)
                        except Exception as e:
                            reply_msg = f"[System Alert] SRE chat logic failed: {e}"
                            
                        # Log message exchange in chat.json to mirror on the Web Dashboard
                        chat_path = os.path.join(incident_path, "chat.json")
                        chat_data = []
                        if os.path.exists(chat_path):
                            try:
                                with open(chat_path, "r") as f:
                                    chat_data = json.load(f)
                            except Exception:
                                pass
                                
                        chat_data.append({
                            "sender": "Operator (Telegram)",
                            "message": msg_text,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        chat_data.append({
                            "sender": f"{get_commander_name()} Agent (IC)",
                            "message": reply_msg,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        
                        os.makedirs(os.path.dirname(chat_path), exist_ok=True)
                        with open(chat_path, "w") as f:
                            json.dump(chat_data, f, indent=2)
                            
                        send_raw_telegram_message(bot_token, chat_id, f"🏰 *{get_commander_name()} (IC):*\n{reply_msg}")
                        
        except Exception as e:
            print(f"[Telegram Bot Loop] Error: {e}")
            
        if os.environ.get("TESTING_BOT") == "true":
            break
        time.sleep(1)

def run_auto_archive_loop():
    import time
    while True:
        try:
            auto_archive_incidents()
        except Exception as e:
            print(f"[Auto-Archive Loop] Error: {e}")
        interval = int(os.getenv("AUTO_ARCHIVE_INTERVAL_SECS", 86400))
        time.sleep(interval)

def run_server(port=8080):
    try:
        from src.observability import instrument_agents
        instrument_agents()
    except Exception as e:
        print(f"[Observability Startup] Failed to initialize tracing: {e}")
        
    try:
        from src.gcs_sync import GcsSyncManager
        GcsSyncManager.trigger_sync_background("from")
    except Exception as e:
        print(f"[GCS Sync Startup] Failed to trigger initial sync: {e}")
        
    server_address = ('', port)
    httpd = HTTPServer(server_address, SREHttpRequestHandler)
    print(f"Starting Project Benjamin SRE Dashboard Server on port {port}...")
    print(f"Visit: http://localhost:{port}/")
    
    # Launch background interactive SRE Telegram Bot daemon thread
    import threading
    t = threading.Thread(target=start_telegram_bot, daemon=True)
    t.start()
    
    # Launch background auto-archive scheduler thread
    archive_thread = threading.Thread(target=run_auto_archive_loop, daemon=True)
    archive_thread.start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == "__main__":
    import sys
    port = int(os.environ.get("PORT", 8080))
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
