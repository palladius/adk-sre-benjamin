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

class LogisticsLead:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        system_instruction = load_prompt("logistics_agent", prompt_key="system_instruction")
        
        self.agent = LlmAgent(
            name="LogisticsAgent",
            instruction=system_instruction,
            model=model_name
        )
        
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
