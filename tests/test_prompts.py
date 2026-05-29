import os
import pytest
from jinja2 import TemplateError
from src.prompt_loader import load_prompt

def test_load_prompt_success(tmp_path):
    # Set up a mock templates directory
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    
    # Write a test template
    template_content = "Hello {{ name }}! You are the {{ role }}."
    test_file = prompt_dir / "test_agent.txt"
    test_file.write_text(template_content)
    
    # Load and hydrate prompt
    hydrated = load_prompt("test_agent", prompt_dir=str(prompt_dir), name="Benjamin", role="Incident Commander")
    assert hydrated == "Hello Benjamin! You are the Incident Commander."

def test_load_prompt_missing_file():
    with pytest.raises(FileNotFoundError):
        load_prompt("nonexistent_agent")

def test_load_prompt_invalid_jinja(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    
    # Invalid Jinja syntax: unclosed braces
    test_file = prompt_dir / "bad_agent.txt"
    test_file.write_text("Hello {{ name")
    
    with pytest.raises(TemplateError):
        load_prompt("bad_agent", prompt_dir=str(prompt_dir), name="Benjamin")
