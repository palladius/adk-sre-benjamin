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

@patch("urllib.request.urlopen")
@patch("urllib.request.Request")
def test_telegram_bot_commands_resolution(mock_request, mock_urlopen, temp_active_state):
    # Set up environment variables
    os.environ["TELEGRAM_BOT_TOKEN"] = "mock-bot-token"
    os.environ["TELEGRAM_CHAT_ID"] = "123456"
    os.environ["TESTING_BOT"] = "true"
    
    # 1. Test case-insensitive resolution (lowercase)
    mock_updates_resp = MagicMock()
    mock_updates_resp.status = 200
    mock_updates_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 1003,
                "message": {
                    "chat": {"id": 123456},
                    "text": "/incident inc-test-case"
                }
            }
        ]
    }).encode("utf-8")
    
    mock_urlopen.return_value.__enter__.return_value = mock_updates_resp
    
    # Mock get_incidents_list to return INC-TEST-CASE
    mock_get_list = MagicMock(return_value=[{"id": "INC-TEST-CASE", "status": "INVESTIGATING"}])
    
    with patch("src.server.get_incidents_list", mock_get_list), \
         patch("os.path.exists", return_value=True):
        start_telegram_bot()
        
    state = get_active_state()
    assert state["incident_id"] == "INC-TEST-CASE"

    # 2. Test index-based resolution (e.g. 1)
    mock_updates_resp_idx = MagicMock()
    mock_updates_resp_idx.status = 200
    mock_updates_resp_idx.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 1004,
                "message": {
                    "chat": {"id": 123456},
                    "text": "/incident 1"
                }
            }
        ]
    }).encode("utf-8")
    
    mock_urlopen.return_value.__enter__.return_value = mock_updates_resp_idx
    
    with patch("src.server.get_incidents_list", mock_get_list), \
         patch("os.path.exists", return_value=True):
        start_telegram_bot()
        
    state2 = get_active_state()
    assert state2["incident_id"] == "INC-TEST-CASE"

@patch("urllib.request.urlopen")
@patch("urllib.request.Request")
def test_telegram_bot_mobile_shortcuts(mock_request, mock_urlopen, temp_active_state):
    # Set up environment variables
    os.environ["TELEGRAM_BOT_TOKEN"] = "mock-bot-token"
    os.environ["TELEGRAM_CHAT_ID"] = "123456"
    os.environ["TESTING_BOT"] = "true"
    
    # 1. Test sending raw digit shortcut (e.g., "#1")
    mock_updates_resp = MagicMock()
    mock_updates_resp.status = 200
    mock_updates_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 1005,
                "message": {
                    "chat": {"id": 123456},
                    "text": "#1"
                }
            }
        ]
    }).encode("utf-8")
    
    mock_urlopen.return_value.__enter__.return_value = mock_updates_resp
    mock_get_list = MagicMock(return_value=[{"id": "INC-SHORTCUT-CASE", "status": "INVESTIGATING"}])
    
    with patch("src.server.get_incidents_list", mock_get_list), \
         patch("os.path.exists", return_value=True):
        start_telegram_bot()
        
    state = get_active_state()
    assert state["incident_id"] == "INC-SHORTCUT-CASE"

    # 2. Test sending raw project name shortcut (e.g., "test-project-123")
    mock_updates_resp_proj = MagicMock()
    mock_updates_resp_proj.status = 200
    mock_updates_resp_proj.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 1006,
                "message": {
                    "chat": {"id": 123456},
                    "text": "test-project-123"
                }
            }
        ]
    }).encode("utf-8")
    
    mock_urlopen.return_value.__enter__.return_value = mock_updates_resp_proj
    mock_get_projects = MagicMock(return_value=["test-project-123"])
    
    with patch("src.server.get_discovered_projects", mock_get_projects), \
         patch("os.path.exists", return_value=True):
        start_telegram_bot()
        
    state2 = get_active_state()
    assert state2["project_id"] == "test-project-123"

@patch("urllib.request.urlopen")
@patch("urllib.request.Request")
def test_telegram_bot_list_projects_button(mock_request, mock_urlopen, temp_active_state):
    os.environ["TELEGRAM_BOT_TOKEN"] = "mock-bot-token"
    os.environ["TELEGRAM_CHAT_ID"] = "123456"
    os.environ["TESTING_BOT"] = "true"
    
    mock_updates_resp = MagicMock()
    mock_updates_resp.status = 200
    mock_updates_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 1007,
                "message": {
                    "chat": {"id": 123456},
                    "text": "☁️ List Projects"
                }
            }
        ]
    }).encode("utf-8")
    
    mock_urlopen.return_value.__enter__.return_value = mock_updates_resp
    
    with patch("src.server.get_discovered_projects", return_value=["project-a", "project-b"]) as mock_get_proj, \
         patch("src.server.send_telegram_inline_keyboard") as mock_send_kbd, \
         patch("os.path.exists", return_value=True):
        start_telegram_bot()
        
        assert mock_get_proj.call_count >= 1
        mock_send_kbd.assert_called_once_with(
            "mock-bot-token", "123456",
            "☁️ *Select a GCP Project context:*",
            [[{"text": "☁️ project-a", "callback_data": "select_project:project-a"}],
             [{"text": "☁️ project-b", "callback_data": "select_project:project-b"}]]
        )
