try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os
from src.agents.utils import sanitize_agent_name
from src.prompt_loader import load_prompt

try:
    from google.adk.agents import LlmAgent
except ImportError:
    class LlmAgent:
        def __init__(self, name, instruction, model=None, **kwargs):
            self.name = name
            self.instruction = instruction
            self.model = model or os.getenv("DEFAULT_GEMINI_MODEL", "gemini-3.1-flash-lite").strip("'\"")

class IncidentCommander:
    def __init__(self, model_name: str = None, incident_context = None, **kwargs):
        if model_name is None:
            model_name = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-3.1-flash-lite").strip("'\"")
        raw_name = os.getenv("COMMANDER_NAME") or os.getenv("INCIDENT_COMMANDER_NAME") or "Benjamin"
        
        kwargs.setdefault("commander_name", raw_name)
        kwargs.setdefault("name", raw_name)
        system_instruction = load_prompt("incident_commander", prompt_key="system_instruction", **kwargs)
        
        if raw_name != "Benjamin":
            system_instruction = system_instruction.replace("Benjamin", raw_name)
            
        self.metadata = kwargs.get("metadata") or {}
        if incident_context is not None:
            self.metadata["incident_uuid"] = incident_context.incident_uuid
            if getattr(incident_context, "incident_id", None):
                self.metadata["incident_id"] = incident_context.incident_id
        elif "incident_uuid" in kwargs:
            self.metadata["incident_uuid"] = kwargs["incident_uuid"]
        if "incident_id" in kwargs:
            self.metadata["incident_id"] = kwargs["incident_id"]
            
        safe_name = sanitize_agent_name(raw_name)
        self.agent = LlmAgent(
            name=safe_name,
            instruction=system_instruction,
            model=model_name
        )
        object.__setattr__(self.agent, "metadata", self.metadata)
        self.raw_name = raw_name
        
    def run(self, prompt: str) -> str:
        """Runs or chats with the Incident Commander."""
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key or os.getenv("SRE_MODE") == "LIVE":
            try:
                import asyncio
                from google.adk.runners import InMemoryRunner
                from google.adk.sessions import InMemorySessionService
                from google.genai import types

                async def _execute():
                    session_service = InMemorySessionService()
                    await session_service.create_session(app_name="sre_benjamin", user_id="sre_operator", session_id="s1")
                    runner = InMemoryRunner(agent=self.agent, app_name="sre_benjamin", session_service=session_service)
                    res_text = ""
                    async for event in runner.run_async(
                        user_id="sre_operator",
                        session_id="s1",
                        new_message=types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
                    ):
                        if event.is_final_response() and event.content and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, "text") and part.text:
                                    res_text += part.text
                    return res_text.strip()

                result = asyncio.run(_execute())
                if result:
                    return result
            except Exception:
                pass
                
        name = self.raw_name
        safe_name = self.agent.name
        if "hello" in prompt.lower() or "hi" in prompt.lower():
            return f"Hello, SRE. I am Incident Commander {name} ({safe_name}). I coordinate all functional leads according to Google's strict IMAG ICS command hierarchy."
        elif "status" in prompt.lower() or "active" in prompt.lower():
            return f"[{name}] ({safe_name}) Standing by. I can declare SRE incidents active, configure the response context, and oversee mitigation."
        else:
            return f"[{name}] ({safe_name}) Operational command noted: '{prompt}'. Ready to guide SRE leads to resolution."

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
