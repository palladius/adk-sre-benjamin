import os
import json
import pytest
from src.comms_telegram import send_telegram_alert
from src.comms_github import GitHubTicketingEngine

def test_telegram_mock_mode(tmp_path, monkeypatch):
    # Ensure no actual Telegram variables are set
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    
    feed_path = os.path.join(tmp_path, "telegram_feed.json")
    
    success = send_telegram_alert(
        message="Test alert: active incident",
        incident_id="INC-20260601-TEST",
        feed_file_path=feed_path
    )
    
    assert success is True
    assert os.path.exists(feed_path)
    
    with open(feed_path, "r") as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["message"] == "Test alert: active incident"
        assert data[0]["incident_id"] == "INC-20260601-TEST"

def test_github_ticketing_mock_mode(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    
    issue_file = os.path.join(tmp_path, "github_issue.json")
    engine = GitHubTicketingEngine(issue_file_path=issue_file)
    
    # 1. Create issue
    issue_id = engine.create_incident_issue(
        incident_id="INC-20260601-TEST",
        trigger_event="frontend_latency_slo_violated",
        project_id="prod-db-999"
    )
    
    assert issue_id == "issue_1"
    assert os.path.exists(issue_file)
    
    with open(issue_file, "r") as f:
        data = json.load(f)
        assert data["incident_id"] == "INC-20260601-TEST"
        assert data["title"] == "🚨 ACTIVE: INC-20260601-TEST - frontend_latency_slo_violated"
        assert data["status"] == "open"
        assert len(data["comments"]) == 0
        
    # 2. Add Comment
    engine.add_issue_comment("issue_1", "Operations Lead", "Querying metrics telemetry.")
    
    with open(issue_file, "r") as f:
        data = json.load(f)
        assert len(data["comments"]) == 1
        assert data["comments"][0]["author"] == "Operations Lead"
        assert data["comments"][0]["body"] == "Querying metrics telemetry."
        
    # 3. Close Issue
    engine.close_incident_issue("issue_1", "Restarted database service successfully.")
    
    with open(issue_file, "r") as f:
        data = json.load(f)
        assert data["status"] == "closed"
        assert len(data["comments"]) == 2
        assert data["comments"][1]["body"] == "Incident Resolved: Restarted database service successfully."
