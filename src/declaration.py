import os
import json
import base64
import urllib.request
import re

def get_projects_list() -> list[str]:
    """Lightweight helper to retrieve project IDs from discover/gcp-project/."""
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

def parse_declaration_intent_heuristics(text: str) -> dict:
    """Fallback heuristics-based parser when MOCK_TOOLING is enabled or Gemini is offline."""
    lower_text = text.lower().strip()
    
    # Check if this text declares an incident
    declaration_keywords = [
        "declare incident", "create incident", "new incident", 
        "incident trigger", "slo violated", "incident declaration", 
        "/newincident"
    ]
    
    is_decl = False
    if any(kw in lower_text for kw in declaration_keywords):
        is_decl = True
    # If starting with slash command /newincident
    if lower_text.startswith("/newincident"):
        is_decl = True
        
    # Extract project ID if present in the text (exact match against discovered projects)
    projects = get_projects_list()
    matched_project = None
    for proj in projects:
        # Match as a word boundary
        if re.search(r'\b' + re.escape(proj.lower()) + r'\b', lower_text):
            matched_project = proj
            break
            
    # Infer event type
    event_type = "manual_alert"
    if "gke" in lower_text:
        event_type = "gke_cluster_down"
    elif "latency" in lower_text or "slo" in lower_text:
        event_type = "latency_high"
    elif "sql" in lower_text or "db" in lower_text:
        event_type = "sql_instance_down"
        
    # Clean description
    description = text
    # Strip slash command if present
    if description.lower().startswith("/newincident"):
        description = description[len("/newincident"):].strip()
        
    return {
        "is_incident_declaration": is_decl,
        "event_type": event_type,
        "project_id": matched_project,
        "description": description or "Manual incident declaration"
    }

def parse_declaration_intent(text: str) -> dict:
    """Parses SRE incident declaration intent using Gemini API or heuristics fallback."""
    mock_tooling = os.getenv("MOCK_TOOLING", "true").lower() == "true"
    api_key = os.getenv("GEMINI_API_KEY")
    
    if mock_tooling or not api_key:
        return parse_declaration_intent_heuristics(text)
        
    model_name = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-3.1-flash-lite").strip("'\"")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    prompt = f"""
Analyze the following SRE chat message. Determine if the operator is declaring or requesting to create a new incident (e.g. 'I'd like to create a new incident...', 'declare incident GKE cluster down').
Return a raw JSON object with these keys:
- 'is_incident_declaration': boolean (true if the user is declaring/requesting to create a new incident, false otherwise)
- 'event_type': string (inferred event type: e.g. 'gke_cluster_down', 'latency_high', 'sql_instance_down', or 'manual_alert' if not specified or unclear)
- 'project_id': string or null (the exact GCP project ID if it matches or is clearly identified, or null if it's missing, unclear, or fuzzy)
- 'description': string (a short summary of the incident description)

Do not wrap the response in markdown blocks or any other formatting. Output ONLY the raw JSON string.

User message to analyze:
"{text}"
"""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
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
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 200:
                res_body = json.loads(response.read().decode("utf-8"))
                text_response = res_body["candidates"][0]["content"]["parts"][0]["text"].strip()
                
                # Clean up markdown code block if returned
                if text_response.startswith("```"):
                    lines = text_response.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    text_response = "\n".join(lines).strip()
                    
                parsed = json.loads(text_response)
                # Ensure all required keys exist and types match
                return {
                    "is_incident_declaration": bool(parsed.get("is_incident_declaration", False)),
                    "event_type": str(parsed.get("event_type", "manual_alert")),
                    "project_id": parsed.get("project_id"),  # could be None/null
                    "description": str(parsed.get("description", text))
                }
    except Exception as e:
        print(f"[Declaration Parser] Live Gemini call failed, falling back to heuristics: {e}")
        
    return parse_declaration_intent_heuristics(text)
