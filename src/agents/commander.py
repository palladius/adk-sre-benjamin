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

class IncidentCommander:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        # Load system instruction template from YAML
        system_instruction = load_prompt("benjamin", prompt_key="system_instruction")
        
        self.agent = LlmAgent(
            name="Benjamin",
            instruction=system_instruction,
            model=model_name
        )
        
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
