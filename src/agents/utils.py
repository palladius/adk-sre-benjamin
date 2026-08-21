import re

def sanitize_agent_name(name: str) -> str:
    """Sanitizes raw agent names to valid Python identifiers required by ADK Agent schema."""
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', name.strip())
    cleaned = re.sub(r'_+', '_', cleaned).strip('_')
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"agent_{cleaned}"
    return cleaned
