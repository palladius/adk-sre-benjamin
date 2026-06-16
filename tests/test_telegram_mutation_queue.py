import os
import json
import pytest
from unittest.mock import patch, MagicMock
from src.server import start_telegram_bot, get_active_state, save_active_state

@pytest.fixture
def temp_active_state(tmp_path):
    temp_file = tmp_path / "active_state.json"
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
def test_telegram_bot_pending_command(mock_request, mock_urlopen, temp_active_state):
    state = get_active_state()
    state["incident_id"] = "INC-TEST-PENDING"
    save_active_state(state)
    
    incident_path = os.path.join("investigations", "INC-TEST-PENDING")
    os.makedirs(incident_path, exist_ok=True)
    
    pending_file = os.path.join(incident_path, "pending_approvals.json")
    queue_data = [
        {
            "id": "cmd-01",
            "command": "kubectl drain node-1",
            "timestamp": "2026-06-02T12:00:00Z",
            "risk_factor": "🟠 HIGH",
            "risk_reason": "Draining primary services might disrupt user traffic.",
            "justification": "Clears stuck TCP sockets causing the SLO alert."
        }
    ]
    with open(pending_file, "w") as f:
        json.dump(queue_data, f)
        
    os.environ["TELEGRAM_BOT_TOKEN"] = "mock-bot-token"
    os.environ["TELEGRAM_CHAT_ID"] = "123456"
    os.environ["TESTING_BOT"] = "true"
    
    mock_updates_resp = MagicMock()
    mock_updates_resp.status = 200
    mock_updates_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 2001,
                "message": {
                    "chat": {"id": 123456},
                    "text": "/pending"
                }
            }
        ]
    }).encode("utf-8")
    
    mock_urlopen.return_value.__enter__.return_value = mock_updates_resp
    
    with patch("src.server.send_telegram_inline_keyboard") as mock_send_kbd, \
         patch("os.path.exists", return_value=True):
        start_telegram_bot()
        
    mock_send_kbd.assert_called_once()
    args, kwargs = mock_send_kbd.call_args
    assert args[0] == "mock-bot-token"
    assert args[1] == "123456"
    text = args[2]
    assert "Pending SRE Mutation Actions Queue" in text
    assert "cmd-01" in text
    assert "kubectl drain node-1" in text
    assert "🟠 HIGH" in text
    
    buttons = args[3]
    assert len(buttons) == 1
    assert buttons[0][0]["text"] == "💥 Approve cmd-01"
    assert buttons[0][0]["callback_data"] == "approve_mut:cmd-01"
    assert buttons[0][1]["text"] == "❌ Reject cmd-01"
    assert buttons[0][1]["callback_data"] == "reject_mut:cmd-01"
    
    # Clean up
    if os.path.exists(incident_path):
        import shutil
        shutil.rmtree(incident_path)

@patch("urllib.request.urlopen")
@patch("urllib.request.Request")
def test_telegram_bot_approve_callback(mock_request, mock_urlopen, temp_active_state):
    state = get_active_state()
    state["incident_id"] = "INC-TEST-PENDING"
    save_active_state(state)
    
    incident_path = os.path.join("investigations", "INC-TEST-PENDING")
    os.makedirs(incident_path, exist_ok=True)
    
    with open(os.path.join(incident_path, "state.md"), "w") as f:
        f.write("# state\n## Pending SRE Mutation Actions Queue\n| `cmd-01` |\n")
        
    pending_file = os.path.join(incident_path, "pending_approvals.json")
    queue_data = [
        {
            "id": "cmd-01",
            "command": "kubectl drain node-1",
            "timestamp": "2026-06-02T12:00:00Z",
            "risk_factor": "🟠 HIGH",
            "risk_reason": "Draining primary services might disrupt user traffic.",
            "justification": "Clears stuck TCP sockets causing the SLO alert."
        }
    ]
    with open(pending_file, "w") as f:
        json.dump(queue_data, f)
        
    os.environ["TELEGRAM_BOT_TOKEN"] = "mock-bot-token"
    os.environ["TELEGRAM_CHAT_ID"] = "123456"
    os.environ["TESTING_BOT"] = "true"
    
    mock_cb_resp = MagicMock()
    mock_cb_resp.status = 200
    mock_cb_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 2002,
                "callback_query": {
                    "id": "cb_query_456",
                    "message": {
                        "chat": {"id": 123456},
                        "message_id": 999
                    },
                    "data": "approve_mut:cmd-01"
                }
            }
        ]
    }).encode("utf-8")
    
    mock_urlopen.return_value.__enter__.return_value = mock_cb_resp
    
    with patch("src.server.answer_telegram_callback_query") as mock_ans, \
         patch("src.server.edit_telegram_message_text") as mock_edit:
        start_telegram_bot()
        
    mock_ans.assert_called_once_with("mock-bot-token", "cb_query_456", "Approved cmd-01")
    mock_edit.assert_called_once_with("mock-bot-token", "123456", 999, "✅ *Mutation approved:* `cmd-01`")
    
    with open(pending_file, "r") as f:
        q = json.load(f)
    assert len(q) == 0
    
    # Clean up
    if os.path.exists(incident_path):
        import shutil
        shutil.rmtree(incident_path)

@patch("urllib.request.urlopen")
@patch("urllib.request.Request")
def test_send_telegram_menu_with_pending_button(mock_request, mock_urlopen, temp_active_state):
    mock_response = MagicMock()
    mock_response.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    state = get_active_state()
    state["incident_id"] = "None"
    save_active_state(state)
    
    from src.server import send_telegram_menu
    send_telegram_menu("mock-bot-token", "123456", "Hello operator")
    
    args, kwargs = mock_request.call_args
    data = kwargs.get("data")
    if not data and len(args) > 1:
        data = args[1]
        
    import urllib.parse
    decoded_params = urllib.parse.parse_qs(data.decode("utf-8"))
    reply_markup = json.loads(decoded_params["reply_markup"][0])
    keyboard = reply_markup["keyboard"]
    
    assert not any(any(btn.get("text") == "📥 Pending Approvals" for btn in row) for row in keyboard)
    
    state["incident_id"] = "INC-ACTIVE-123"
    save_active_state(state)
    
    mock_request.reset_mock()
    send_telegram_menu("mock-bot-token", "123456", "Hello operator")
    
    args, kwargs = mock_request.call_args
    data = kwargs.get("data")
    if not data and len(args) > 1:
        data = args[1]
    
    decoded_params = urllib.parse.parse_qs(data.decode("utf-8"))
    reply_markup = json.loads(decoded_params["reply_markup"][0])
    keyboard = reply_markup["keyboard"]
    
    assert any(any(btn.get("text") == "📥 Pending Approvals" for btn in row) for row in keyboard)
