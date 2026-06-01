import os
import re
import yaml

DEFAULT_SEARCH_DIRS = [
    "/home/riccardo/.gemini/config/plugins/palladius-common-commands/skills/",
    "/home/riccardo/.gemini/config/plugins/palladius-public-goodies/skills/",
    "/home/riccardo/.gemini/config/plugins/palladius-private-goodies/skills/",
]

class SkillAdapter:
    def __init__(self, search_dirs: list[str] = None):
        self.search_dirs = search_dirs if search_dirs is not None else DEFAULT_SEARCH_DIRS
        
    def load_sre_skill(self, skill_name: str) -> dict:
        """Discovers, loads, and parses an SRE extension skill from the plugin environment."""
        skill_dir_path = None
        
        # 1. Discover the skill directory
        for base_dir in self.search_dirs:
            potential_path = os.path.join(base_dir, skill_name)
            if os.path.exists(potential_path) and os.path.isdir(potential_path):
                skill_dir_path = potential_path
                break
                
        if not skill_dir_path:
            raise FileNotFoundError(f"SRE Skill '{skill_name}' could not be resolved in search paths.")
            
        skill_md_path = os.path.join(skill_dir_path, "SKILL.md")
        if not os.path.exists(skill_md_path):
            raise FileNotFoundError(f"SKILL.md file missing inside resolved path: {skill_dir_path}")
            
        # 2. Parse SKILL.md containing YAML frontmatter and Markdown body
        with open(skill_md_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        frontmatter = {}
        instructions = content
        
        # SRE skills format uses --- enclosed YAML block at the very top
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
        if match:
            raw_yaml = match.group(1)
            instructions = match.group(2).strip()
            try:
                frontmatter = yaml.safe_load(raw_yaml) or {}
            except Exception as e:
                print(f"[Skill Loader Warning] Failed to parse frontmatter YAML: {e}")
                
        return {
            "name": frontmatter.get("name", skill_name),
            "description": frontmatter.get("description", "SRE automated skill"),
            "instructions": instructions,
            "path": skill_dir_path,
            "frontmatter": frontmatter
        }
