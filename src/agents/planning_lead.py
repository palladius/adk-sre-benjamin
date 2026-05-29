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

class PlanningLead:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        system_instruction = load_prompt("planning_agent", prompt_key="system_instruction")
        
        self.agent = LlmAgent(
            name="PlanningAgent",
            instruction=system_instruction,
            model=model_name
        )
        
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
