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

class OperationsLead:
    def __init__(self, model_name: str = "gemini-2.5-flash", loaded_skills: list[dict] = None):
        system_instruction = load_prompt("ops_agent", prompt_key="system_instruction")
        
        if loaded_skills:
            for skill in loaded_skills:
                system_instruction += f"\n\n### LOADED SRE SKILL: {skill['name']}\n{skill['instructions']}"
        
        self.agent = LlmAgent(
            name="OpsAgent",
            instruction=system_instruction,
            model=model_name
        )
        
    def triage_metric(self, metric_name: str, value: float, threshold: float) -> str:
        """Triggers dynamic metric polling diagnostics."""
        return load_prompt(
            "ops_agent",
            prompt_key="diagnostic_triage",
            metric_name=metric_name,
            value=value,
            threshold=threshold
        )
        
    def propose_mutation(self, command: str, asset: str, expected_outcome: str) -> str:
        """Proposes a system mutation command to the safety gates."""
        return load_prompt(
            "ops_agent",
            prompt_key="propose_mutation",
            command=command,
            asset=asset,
            expected_outcome=expected_outcome
        )
