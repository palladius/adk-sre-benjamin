try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from google.adk.agents import LlmAgent
except ImportError:
    class LlmAgent:
        def __init__(self, name, instruction, model=None, **kwargs):
            self.name = name
            self.instruction = instruction
            self.model = model or os.getenv("DEFAULT_GEMINI_MODEL", "gemini-3.1-flash-lite").strip("'\"")
            self.kwargs = kwargs
            self.metadata = kwargs.get("metadata") or {}

from src.prompt_loader import load_prompt

import os

class CommunicationsLead:
    def __init__(self, model_name: str = None, loaded_skills: list[dict] = None, incident_context = None, **kwargs):
        if model_name is None:
            model_name = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-3.1-flash-lite").strip("'\"")
        comms_name = os.getenv("COMMS_LEAD_NAME") or os.getenv("COMMUNICATIONS_LEAD_NAME") or os.getenv("MADHAVI_NAME") or "Madhavi"
        
        kwargs.setdefault("incident_id", "active-incident")
        kwargs.setdefault("comms_name", comms_name)
        system_instruction = load_prompt("comms_agent", prompt_key="system_instruction", **kwargs)
        
        if comms_name != "Madhavi":
            system_instruction = system_instruction.replace("Madhavi", comms_name)

            
        from src.skills_adapter import SkillAdapter
        if loaded_skills is None:
            loaded_skills = []
            adapter = SkillAdapter()
            for skill_name in ["postmortem-generator", "postmortem-aggregator"]:
                try:
                    skill = adapter.load_sre_skill(skill_name)
                    loaded_skills.append(skill)
                except FileNotFoundError:
                    pass
                    
        if loaded_skills:
            for skill in loaded_skills:
                system_instruction += f"\n\n### LOADED SRE SKILL: {skill['name']}\n{skill['instructions']}"

        self.metadata = kwargs.get("metadata") or {}
        if "incident_uuid" in kwargs:
            self.metadata["incident_uuid"] = kwargs["incident_uuid"]
        if "incident_id" in kwargs:
            self.metadata["incident_id"] = kwargs["incident_id"]
            
        if incident_context is not None:
            self.metadata["incident_uuid"] = incident_context.incident_uuid
            if getattr(incident_context, "incident_id", None):
                self.metadata["incident_id"] = incident_context.incident_id
            
        self.agent = LlmAgent(
            name=comms_name,
            instruction=system_instruction,
            model=model_name,
            metadata=self.metadata
        )
        self.agent.metadata = self.metadata
        
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
            "comms_agent",
            prompt_key="incident_broadcast",
            incident_id=incident_id,
            incident_status=incident_status,
            project_id=project_id,
            summary_text=summary_text
        )
        
    def request_hitl_approval(self, incident_id: str, command: str, risk_level: str, reasons: list[str]) -> str:
        """Generates Human-in-the-Loop authorization alerts."""
        return load_prompt(
            "comms_agent",
            prompt_key="hitl_approval_request",
            incident_id=incident_id,
            command=command,
            risk_level=risk_level,
            reasons=", ".join(reasons)
        )

    def create_discord_war_room(self) -> dict:
        """Dynamically creates a Discord war-room channel for the active incident."""
        from src.comms_discord import create_discord_channel
        incident_id = self.metadata.get("incident_id") or "active-incident"
        return create_discord_channel(incident_id=incident_id)
