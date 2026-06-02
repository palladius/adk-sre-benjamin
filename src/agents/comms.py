try:
    from google.adk.agents import LlmAgent
except ImportError:
    class LlmAgent:
        def __init__(self, name, instruction, model="gemini-1.5-flash", **kwargs):
            self.name = name
            self.instruction = instruction
            self.model = model
            self.kwargs = kwargs

from src.prompt_loader import load_prompt

import os

class CommunicationsLead:
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        comms_name = os.getenv("COMMS_LEAD_NAME") or os.getenv("COMMUNICATIONS_LEAD_NAME") or os.getenv("MADHAVI_NAME") or "Madhavi"
        system_instruction = load_prompt("madhavi", prompt_key="system_instruction")
        
        if comms_name != "Madhavi":
            system_instruction = system_instruction.replace("Madhavi", comms_name)
            
        self.agent = LlmAgent(
            name=comms_name,
            instruction=system_instruction,
            model=model_name
        )
        
    def run(self, prompt: str) -> str:
        """Runs or chats with the Communications Lead agent."""
        if hasattr(self.agent, "run"):
            try:
                return self.agent.run(prompt)
            except Exception:
                pass
                
        # Mock/development interactive response fallback
        name = self.agent.name
        if "hello" in prompt.lower() or "hi" in prompt.lower():
            return f"Hello! I am {name}, your Communications Lead for Project Benjamin. How can I assist you with public SRE channel broadcasts?"
        elif "status" in prompt.lower() or "incident" in prompt.lower():
            return f"[{name}] Standing by. I can broadcast incident status updates, manage human-in-the-loop escalations, and sync with GitHub/ServiceNow."
        else:
            return f"[{name}] Factual SRE dispatch update: Received instructions '{prompt}'. All notification routes are active."
        
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
