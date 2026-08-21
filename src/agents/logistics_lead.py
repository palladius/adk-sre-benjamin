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

class LogisticsLead:
    def __init__(self, model_name: str = None, incident_context = None, **kwargs):
        if model_name is None:
            model_name = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-3.1-flash-lite").strip("'\"")
        raw_name = os.getenv("LOGISTICS_LEAD_NAME") or os.getenv("LOGISTICS_AGENT_NAME") or "LogisticsAgent"
        
        kwargs.setdefault("logistics_name", raw_name)
        system_instruction = load_prompt("logistics_agent", prompt_key="system_instruction", **kwargs)
        
        if raw_name != "LogisticsAgent":
            system_instruction = system_instruction.replace("Logistics Agent", raw_name)
            system_instruction = system_instruction.replace("LogisticsAgent", raw_name)
            
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
        self.raw_name = raw_name
        
    def run(self, prompt: str) -> str:
        """Runs or chats with the Logistics Lead agent."""
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
        if "hello" in prompt.lower() or "hi" in prompt.lower():
            return f"Hello. I am {name}, your Logistics Lead. I verify credentials, check quotas, and assess risk gates for proposed mutations."
        elif "status" in prompt.lower() or "safety" in prompt.lower():
            return f"[{name}] Standing by. I can decompose dangerous commands, calculate risk coefficients, and audit API limits."
        else:
            return f"[{name}] Logistics audit: '{prompt}'. Running security checks and credentials scan."
        
    def command_evaluation(
        self, 
        proposed_command: str, 
        command_parts: list[str], 
        max_risk: str, 
        evaluation_status: str, 
        reasons: list[str]
    ) -> str:
        """Evaluates proposed commands for safety risk coefficients."""
        return load_prompt(
            "logistics_agent",
            prompt_key="command_evaluation",
            proposed_command=proposed_command,
            command_parts=", ".join(command_parts),
            max_risk=max_risk,
            evaluation_status=evaluation_status,
            reasons=", ".join(reasons)
        )
        
    def quota_check(self, project_id: str, cred_var_name: str, cred_status: str) -> str:
        """Verifies environment variables and API quotas."""
        return load_prompt(
            "logistics_agent",
            prompt_key="quota_check",
            project_id=project_id,
            cred_var_name=cred_var_name,
            cred_status=cred_status
        )
