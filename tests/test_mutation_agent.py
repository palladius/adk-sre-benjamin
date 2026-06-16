import os
import pytest
from src.agents import MutationAgent, validate_mutation_command

def test_validate_mutation_command_valid():
    # Valid whitelisted commands
    valid_commands = [
        "systemctl restart mysql",
        "systemctl restart postgresql",
        "systemctl restart nginx",
        "systemctl restart apache2",
        "sudo systemctl restart mysql",
        "systemctl start nginx",
        "systemctl stop postgresql"
    ]
    for cmd in valid_commands:
        is_valid, msg = validate_mutation_command(cmd)
        assert is_valid is True
        assert msg == ""

def test_validate_mutation_command_invalid():
    # Non-whitelisted/dangerous commands
    invalid_commands = [
        "rm -rf /",
        "systemctl restart docker",
        "apt-get install nginx",
        "drop database users",
        "reboot",
        "systemctl restart mysql; rm -rf /"
    ]
    for cmd in invalid_commands:
        is_valid, msg = validate_mutation_command(cmd)
        assert is_valid is False
        assert "not in the whitelist" in msg

def test_mutation_agent_mock_execution(monkeypatch):
    # Ensure that SRE_MODE=MOCK (default) does not run actual commands
    monkeypatch.setenv("SRE_MODE", "MOCK")
    agent = MutationAgent(project_id="test-project")
    
    # Whitelisted command should succeed in mock mode
    success, output = agent.execute_mutation("systemctl restart mysql")
    assert success is True
    assert "Mock execution successful" in output
    
    # Non-whitelisted command should be blocked even in mock mode
    success, output = agent.execute_mutation("rm -rf /")
    assert success is False
    assert "Blocked" in output

def test_mutation_agent_live_execution_blocked(monkeypatch):
    # SRE_MODE=LIVE should still block non-whitelisted commands immediately
    monkeypatch.setenv("SRE_MODE", "LIVE")
    agent = MutationAgent(project_id="test-project")
    
    success, output = agent.execute_mutation("rm -rf /")
    assert success is False
    assert "Blocked" in output
