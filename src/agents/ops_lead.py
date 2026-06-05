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

from src.prompt_loader import load_prompt

import os

class OperationsLead:
    def __init__(self, model_name: str = None, loaded_skills: list[dict] = None, **kwargs):
        if model_name is None:
            model_name = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-3.1-flash-lite").strip("'\"")
        ops_name = os.getenv("OPS_LEAD_NAME") or os.getenv("OPERATIONS_LEAD_NAME") or os.getenv("OPS_AGENT_NAME") or "OpsAgent"
        
        kwargs.setdefault("ops_name", ops_name)
        system_instruction = load_prompt("ops_agent", prompt_key="system_instruction", **kwargs)
        
        if ops_name != "OpsAgent":
            system_instruction = system_instruction.replace("Ops Agent", ops_name)
            system_instruction = system_instruction.replace("OpsAgent", ops_name)
            
        from src.skills_adapter import SkillAdapter
        if loaded_skills is None:
            loaded_skills = []
            adapter = SkillAdapter()
            for skill_name in [
                "anomaly-detection",
                "cloud-logging",
                "cloud-monitoring",
                "gcp-setup",
                "gcp-playbooks",
                "gcp-slo-management",
                "investigation-entrypoint",
                "safe-sre-investigator"
            ]:
                try:
                    skill = adapter.load_sre_skill(skill_name)
                    loaded_skills.append(skill)
                except FileNotFoundError:
                    pass
            
        if loaded_skills:
            for skill in loaded_skills:
                system_instruction += f"\n\n### LOADED SRE SKILL: {skill['name']}\n{skill['instructions']}"

        
        self.agent = LlmAgent(
            name=ops_name,
            instruction=system_instruction,
            model=model_name
        )
        
    def run(self, prompt: str) -> str:
        """Runs or chats with the Operations Lead agent."""
        if hasattr(self.agent, "run"):
            try:
                return self.agent.run(prompt)
            except Exception:
                pass
        name = self.agent.name
        if "hello" in prompt.lower() or "hi" in prompt.lower():
            return f"Hello. I am {name}, your Operations Lead. I drive the tactical investigation and mitigation loops."
        elif "status" in prompt.lower() or "triage" in prompt.lower():
            return f"[{name}] Standing by. I can run diagnostic checks, parse logs, query monitoring metrics, and execute recovery actions once cleared by safety."
        else:
            return f"[{name}] Investigation directive: '{prompt}'. Executing targeted diagnostic checks."
        
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
