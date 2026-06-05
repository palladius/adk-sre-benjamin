import os
import pytest
from jinja2 import TemplateError
from src.prompt_loader import load_prompt

def test_load_prompt_yaml_default(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    
    # Write a test YAML prompt file
    yaml_content = """
agent_name: test_agent
system_instruction: |
  You are {{ name }}, SRE lead.
few_shot_examples: |
  Input: {{ alert }} -> Output: Blocked!
"""
    test_file = prompt_dir / "test_agent.yaml"
    test_file.write_text(yaml_content)
    
    # 1. Load default system_instruction
    hydrated_system = load_prompt(
        "test_agent", 
        prompt_dir=str(prompt_dir), 
        name="Benjamin"
    )
    assert hydrated_system.strip() == "You are Benjamin, SRE lead."
    
    # 2. Load custom few_shot_examples
    hydrated_shots = load_prompt(
        "test_agent", 
        prompt_key="few_shot_examples",
        prompt_dir=str(prompt_dir), 
        alert="DROP DATABASE"
    )
    assert hydrated_shots.strip() == "Input: DROP DATABASE -> Output: Blocked!"

def test_load_prompt_missing_file():
    with pytest.raises(FileNotFoundError):
        load_prompt("nonexistent_agent")

def test_load_prompt_missing_key(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    
    yaml_content = """
agent_name: test_agent
system_instruction: |
  Hello World.
"""
    test_file = prompt_dir / "test_agent.yaml"
    test_file.write_text(yaml_content)
    
    with pytest.raises(KeyError):
        load_prompt("test_agent", prompt_key="nonexistent_key", prompt_dir=str(prompt_dir))

def test_load_prompt_invalid_yaml(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    
    # Invalid YAML (missing colon or bad indent)
    yaml_content = """
agent_name test_agent
  system_instruction: Hello
"""
    test_file = prompt_dir / "bad_yaml.yaml"
    test_file.write_text(yaml_content)
    
    with pytest.raises(ValueError, match="Invalid YAML"):
        load_prompt("bad_yaml", prompt_dir=str(prompt_dir))

def test_load_prompt_invalid_jinja(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    
    yaml_content = """
system_instruction: |
  Hello {{ name
"""
    test_file = prompt_dir / "bad_jinja.yaml"
    test_file.write_text(yaml_content)
    
    with pytest.raises(TemplateError):
        load_prompt("bad_jinja", prompt_dir=str(prompt_dir), name="Benjamin")

def test_load_prompt_defaults_to_etc():
    # Calling load_prompt without specifying prompt_dir should default to etc/prompts/
    # and load version from etc/prompts/incident_commander.yaml which has "etc-version-1.13".
    val = load_prompt("incident_commander", prompt_key="version")
    assert val == "etc-version-1.13"

