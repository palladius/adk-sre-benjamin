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
    status = "UNKNOWN"
    project_id = "UNKNOWN"
    trigger_event = "UNKNOWN"
    timeline = []
    artifacts = []
    
    # 1. Parse state.md
    if os.path.exists(state_path):
        try:
            with open(state_path, "r") as f:
                state_content = f.read()
                
            status_match = re.search(r'\-\s+\*\*Status:\*\*\s*([A-Za-z0-9_]+)', state_content, re.IGNORECASE)
            if status_match:
                status = status_match.group(1).strip()
                
            project_match = re.search(r'\-\s+\*\*Target Project:\*\*\s*`?([^`\n]+)`?', state_content, re.IGNORECASE)
            if project_match:
                project_id = project_match.group(1).strip()
                
            trigger_match = re.search(r'\-\s+\*\*Trigger Event:\*\*\s*`?([^`\n]+)`?', state_content, re.IGNORECASE)
            if trigger_match:
                trigger_event = trigger_match.group(1).strip()
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
            
    return {
        "incident_id": incident_id,
        "status": status,
        "project_id": project_id,
        "trigger_event": trigger_event,
        "timeline": timeline,
        "artifacts": artifacts,
        "folder_path": folder_path
    }

class SREHttpRequestHandler(BaseHTTPRequestHandler):
    
    def end_headers(self):
        # Enable CORS for local testing/dashboard consumption
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
        
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        # API: Get Server Configuration
        if path == "/api/config":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("PROJECT_ID") or "prod-db-999"
            self.wfile.write(json.dumps({"project_id": project_id}).encode("utf-8"))
            return
            
        # API: Discover GCP Resources for a Project
        elif path.startswith("/api/projects/") and path.endswith("/discover"):
            try:
                project_id = path.split("/")[3]
                cache_dir = os.path.join("discover", "gcp-project")
                json_path = os.path.join(cache_dir, f"{project_id}.json")
                
                # Check cache: if it exists, read it
                if os.path.exists(json_path):
                    with open(json_path, "r") as f:
                        resources = json.load(f)
                else:
                    # Run the crawler
                    from src.discovery import discover_project_resources
                    discover_project_resources(project_id)
                    with open(json_path, "r") as f:
                        resources = json.load(f)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                
                response_data = {
                    "project_id": project_id,
                    "resources": resources,
                    "cache_path": json_path,
                    "wiki_path": os.path.join(cache_dir, f"{project_id}.md")
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
                cache_dir = os.path.join("discover", "gcp-project")
                md_path = os.path.join(cache_dir, f"{project_id}.md")
                
                os.makedirs(cache_dir, exist_ok=True)
                if not os.path.exists(md_path):
                    # Check if json cache exists to regenerate or bootstrap it
                    json_path = os.path.join(cache_dir, f"{project_id}.json")
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
                cache_dir = os.path.join("discover", "gcp-project")
                dot_path = os.path.join(cache_dir, f"{project_id}.dot")
                
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
            
            incidents_dir = "investigations"
            incidents = []
            if os.path.exists(incidents_dir):
                for item in sorted(os.listdir(incidents_dir), reverse=True):
                    item_path = os.path.join(incidents_dir, item)
                    if os.path.isdir(item_path) and item.startswith("INC-"):
                        incidents.append(parse_incident_folder(item_path))
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
                                "sender": "Benjamin Agent (IC)",
                                "message": f"Welcome to the tactical Incident Chat for {incident_id}. I am Benjamin, the SRE Incident Commander. We are currently analyzing the incident alert '{details.get('trigger_event')}' targeting project '{details.get('project_id')}'. How can I assist you?",
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
                    
    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        # 4. API: Trigger Incident Simulation
        if path == "/api/simulate":
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
                            "sender": "Benjamin Agent (IC)",
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
                                f"Resuming incident resolution... Benjamin is executing the action."
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
                            "sender": "Benjamin Agent (IC)",
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
                
                cache_dir = os.path.join("discover", "gcp-project")
                os.makedirs(cache_dir, exist_ok=True)
                md_path = os.path.join(cache_dir, f"{project_id}.md")
                with open(md_path, "w") as f:
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

        # API: Save Custom Graphviz DOT for a Project
        elif path.startswith("/api/projects/") and path.endswith("/graph"):
            try:
                project_id = path.split("/")[3]
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                payload = json.loads(post_data.decode("utf-8"))
                content = payload.get("content", "")
                
                cache_dir = os.path.join("discover", "gcp-project")
                os.makedirs(cache_dir, exist_ok=True)
                dot_path = os.path.join(cache_dir, f"{project_id}.dot")
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
                                "sender": "Benjamin Agent (IC)",
                                "message": (
                                    f"Welcome to the tactical Incident Chat for {incident_id}. "
                                    f"I am Benjamin, the SRE Incident Commander. We are currently analyzing the alert "
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
                        commander = IncidentCommander()
                        
                        # Supply full screen operational context dynamically to the model
                        chat_context = (
                            f"[Operational Context]\n"
                            f"Selected Incident ID: {incident_id}\n"
                            f"Current Incident Status: {status}\n"
                            f"Target GCP Project ID: {project_id}\n"
                            f"Trigger Alert Event: {trigger_event}\n\n"
                            f"Operator Prompt:\n{user_msg}"
                        )
                        reply_msg = commander.run(chat_context)
                    except Exception as e:
                        reply_msg = f"[System Alert] Incident Commander failed: {e}"
                    
                    chat_data.append({
                        "sender": "Benjamin Agent (IC)",
                        "message": reply_msg,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
                    # Push Benjamin Agent reply directly to Telegram if configured
                    if bot_token and chat_id:
                        if "ENTER_BOT" not in bot_token and "ENTER_CHAT" not in chat_id:
                            try:
                                send_raw_telegram_message(bot_token, chat_id, f"🏰 *Benjamin (IC):*\n{reply_msg}")
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
                incidents.append({
                    "id": folder,
                    "status": details.get("status", "UNKNOWN"),
                    "project_id": details.get("project_id", "UNKNOWN"),
                    "trigger_event": details.get("trigger_event", "UNKNOWN")
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
                [{"text": "☁️ Target Project"}, {"text": "🆔 Select Incident"}]
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
            time.sleep(5)
            continue
            
        # Select latest active incident if none selected
        if not selected_incident_id:
            incidents = get_incidents_list()
            if incidents:
                selected_incident_id = incidents[-1]["id"]
                
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getUpdates?offset={last_update_id + 1}&timeout=5"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    updates = data.get("result", [])
                    for update in updates:
                        last_update_id = max(last_update_id, update.get("update_id", 0))
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
                        lower_text = msg_text.lower()
                        if lower_text.startswith("/start") or lower_text == "/help" or lower_text == "help":
                            welcome_msg = (
                                "🏰 *Project Benjamin SRE Command Hub*\n\n"
                                f"• *Active Incident Context:* `{selected_incident_id}`\n"
                                f"• *Target GCP Project ID:* `{os.getenv('PROJECT_ID', 'sre-next')}`\n\n"
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
                            
                        elif msg_text == "📋 List Incidents":
                            inc_list = get_incidents_list()
                            if not inc_list:
                                send_raw_telegram_message(bot_token, chat_id, "📋 No SRE incidents recorded in repository.")
                                continue
                            list_msg = "📋 *Historical SRE Incidents:*\n\n"
                            for idx, inc in enumerate(inc_list, 1):
                                list_msg += f"{idx}. `{inc['id']}` ({inc['status']}) | Project: `{inc['project_id']}`\n"
                            list_msg += "\n💡 *Reply `/select <Incident_ID>` to switch incident context.*"
                            send_raw_telegram_message(bot_token, chat_id, list_msg)
                            continue
                            
                        elif msg_text == "☁️ Target Project":
                            curr_proj = os.getenv("PROJECT_ID", "sre-next")
                            send_raw_telegram_message(
                                bot_token, chat_id,
                                f"☁️ *Active GCP Project context:* `{curr_proj}`\n\n"
                                f"💡 *To change this project, reply:* `/setproject <Project_ID>`"
                            )
                            continue
                            
                        elif msg_text == "🆔 Select Incident":
                            send_raw_telegram_message(
                                bot_token, chat_id,
                                "🆔 *Switch Incident Context*\n\n"
                                "Please reply with this format:\n`/select <Incident_ID>`\n\n"
                                "Example: `/select INC-PLAYGROUND`"
                            )
                            continue
                            
                        elif msg_text.startswith("/select"):
                            parts = msg_text.split(" ", 1)
                            if len(parts) < 2:
                                send_raw_telegram_message(bot_token, chat_id, "❌ Usage: `/select <Incident_ID>`")
                                continue
                            target_inc = parts[1].strip()
                            target_inc_path = os.path.join("investigations", target_inc)
                            if os.path.exists(target_inc_path):
                                selected_incident_id = target_inc
                                details = parse_incident_folder(target_inc_path)
                                status_val = details.get('status', 'UNKNOWN')
                                
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
                            
                        elif msg_text.startswith("/setproject"):
                            parts = msg_text.split(" ", 1)
                            if len(parts) < 2:
                                send_raw_telegram_message(bot_token, chat_id, "❌ Usage: `/setproject <Project_ID>`")
                                continue
                            target_proj = parts[1].strip()
                            
                            # Update .env
                            env_path = ".env"
                            if os.path.exists(env_path):
                                with open(env_path, "r") as f:
                                    content = f.read()
                                import re
                                if "PROJECT_ID=" in content:
                                    content = re.sub(r"PROJECT_ID=.*", f"PROJECT_ID='{target_proj}'", content)
                                else:
                                    content += f"\nPROJECT_ID='{target_proj}'\n"
                                with open(env_path, "w") as f:
                                    f.write(content.strip() + "\n")
                                    
                            os.environ["PROJECT_ID"] = target_proj
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
                                        f"Resuming SRE incident resolution... Benjamin is executing the action."
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
                                        "sender": "Benjamin Agent (IC)",
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
                                        "sender": "Benjamin Agent (IC)",
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
                            commander = IncidentCommander()
                            
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
                            "sender": "Benjamin Agent (IC)",
                            "message": reply_msg,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        
                        os.makedirs(os.path.dirname(chat_path), exist_ok=True)
                        with open(chat_path, "w") as f:
                            json.dump(chat_data, f, indent=2)
                            
                        send_raw_telegram_message(bot_token, chat_id, f"🏰 *Benjamin (IC):*\n{reply_msg}")
                        
        except Exception as e:
            print(f"[Telegram Bot Loop] Error: {e}")
            
        time.sleep(1)

def run_server(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, SREHttpRequestHandler)
    print(f"Starting Project Benjamin SRE Dashboard Server on port {port}...")
    print(f"Visit: http://localhost:{port}/")
    
    # Launch background interactive SRE Telegram Bot daemon thread
    import threading
    t = threading.Thread(target=start_telegram_bot, daemon=True)
    t.start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == "__main__":
    import sys
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
