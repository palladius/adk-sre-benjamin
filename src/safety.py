import re

HIGH_KEYWORDS = [
    "rm -rf", 
    "drop database", 
    "truncate", 
    "reboot", 
    "shutdown", 
    "dd "
]

MEDIUM_KEYWORDS = [
    "apt-get install", 
    "pip install", 
    "npm install", 
    "systemctl restart", 
    "systemctl stop", 
    "service ", 
    ".env", 
    "config"
]

def decompose_command(command: str) -> list[str]:
    """Decomposes a nested command string by splitting on shell control operators."""
    operators = ['&&', '||', ';', '|']
    raw_parts = [command]
    
    for op in operators:
        next_parts = []
        for part in raw_parts:
            next_parts.extend(part.split(op))
        raw_parts = next_parts
        
    return [p.strip() for p in raw_parts if p.strip()]

def assess_risk(command_part: str) -> str:
    """Classifies a command part into LOW, MEDIUM, or HIGH risk categories."""
    cmd_lower = command_part.lower()
    
    # Evaluate high-risk keywords
    for kw in HIGH_KEYWORDS:
        if kw in cmd_lower:
            return "HIGH"
            
    # Evaluate medium-risk keywords
    for kw in MEDIUM_KEYWORDS:
        if kw in cmd_lower:
            return "MEDIUM"
            
    return "LOW"

def is_command_safe(command: str) -> tuple[bool, str, list[str]]:
    """Analyzes all parts of a command string for potential safety risk violations.
    
    Returns:
        (is_safe, max_risk, blocked_reasons)
    """
    parts = decompose_command(command)
    max_risk = "LOW"
    reasons = []
    
    risk_weights = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3
    }
    
    for part in parts:
        risk = assess_risk(part)
        
        # Track highest risk category encountered
        if risk_weights[risk] > risk_weights[max_risk]:
            max_risk = risk
            
        if risk == "HIGH":
            reasons.append(f"Destructive command element detected in: '{part}'")
            
    is_safe = max_risk != "HIGH"
    return is_safe, max_risk, reasons
