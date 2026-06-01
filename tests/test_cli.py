import os
import sys
import io
import pytest
from src.cli import run_cli

def test_cli_piped_input_and_hydrate(tmp_path):
    # Set up mock incident folder
    incident_dir = tmp_path / "INC-MOCK-111"
    incident_dir.mkdir()
    
    # Create a mock state.md
    state_file = incident_dir / "state.md"
    state_file.write_text("DATABASE_STATUS: latency spiking at 480ms")
    
    # Create mock prompts directory
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    yaml_content = """
agent_name: ops_agent
system_instruction: |
  You are Ops Lead. Active state: {{ state }}
"""
    (prompt_dir / "ops_agent.yaml").write_text(yaml_content)
    
    # Simulate piping standard input (stdin)
    stdin_data = "Find the database error in active logs."
    sys.stdin = io.StringIO(stdin_data)
    
    # We capture stdout to inspect what the CLI produces
    captured_stdout = io.StringIO()
    sys.stdout = captured_stdout
    
    # Execute the CLI runner
    exit_code = run_cli([
        "--agent", "ops_agent",
        "--incident-dir", str(incident_dir),
        "--prompt-dir", str(prompt_dir)
    ])
    
    # Restore original stdin/stdout
    sys.stdin = sys.__stdin__
    sys.stdout = sys.__stdout__
    
    assert exit_code == 0
    output = captured_stdout.getvalue()
    
    # Verify the hydrated system instruction and user instruction are output
    assert "Active state: DATABASE_STATUS: latency spiking at 480ms" in output
    assert "Instruction: Find the database error in active logs." in output

def test_cli_interactive_message(monkeypatch):
    # Set up mock prompts directory
    import io
    captured_stdout = io.StringIO()
    sys.stdout = captured_stdout
    
    # Run the CLI with interactive message targeting 'comms' alias
    exit_code = run_cli([
        "--agent", "comms",
        "--message", "hello there"
    ])
    
    sys.stdout = sys.__stdout__
    
    assert exit_code == 0
    output = captured_stdout.getvalue()
    assert "Agent: comms" in output
    assert "Instruction: hello there" in output
    assert "Response:" in output
    assert "Madhavi" in output or "Lucia" in output

def test_cli_missing_args():
    # Calling without --agent should fail
    with pytest.raises(SystemExit):
        run_cli([])
