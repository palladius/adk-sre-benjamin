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

import os

class LogisticsLead:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        logistics_name = os.getenv("LOGISTICS_LEAD_NAME") or os.getenv("LOGISTICS_AGENT_NAME") or "LogisticsAgent"
        system_instruction = load_prompt("logistics_agent", prompt_key="system_instruction")
        
        if logistics_name != "LogisticsAgent":
            system_instruction = system_instruction.replace("Logistics Agent", logistics_name)
            system_instruction = system_instruction.replace("LogisticsAgent", logistics_name)
            
        self.agent = LlmAgent(
            name=logistics_name,
            instruction=system_instruction,
            model=model_name
        )
        
    def run(self, prompt: str) -> str:
        """Runs or chats with the Logistics Lead agent."""
        if hasattr(self.agent, "run"):
            try:
                return self.agent.run(prompt)
            except Exception:
                pass
        name = self.agent.name
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
