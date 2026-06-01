import os
import pytest
from src.skills_adapter import SkillAdapter

def test_skill_loader_mock(tmp_path):
    # Set up mock skill folder structure
    skill_dir = tmp_path / "mock-skill"
    skill_dir.mkdir()
    
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("""---
name: mock-skill
description: A mock SRE investigation skill
metadata:
  version: 1.0
---
# Mock SRE Investigation Instructions
Follow these steps to analyze system telemetry:
1. Check CPU load.
2. Restart pool.
""")
    
    adapter = SkillAdapter(search_dirs=[str(tmp_path)])
    skill = adapter.load_sre_skill("mock-skill")
    
    assert skill is not None
    assert skill["name"] == "mock-skill"
    assert skill["description"] == "A mock SRE investigation skill"
    assert "Mock SRE Investigation Instructions" in skill["instructions"]
    assert "Check CPU load" in skill["instructions"]

def test_skill_loader_real():
    # Attempt to load a real SRE skill from the palladius-common-commands plugin path
    real_plugin_path = "/home/riccardo/.gemini/config/plugins/palladius-common-commands/skills/"
    
    if os.path.exists(real_plugin_path):
        adapter = SkillAdapter(search_dirs=[real_plugin_path])
        skill = adapter.load_sre_skill("cloud-build-investigation")
        
        assert skill is not None
        assert "cloud-build-investigation" in skill["name"].lower()
        assert len(skill["instructions"]) > 0
