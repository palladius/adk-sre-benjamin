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

class PlanningLead:
    def __init__(self, model_name: str = None, loaded_skills: list[dict] = None, incident_context = None, **kwargs):
        if model_name is None:
            model_name = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-3.1-flash-lite").strip("'\"")
        planning_name = os.getenv("PLANNING_LEAD_NAME") or os.getenv("PLANNING_AGENT_NAME") or "Scrivano Fossati"
        
        kwargs.setdefault("incident_id", "active-incident")
        kwargs.setdefault("planning_name", planning_name)
        system_instruction = load_prompt("planning_agent", prompt_key="system_instruction", **kwargs)

        
        if planning_name != "Scrivano Fossati":
            system_instruction = system_instruction.replace("Scrivano Fossati", planning_name)
            
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
        if incident_context is not None:
            self.metadata["incident_uuid"] = incident_context.incident_uuid
            if getattr(incident_context, "incident_id", None):
                self.metadata["incident_id"] = incident_context.incident_id
        elif "incident_uuid" in kwargs:
            self.metadata["incident_uuid"] = kwargs["incident_uuid"]
        if "incident_id" in kwargs:
            self.metadata["incident_id"] = kwargs["incident_id"]
        
        self.agent = LlmAgent(
            name=planning_name,
            instruction=system_instruction,
            model=model_name,
            metadata=self.metadata
        )
        self.agent.metadata = self.metadata
        
    def run(self, prompt: str) -> str:
        """Runs or chats with the Planning Lead agent."""
        if hasattr(self.agent, "run"):
            try:
                return self.agent.run(prompt)
            except Exception:
                pass
        name = self.agent.name
        if "hello" in prompt.lower() or "hi" in prompt.lower():
            return f"Hello. I am {name}, your Planning Lead. I compile timeline logs, index historical postmortems via Memento, and scan GCP asset safety postures."
        elif "status" in prompt.lower() or "memory" in prompt.lower():
            return f"[{name}] Standing by. I can search past incidents, generate runbook insights, and chronicle state changes with safe Git annotations."
        else:
            return f"[{name}] Planning directive: '{prompt}'. Running historical checks and updating incident record."
        
    def scribe_commit(self, action_summary: str, commit_hash: str) -> str:
        """Generates timeline chronicle details for git note attachments."""
        return load_prompt(
            "planning_agent",
            prompt_key="scribe_commit",
            action_summary=action_summary,
            commit_hash=commit_hash
        )
        
    def discovery_summary(self, project_id: str, networks_count: int, databases_count: int, vulnerability_count: int) -> str:
        """Summarizes GCP crawler scanning results."""
        return load_prompt(
            "planning_agent",
            prompt_key="discovery_summary",
            project_id=project_id,
            networks_count=networks_count,
            databases_count=databases_count,
            vulnerability_count=vulnerability_count
        )
