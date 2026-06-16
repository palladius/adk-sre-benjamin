try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from google.adk.agents import LlmAgent
except ImportError:
    import urllib.request
    import urllib.parse
    import json
    import os

    # Dynamic fallback to support local execution with authentic Gemini API queries
    class LlmAgent:
        def __init__(self, name, instruction, model=None, **kwargs):
            self.name = name
            self.instruction = instruction
            self.model = model or os.getenv("DEFAULT_GEMINI_MODEL", "gemini-3.1-flash-lite").strip("'\"")
            self.kwargs = kwargs
            self.metadata = kwargs.get("metadata") or {}
            
        def run(self, prompt: str) -> str:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                # Local development placeholder if API key is not present
                name = self.name
                if "hello" in prompt.lower() or "hi" in prompt.lower():
                    return f"Hello, SRE. I am Incident Commander {name}. I coordinate all functional leads according to Google's strict IMAG ICS command hierarchy. (Mock Mode: No GEMINI_API_KEY found)"
                elif "status" in prompt.lower() or "active" in prompt.lower():
                    return f"[{name}] Standing by. I can declare SRE incidents active, configure the response context, and oversee mitigation. (Mock Mode)"
                else:
                    return f"[{name}] Operational command noted: '{prompt}'. Ready to guide SRE leads to resolution. (Mock Mode)"
            
            # Map model names gracefully if needed (prefer DEFAULT_GEMINI_MODEL and avoid gemini-1.5-flash)
            model_target = (self.model or os.getenv("DEFAULT_GEMINI_MODEL", "gemini-3.1-flash-lite")).strip("'\"")
            if "1.5" in model_target or "2.5" in model_target:
                model_target = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-3.1-flash-lite").strip("'\"")
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_target}:generateContent?key={api_key}"
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "systemInstruction": {
                    "parts": [
                        {"text": self.instruction}
                    ]
                }
            }
            
            try:
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=20) as response:
                    if response.status == 200:
                        res_body = json.loads(response.read().decode("utf-8"))
                        text = res_body["candidates"][0]["content"]["parts"][0]["text"]
                        return text.strip()
                    else:
                        return f"[{self.name}] Failed Gemini call (HTTP {response.status})"
            except Exception as e:
                return f"[{self.name}] Error communicating with Gemini API: {e}"

from src.prompt_loader import load_prompt

import os

class IncidentCommander:
    def __init__(self, model_name: str = None, incident_context = None, **kwargs):
        if model_name is None:
            model_name = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-3.1-flash-lite").strip("'\"")
        commander_name = os.getenv("COMMANDER_NAME") or os.getenv("INCIDENT_COMMANDER_NAME") or "Benjamin"
        
        kwargs.setdefault("commander_name", commander_name)
        kwargs.setdefault("name", commander_name)
        # Load system instruction template from YAML
        system_instruction = load_prompt("incident_commander", prompt_key="system_instruction", **kwargs)
        
        if commander_name != "Benjamin":
            system_instruction = system_instruction.replace("Benjamin", commander_name)
            
        self.metadata = kwargs.get("metadata") or {}
        if incident_context is not None:
            self.metadata["incident_uuid"] = incident_context.incident_uuid
        elif "incident_uuid" in kwargs:
            self.metadata["incident_uuid"] = kwargs["incident_uuid"]
            
        self.agent = LlmAgent(
            name=commander_name,
            instruction=system_instruction,
            model=model_name,
            metadata=self.metadata
        )
        self.agent.metadata = self.metadata
        
    def run(self, prompt: str) -> str:
        """Runs or chats with the Incident Commander."""
        if hasattr(self.agent, "run"):
            try:
                return self.agent.run(prompt)
            except Exception:
                pass
        name = self.agent.name
        if "hello" in prompt.lower() or "hi" in prompt.lower():
            return f"Hello, SRE. I am Incident Commander {name}. I coordinate all functional leads according to Google's strict IMAG ICS command hierarchy."
        elif "status" in prompt.lower() or "active" in prompt.lower():
            return f"[{name}] Standing by. I can declare SRE incidents active, configure the response context, and oversee mitigation."
        else:
            return f"[{name}] Operational command noted: '{prompt}'. Ready to guide SRE leads to resolution."
        
    def declare_incident(self, alert_event: str, project_id: str, incident_id: str) -> str:
        """Declares an incident active and formats the notification payload."""
        declaration_prompt = load_prompt(
            "incident_commander",
            prompt_key="incident_declaration",
            alert_event=alert_event,
            project_id=project_id,
            incident_id=incident_id
        )
        return declaration_prompt
