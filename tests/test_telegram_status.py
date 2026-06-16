import os
import json
import shutil
import pytest
from unittest.mock import patch, MagicMock
from src.server import start_telegram_bot
from src.incident import get_investigations_dir

@pytest.fixture
def mock_incident_folder():
    inc_dir = os.path.join(get_investigations_dir(), "INC-TELEGRAM-STATUS-TEST")
    if os.path.exists(inc_dir):
        shutil.rmtree(inc_dir)
    os.makedirs(inc_dir, exist_ok=True)
    state_file = os.path.join(inc_dir, "state.md")
    with open(state_file, "w") as f:
        f.write("""# Active SRE Incident State: INC-TELEGRAM-STATUS-TEST
## Metadata
- **Status:** ONGOING
- **RCA Found:** True
- **Mitigated:** False
- **Fixed:** True
- **Verified:** False
- **Target Project:** `prod-db-999`
- **Trigger Event:** `frontend_latency_slo_violated`
""")
    # Touch timeline
    timeline_file = os.path.join(inc_dir, "timeline.md")
    with open(timeline_file, "w") as f:
        f.write("- **[timestamp]** [System] Started")
        
    yield inc_dir
    
    if os.path.exists(inc_dir):
        shutil.rmtree(inc_dir)

@patch("urllib.request.urlopen")
@patch("urllib.request.Request")
def test_telegram_bot_status_check(mock_request, mock_urlopen, mock_incident_folder, tmp_path):
    os.environ["TELEGRAM_BOT_TOKEN"] = "mock-bot-token"
    os.environ["TELEGRAM_CHAT_ID"] = "123456"
    os.environ["TESTING_BOT"] = "true"
    
    # Mock active_state.json
    temp_file = tmp_path / "active_state.json"
    active_state = {
        "project_id": "prod-db-999",
        "incident_id": "INC-TELEGRAM-STATUS-TEST",
        "incident_status": "ONGOING"
    }
    with open(temp_file, "w") as f:
        json.dump(active_state, f)
        
    # Mock updates request
    mock_updates_resp = MagicMock()
    mock_updates_resp.status = 200
    mock_updates_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 2001,
                "message": {
                    "chat": {"id": 123456},
                    "text": "🚨 Status Check"
                }
            }
        ]
    }).encode("utf-8")
    
    mock_urlopen.return_value.__enter__.return_value = mock_updates_resp
    
    with patch("src.server.ACTIVE_STATE_FILE", str(temp_file)), \
         patch("src.server.send_raw_telegram_message") as mock_send_msg:
         
        start_telegram_bot()
        
        # Verify status message content
        assert mock_send_msg.call_count == 1
        sent_message = mock_send_msg.call_args[0][2]
        assert "Incident:* `INC-TELEGRAM-STATUS-TEST`" in sent_message
        assert "*Status:* `ONGOING`" in sent_message
        assert "RCA Found: `Yes`" in sent_message
        assert "Mitigated: `No`" in sent_message
        assert "Fixed: `Yes`" in sent_message
        assert "Verified: `No`" in sent_message
