try:
    from google.adk.agents import LlmAgent
except ImportError:
    class LlmAgent:
        def __init__(self, name, instruction, model="gemini-2.5-flash", **kwargs):
            self.name = name
            self.instruction = instruction
            self.model = model
            self.kwargs = kwargs

from src.prompt_loader import load_prompt

class CommunicationsLead:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        system_instruction = load_prompt("madhavi", prompt_key="system_instruction")
        
        self.agent = LlmAgent(
            name="Madhavi",
            instruction=system_instruction,
            model=model_name
        )
        
    def broadcast_incident(self, incident_id: str, incident_status: str, project_id: str, summary_text: str) -> str:
        """Broadcasts active incident reports to channels."""
        return load_prompt(
            "madhavi",
            prompt_key="incident_broadcast",
            incident_id=incident_id,
            incident_status=incident_status,
            project_id=project_id,
            summary_text=summary_text
        )
        
    def request_hitl_approval(self, incident_id: str, command: str, risk_level: str, reasons: list[str]) -> str:
        """Generates Human-in-the-Loop authorization alerts."""
        return load_prompt(
            "madhavi",
            prompt_key="hitl_approval_request",
            incident_id=incident_id,
            command=command,
            risk_level=risk_level,
            reasons=", ".join(reasons)
        )
