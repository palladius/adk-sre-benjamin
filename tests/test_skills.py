import os
import pytest
from src.skills_adapter import SkillAdapter
from src.agents.ops_lead import OperationsLead
from src.agents.planning_lead import PlanningLead

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

def test_agent_hydration_with_skill(tmp_path):
    skill_dir = tmp_path / "telemetry-skill"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("""---
name: telemetry-skill
description: Telemetry analysis skill
---
# Instructions
Look for latency alerts and report pool depth.
""")
    
    adapter = SkillAdapter(search_dirs=[str(tmp_path)])
    skill = adapter.load_sre_skill("telemetry-skill")
    
    # Initialize agents with dynamically loaded skill
    ops = OperationsLead(loaded_skills=[skill])
    planning = PlanningLead(loaded_skills=[skill])
    
    assert "telemetry-skill" in ops.agent.instruction
    assert "report pool depth" in ops.agent.instruction
    assert "telemetry-skill" in planning.agent.instruction
    assert "report pool depth" in planning.agent.instruction

def test_skill_loader_real():
    # Attempt to load a real SRE skill from the palladius-common-commands plugin path
    real_plugin_path = "/home/riccardo/.gemini/config/plugins/palladius-common-commands/skills/"
    
    if os.path.exists(real_plugin_path):
        adapter = SkillAdapter(search_dirs=[real_plugin_path])
        skill = adapter.load_sre_skill("cloud-build-investigation")
        
        assert skill is not None
        assert "cloud-build-investigation" in skill["name"].lower()
        assert len(skill["instructions"]) > 0

def test_skill_loader_sre_extension_dir(monkeypatch):
    # Set the env variable to the real git repository path
    monkeypatch.setenv("GEMINI_CLI_SRE_DIR", "/home/riccardo/git/sre")
    
    adapter = SkillAdapter()
    assert "/home/riccardo/git/sre" in adapter.search_dirs
    assert "/home/riccardo/git/sre/skills" in adapter.search_dirs
    
    # Load anomaly-detection or safe-sre-investigator skill if the real repo is there
    if os.path.exists("/home/riccardo/git/sre/skills/anomaly-detection"):
        skill = adapter.load_sre_skill("anomaly-detection")
        assert skill is not None
        assert skill["name"] == "anomaly-detection"
        assert "anomal" in skill["description"].lower()
        assert len(skill["instructions"]) > 0
