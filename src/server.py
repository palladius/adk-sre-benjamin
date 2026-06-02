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
                        chat_data = [
                            {
                                "sender": "Benjamin Agent (IC)",
                                "message": f"Welcome to the tactical Incident Chat for {incident_id}. I am Benjamin, the SRE Incident Commander. We are currently analyzing the incident alert '{details.get('trigger_event')}' targeting project '{details.get('project_id')}'. How can I assist you?",
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        ]
                    
                    # Append user message
                    chat_data.append({
                        "sender": "Operator (You)",
                        "message": user_msg,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
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

def run_server(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, SREHttpRequestHandler)
    print(f"Starting Project Benjamin SRE Dashboard Server on port {port}...")
    print(f"Visit: http://localhost:{port}/")
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
