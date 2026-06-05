import os
import yaml
from jinja2 import Environment, BaseLoader, TemplateError

DEFAULT_PROMPT_DIR = os.path.join(os.path.dirname(__file__), "prompts")

def load_prompt(
    agent_name: str, 
    prompt_key: str = "system_instruction", 
    prompt_dir: str = None, 
    **kwargs
) -> str:
    """Loads and hydrates SRE agent prompts from a structured YAML configuration using Jinja2."""
    filename = f"{agent_name}.yaml"
    
    if prompt_dir is None:
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        etc_prompts_dir = os.path.join(repo_root, "etc", "prompts")
        if os.path.exists(os.path.join(etc_prompts_dir, filename)):
            prompt_dir = etc_prompts_dir
        else:
            prompt_dir = DEFAULT_PROMPT_DIR
            
    filepath = os.path.join(prompt_dir, filename)

    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Prompt YAML template for agent '{agent_name}' not found at {filepath}")
        
    try:
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as ye:
        raise ValueError(f"Invalid YAML format in '{filename}': {ye}") from ye
    except Exception as e:
        raise ValueError(f"Error reading prompt file '{filename}': {e}") from e
        
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML content in '{filename}': expected dictionary/object.")
        
    if prompt_key not in data:
        raise KeyError(f"Prompt key '{prompt_key}' not found in configuration for agent '{agent_name}'")
        
    prompt_template = data[prompt_key]
    
    kwargs.setdefault("comms_name", os.getenv("COMMS_LEAD_NAME") or os.getenv("COMMUNICATIONS_LEAD_NAME") or os.getenv("MADHAVI_NAME") or "Madhavi")
    kwargs.setdefault("commander_name", os.getenv("COMMANDER_NAME") or os.getenv("INCIDENT_COMMANDER_NAME") or "Benjamin")
    kwargs.setdefault("ops_name", os.getenv("OPS_LEAD_NAME") or os.getenv("OPERATIONS_LEAD_NAME") or os.getenv("OPS_AGENT_NAME") or "OpsAgent")
    kwargs.setdefault("planning_name", os.getenv("PLANNING_LEAD_NAME") or os.getenv("PLANNING_AGENT_NAME") or "Scrivano Fossati")
    kwargs.setdefault("logistics_name", os.getenv("LOGISTICS_LEAD_NAME") or os.getenv("LOGISTICS_AGENT_NAME") or "LogisticsAgent")
    
    # Initialize a clean, sandbox-safe Jinja2 environment for string compilation
    env = Environment(loader=BaseLoader())
    
    try:
        template = env.from_string(prompt_template)
        return template.render(**kwargs)
    except Exception as e:
        raise TemplateError(f"Error rendering prompt key '{prompt_key}' in '{filename}': {e}") from e
