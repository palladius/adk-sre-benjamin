import pytest
from src.safety import decompose_command, assess_risk, is_command_safe

def test_decompose_command_simple():
    cmd = "cat logs.txt"
    parts = decompose_command(cmd)
    assert parts == ["cat logs.txt"]

def test_decompose_command_pipe():
    cmd = "cat logs.txt | grep error"
    parts = decompose_command(cmd)
    assert parts == ["cat logs.txt", "grep error"]

def test_decompose_command_chained():
    cmd = "apt-get update && apt-get install -y nginx; sudo systemctl restart nginx"
    parts = decompose_command(cmd)
    assert parts == ["apt-get update", "apt-get install -y nginx", "sudo systemctl restart nginx"]

def test_assess_risk_low():
    assert assess_risk("cat logs.txt") == "LOW"
    assert assess_risk("grep 'Exception' app.log") == "LOW"
    assert assess_risk("df -h") == "LOW"

def test_assess_risk_medium():
    assert assess_risk("pip install google-adk") == "MEDIUM"
    assert assess_risk("systemctl restart nginx") == "MEDIUM"
    assert assess_risk("echo 'PORT=8080' > .env") == "MEDIUM"

def test_assess_risk_high():
    assert assess_risk("rm -rf /") == "HIGH"
    assert assess_risk("DROP DATABASE prod_db") == "HIGH"
    assert assess_risk("sudo reboot") == "HIGH"
    assert assess_risk("dd if=/dev/zero of=/dev/sda") == "HIGH"

def test_is_command_safe_low():
    cmd = "cat log.txt | grep 'timeout'"
    is_safe, risk, reasons = is_command_safe(cmd)
    assert is_safe is True
    assert risk == "LOW"
    assert len(reasons) == 0

def test_is_command_safe_high_blocked():
    cmd = "cat logs.txt && rm -rf /home/riccardo/"
    is_safe, risk, reasons = is_command_safe(cmd)
    assert is_safe is False
    assert risk == "HIGH"
    assert len(reasons) > 0
    assert any("Destructive command" in r or "rm -rf" in r for r in reasons)
