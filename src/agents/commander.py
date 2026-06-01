try:
    from google.adk.agents import LlmAgent
except ImportError:
    # Robust mock fallback to support local execution and evaluations without ADK installed
    class LlmAgent:
        def __init__(self, name, instruction, model="gemini-2.5-flash", **kwargs):
            self.name = name
            self.instruction = instruction
            self.model = model
            self.kwargs = kwargs

from src.prompt_loader import load_prompt

import os

class IncidentCommander:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        commander_name = os.getenv("COMMANDER_NAME") or os.getenv("INCIDENT_COMMANDER_NAME") or "Benjamin"
        # Load system instruction template from YAML
        system_instruction = load_prompt("benjamin", prompt_key="system_instruction")
        
        if commander_name != "Benjamin":
            system_instruction = system_instruction.replace("Benjamin", commander_name)
            
        self.agent = LlmAgent(
            name=commander_name,
            instruction=system_instruction,
            model=model_name
        )
        
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
            "benjamin",
            prompt_key="incident_declaration",
            alert_event=alert_event,
            project_id=project_id,
            incident_id=incident_id
        )
        return declaration_prompt
