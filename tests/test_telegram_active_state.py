import os
import json
import pytest
from unittest.mock import patch, MagicMock
import urllib.request
from src.server import start_telegram_bot, get_active_state, save_active_state

@pytest.fixture
def temp_active_state(tmp_path):
    temp_file = tmp_path / "active_state.json"
    # Write a default active state
    default_state = {
        "project_id": "test-project-123",
        "incident_id": "None",
        "incident_status": "UNKNOWN"
    }
    with open(temp_file, "w") as f:
        json.dump(default_state, f)
    
    with patch("src.server.ACTIVE_STATE_FILE", str(temp_file)):
        yield temp_file

@patch("urllib.request.urlopen")
@patch("urllib.request.Request")
def test_telegram_bot_commands(mock_request, mock_urlopen, temp_active_state):
    # Set up environment variables
    os.environ["TELEGRAM_BOT_TOKEN"] = "mock-bot-token"
    os.environ["TELEGRAM_CHAT_ID"] = "123456"
    os.environ["TESTING_BOT"] = "true"
    
    # 1. Test /incident <id> command parsing
    mock_updates_resp = MagicMock()
    mock_updates_resp.status = 200
    mock_updates_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 1001,
                "message": {
                    "chat": {"id": 123456},
                    "text": "/incident INC-TEST-CMD"
                }
            }
        ]
    }).encode("utf-8")
    
    mock_urlopen.return_value.__enter__.return_value = mock_updates_resp
    
    # We need to make sure the investigations/INC-TEST-CMD folder exists so it accepts it
    with patch("os.path.exists", return_value=True):
        start_telegram_bot()
        
    state = get_active_state()
    assert state["incident_id"] == "INC-TEST-CMD"

@patch("urllib.request.urlopen")
@patch("urllib.request.Request")
def test_telegram_bot_callback_queries(mock_request, mock_urlopen, temp_active_state):
    # Set up environment variables
    os.environ["TELEGRAM_BOT_TOKEN"] = "mock-bot-token"
    os.environ["TELEGRAM_CHAT_ID"] = "123456"
    os.environ["TESTING_BOT"] = "true"
    
    # Test select_incident callback query
    mock_cb_resp = MagicMock()
    mock_cb_resp.status = 200
    mock_cb_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 1002,
                "callback_query": {
                    "id": "cb_query_123",
                    "message": {
                        "chat": {"id": 123456},
                        "message_id": 999
                    },
                    "data": "select_incident:INC-CALLBACK-123"
                }
            }
        ]
    }).encode("utf-8")
    
    mock_urlopen.return_value.__enter__.return_value = mock_cb_resp
    
    with patch("os.path.exists", return_value=True):
        start_telegram_bot()
        
    state = get_active_state()
    assert state["incident_id"] == "INC-CALLBACK-123"
