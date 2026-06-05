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
    normalized_dirs = [d.rstrip("/") for d in adapter.search_dirs]
    assert "/home/riccardo/git/sre/skills" in normalized_dirs
    
    # Load anomaly-detection or safe-sre-investigator skill if the real repo is there
    if os.path.exists("/home/riccardo/git/sre/skills/anomaly-detection"):
        skill = adapter.load_sre_skill("anomaly-detection")
        assert skill is not None
        assert skill["name"] == "anomaly-detection"
        assert "anomal" in skill["description"].lower()
        assert len(skill["instructions"]) > 0

def test_skill_adapter_path_expansion():
    test_dirs = ["~/mock-skills-dir"]
    adapter = SkillAdapter(search_dirs=test_dirs)
    import os
    expected = os.path.join(os.path.expanduser("~"), "mock-skills-dir")
    assert adapter.search_dirs[0] == expected

def test_agent_auto_load_skills(tmp_path, monkeypatch):
    # Create mock skills for Ops and Planning/Comms
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    
    anomaly_dir = skills_dir / "anomaly-detection"
    anomaly_dir.mkdir()
    (anomaly_dir / "SKILL.md").write_text("""---
name: anomaly-detection
description: Mock anomaly detection
---
# Instructions
Auto-loaded anomaly detection instructions.
""")
    
    pomo_dir = skills_dir / "postmortem-generator"
    pomo_dir.mkdir()
    (pomo_dir / "SKILL.md").write_text("""---
name: postmortem-generator
description: Mock postmortem generator
---
# Instructions
Auto-loaded postmortem generator instructions.
""")

    # Point SkillAdapter search paths to our tmp SRE dir
    monkeypatch.setenv("GEMINI_CLI_SRE_DIR", str(tmp_path))
    
    from src.agents.comms import CommunicationsLead
    ops = OperationsLead()
    planning = PlanningLead()
    comms = CommunicationsLead()
    
    assert "Auto-loaded anomaly detection" in ops.agent.instruction
    assert "Auto-loaded postmortem generator" in planning.agent.instruction
    assert "Auto-loaded postmortem generator" in comms.agent.instruction


