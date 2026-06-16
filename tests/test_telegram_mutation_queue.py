import os
import json
import pytest
import shutil
from unittest.mock import patch, MagicMock
from src.incident import get_investigations_dir
from src.server import start_telegram_bot, get_active_state, save_active_state, add_pending_mutation

INCIDENT_ID = "INC-TG-QUEUE-TEST"

def get_incident_path():
    return os.path.join(get_investigations_dir(), INCIDENT_ID)

@pytest.fixture(scope="module", autouse=True)
def setup_mock_incident():
    incident_path = get_incident_path()
    if os.path.exists(incident_path):
        shutil.rmtree(incident_path)
    os.makedirs(incident_path, exist_ok=True)
    
    # Create mock state.md
    with open(os.path.join(incident_path, "state.md"), "w") as f:
        f.write("""# Active SRE Incident State: INC-TG-QUEUE-TEST
## Metadata
- **Status:** ACTIVE
- **Target Project:** `test-project`
- **Trigger Event:** `test_trigger`
- **Incident Commander:** Benjamin
- **Safety Level:** LOW Risk
""")
        
    # Create mock timeline.md
    with open(os.path.join(incident_path, "timeline.md"), "w") as f:
        f.write("- **[2026-06-01T07:55:00Z]** [System] Incident declared.\n")
        
    # Create mock chat.json
    with open(os.path.join(incident_path, "chat.json"), "w") as f:
        json.dump([], f)
        
    yield
    
    incident_path = get_incident_path()
    if os.path.exists(incident_path):
        shutil.rmtree(incident_path)

@pytest.fixture
def temp_active_state(tmp_path):
    temp_file = tmp_path / "active_state.json"
    default_state = {
        "project_id": "test-project",
        "incident_id": INCIDENT_ID,
        "incident_status": "ACTIVE"
    }
    with open(temp_file, "w") as f:
        json.dump(default_state, f)
    
    with patch("src.server.ACTIVE_STATE_FILE", str(temp_file)):
        yield temp_file

@patch("urllib.request.urlopen")
@patch("urllib.request.Request")
def test_telegram_bot_pending_command(mock_request, mock_urlopen, temp_active_state):
    os.environ["TELEGRAM_BOT_TOKEN"] = "mock-bot-token"
    os.environ["TELEGRAM_CHAT_ID"] = "123456"
    os.environ["TESTING_BOT"] = "true"
    
    # Clear the queue first
    incident_path = get_incident_path()
    pending_path = os.path.join(incident_path, "pending_approvals.json")
    if os.path.exists(pending_path):
        os.remove(pending_path)
        
    # Add a pending mutation
    add_pending_mutation(
        INCIDENT_ID,
        "kubectl restart deployment frontend",
        "HIGH",
        "Restarting deployment might cause temporary outage",
        "Clears memory leak"
    )
    
    # Mock /pending command message from operator
    mock_updates_resp = MagicMock()
    mock_updates_resp.status = 200
    mock_updates_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 3001,
                "message": {
                    "chat": {"id": 123456},
                    "text": "/pending"
                }
            }
        ]
    }).encode("utf-8")
    
    mock_urlopen.return_value.__enter__.return_value = mock_updates_resp
    
    # Capture sent Telegram messages
    sent_messages = []
    def mock_send_raw(token, chat_id, text):
        sent_messages.append(text)
    
    sent_keyboards = []
    def mock_send_inline(token, chat_id, text, buttons):
        sent_keyboards.append((text, buttons))
        
    with patch("src.server.send_raw_telegram_message", mock_send_raw), \
         patch("src.server.send_telegram_inline_keyboard", mock_send_inline):
        start_telegram_bot()
        
    # Assert formatting & presence of indicator emojis
    assert any("Pending SRE Mutation Actions Queue" in msg for msg in sent_messages)
    assert any("kubectl restart deployment frontend" in kb[0] for kb in sent_keyboards)
    assert any("🟠 HIGH" in kb[0] for kb in sent_keyboards)
    
    # Check buttons were created
    buttons = sent_keyboards[0][1][0]
    assert buttons[0]["text"] == "💥 Approve"
    assert buttons[0]["callback_data"] == "approve_mutation:cmd-01"
    assert buttons[1]["text"] == "❌ Reject"
    assert buttons[1]["callback_data"] == "reject_mutation:cmd-01"

@patch("urllib.request.urlopen")
@patch("urllib.request.Request")
def test_telegram_bot_approve_callback_and_comment(mock_request, mock_urlopen, temp_active_state):
    os.environ["TELEGRAM_BOT_TOKEN"] = "mock-bot-token"
    os.environ["TELEGRAM_CHAT_ID"] = "123456"
    os.environ["TESTING_BOT"] = "true"
    
    # 1. Trigger Approve Callback
    mock_cb_resp = MagicMock()
    mock_cb_resp.status = 200
    mock_cb_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 3002,
                "callback_query": {
                    "id": "cb_123",
                    "message": {
                        "chat": {"id": 123456},
                        "message_id": 888
                    },
                    "data": "approve_mutation:cmd-01"
                }
            }
        ]
    }).encode("utf-8")
    
    mock_urlopen.return_value.__enter__.return_value = mock_cb_resp
    
    from src.server import session_states
    session_states.clear()
    
    start_telegram_bot()
    
    # Session state should set awaiting comment
    assert session_states["123456"]["state"] == "AWAITING_MUTATION_COMMENT"
    assert session_states["123456"]["cmd_id"] == "cmd-01"
    assert session_states["123456"]["action"] == "approve"
    
    # 2. Operator replies with comment
    mock_reply_resp = MagicMock()
    mock_reply_resp.status = 200
    mock_reply_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 3003,
                "message": {
                    "chat": {"id": 123456},
                    "text": "Approving for memory release"
                }
            }
        ]
    }).encode("utf-8")
    
    mock_urlopen.return_value.__enter__.return_value = mock_reply_resp
    
    with patch("src.server.approve_pending_mutation", return_value=True) as mock_approve:
        start_telegram_bot()
        mock_approve.assert_called_once_with(INCIDENT_ID, "cmd-01", "Approving for memory release")
        
    assert "123456" not in session_states
