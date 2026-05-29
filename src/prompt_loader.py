import os
from jinja2 import Environment, FileSystemLoader, TemplateError

DEFAULT_PROMPT_DIR = os.path.join(os.path.dirname(__file__), "prompts")

def load_prompt(agent_name: str, prompt_dir: str = None, **kwargs) -> str:
    """Loads and hydrates a text-based system prompt for an SRE agent using Jinja2."""
    if prompt_dir is None:
        prompt_dir = DEFAULT_PROMPT_DIR
        
    filename = f"{agent_name}.txt"
    filepath = os.path.join(prompt_dir, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Prompt template for agent '{agent_name}' not found at {filepath}")
        
    env = Environment(loader=FileSystemLoader(prompt_dir))
    
    try:
        template = env.get_template(filename)
        return template.render(**kwargs)
    except Exception as e:
        # Wrap any Jinja parse/render errors as TemplateError
        raise TemplateError(f"Error rendering template '{filename}': {e}") from e
