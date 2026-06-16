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

class OperationsLead:
    def __init__(self, model_name: str = None, loaded_skills: list[dict] = None, incident_context = None, **kwargs):
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
            name=ops_name,
            instruction=system_instruction,
            model=model_name,
            metadata=self.metadata
        )
        self.agent.metadata = self.metadata
        
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

def validate_mutation_command(command: str) -> tuple[bool, str]:
    """Ensures a command is strictly limited to whitelisted VM operations."""
    cmd_clean = command.strip().lower()
    
    # Strip leading sudo if present
    if cmd_clean.startswith("sudo "):
        cmd_clean = cmd_clean[5:].strip()
        
    import re
    # Match against whitelisted patterns
    allowed_pattern = r"^systemctl (restart|start|stop) (mysql|postgresql|nginx|apache2)$"
    if not re.match(allowed_pattern, cmd_clean):
        return False, f"Command '{command}' is not in the whitelist of approved VM operations."
        
    return True, ""

class MutationAgent:
    """Agent that executes whitelisted system mutations via gcloud compute ssh."""
    
    def __init__(self, project_id: str = None):
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID") or "sre-next"
        
    def execute_mutation(self, command: str, instance_name: str = None, zone: str = None) -> tuple[bool, str]:
        """Validates and executes a mutation command on a VM instance using gcloud compute ssh."""
        # 1. Security validation
        is_valid, err_msg = validate_mutation_command(command)
        if not is_valid:
            return False, f"Blocked: {err_msg}"
            
        sre_mode = os.getenv("SRE_MODE", "MOCK").upper()
        if sre_mode != "LIVE":
            return True, f"Mock execution successful for command: {command}"
            
        # 2. Target VM discovery
        import subprocess
        import json
        if not instance_name or not zone:
            try:
                cmd = ["gcloud", "compute", "instances", "list", f"--project={self.project_id}", "--format=json"]
                res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                vms = json.loads(res.stdout)
                for vm in vms:
                    if vm.get("status") == "RUNNING":
                        instance_name = vm.get("name")
                        zone = vm.get("zone", "").split("/")[-1]
                        break
            except Exception as e:
                print(f"[MutationAgent Warning] Live VM list query failed: {e}")
                
        # Fallbacks if discovery failed
        if not instance_name:
            if self.project_id == "sre-next":
                instance_name = "frontend-vm"
                zone = "us-central1-a"
            else:
                instance_name = "internal-db-vm"
                zone = "us-central1-a"
                
        # 3. Construct gcloud compute ssh command
        ssh_cmd = [
            "gcloud", "compute", "ssh", instance_name,
            f"--zone={zone}",
            f"--project={self.project_id}",
            f"--command=sudo {command}"
        ]
        
        try:
            res = subprocess.run(ssh_cmd, capture_output=True, text=True, check=True)
            return True, res.stdout or f"Command '{command}' executed successfully on {instance_name}."
        except subprocess.CalledProcessError as e:
            return False, f"Execution failed: {e.stderr}"
