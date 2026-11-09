import os
import json
import shutil
import pytest
from unittest.mock import patch, MagicMock
from http.server import HTTPServer

import src.db as db
from src.storage import DatabaseStateManager, FileStateManager, get_state_manager, set_state_manager
from src.incident import get_investigations_dir
from src.server import SREHttpRequestHandler, get_active_state, save_active_state, start_telegram_bot

@pytest.fixture
def clean_investigations():
    test_dir = get_investigations_dir()
    os.makedirs(test_dir, exist_ok=True)
    yield test_dir

def test_database_state_manager_with_db_and_fallback(tmp_path):
    state_file = tmp_path / "active_state.json"
    fallback = FileStateManager(state_file_path_resolver=lambda: str(state_file))
    mgr = DatabaseStateManager(fallback_manager=fallback)

    # When DB is inactive, reads and writes fall back to fallback manager
    assert not db.is_db_active()
    state = mgr.get_active_state()
    assert state["incident_status"] == "NEW"

    state["incident_id"] = "INC-FALLBACK-1"
    state["incident_status"] = "ONGOING"
    mgr.save_active_state(state)
    assert state_file.exists()

    reloaded = mgr.get_active_state()
    assert reloaded["incident_id"] == "INC-FALLBACK-1"

    # When DB is active, uses DB
    mock_db_state = {
        "project_id": "cloud-proj",
        "incident_id": "INC-DB-123",
        "incident_status": "CLOSED",
        "substatus_rca": True,
        "substatus_mitigated": True,
        "substatus_fixed": True,
        "substatus_verified": True
    }
    with patch("src.db.is_db_active", return_value=True), \
         patch("src.db.get_active_state", return_value=mock_db_state), \
         patch("src.db.save_active_state", return_value=True) as mock_save:
        state_from_db = mgr.get_active_state()
        assert state_from_db["project_id"] == "cloud-proj"
        assert state_from_db["incident_id"] == "INC-DB-123"

        mgr.save_active_state(state_from_db)
        assert mock_save.called

def test_get_state_manager_backend_toggle(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND_STATE", "db")
    set_state_manager(None)
    mgr = get_state_manager()
    assert isinstance(mgr, DatabaseStateManager)

    monkeypatch.setenv("STORAGE_BACKEND_STATE", "local")
    set_state_manager(None)
    mgr_local = get_state_manager()
    assert isinstance(mgr_local, FileStateManager)

def test_incident_to_project_mapping_on_active_state_post(tmp_path, monkeypatch):
    # Setup test incident with target project
    inc_dir = os.path.join(get_investigations_dir(), "INC-MAP-PROJECT-TEST")
    os.makedirs(inc_dir, exist_ok=True)
    state_file = os.path.join(inc_dir, "state.md")
    with open(state_file, "w") as f:
        f.write("""# Active SRE Incident State: INC-MAP-PROJECT-TEST
## Metadata
- **Status:** ONGOING
- **Target Project:** `target-cloud-prod-42`
- **Trigger Event:** `database_cpu_saturation`
""")

    temp_state_file = tmp_path / "active_state.json"
    with open(temp_state_file, "w") as f:
        json.dump({"project_id": "old-proj", "incident_id": "None", "incident_status": "NEW"}, f)

    with patch("src.server.get_active_state_file", return_value=str(temp_state_file)), \
         patch("src.server.ACTIVE_STATE_FILE", str(temp_state_file)), \
         patch("src.comms_telegram.send_telegram_alert") as mock_tg_alert:
        
        # Simulate POST /api/active-state selecting INC-MAP-PROJECT-TEST
        handler = SREHttpRequestHandler.__new__(SREHttpRequestHandler)
        handler.path = "/api/active-state"
        handler.headers = {"Content-Length": str(len(json.dumps({"incident_id": "INC-MAP-PROJECT-TEST"})))}
        
        from io import BytesIO
        handler.rfile = BytesIO(json.dumps({"incident_id": "INC-MAP-PROJECT-TEST"}).encode("utf-8"))
        handler.wfile = BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_POST()

        response_body = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert response_body["incident_id"] == "INC-MAP-PROJECT-TEST"
        assert response_body["project_id"] == "target-cloud-prod-42"
        assert response_body["incident_status"] == "ONGOING"
        assert mock_tg_alert.called
        assert "target-cloud-prod-42" in mock_tg_alert.call_args[0][0]

    if os.path.exists(inc_dir):
        shutil.rmtree(inc_dir)

def test_select_incident_endpoint(tmp_path):
    inc_dir = os.path.join(get_investigations_dir(), "INC-SELECT-ENDPOINT-TEST")
    os.makedirs(inc_dir, exist_ok=True)
    state_file = os.path.join(inc_dir, "state.md")
    with open(state_file, "w") as f:
        f.write("""# Active SRE Incident State: INC-SELECT-ENDPOINT-TEST
## Metadata
- **Status:** ONGOING
- **Target Project:** `sre-cluster-alpha`
- **Trigger Event:** `ingress_packet_loss`
""")

    temp_state_file = tmp_path / "active_state.json"
    with patch("src.server.get_active_state_file", return_value=str(temp_state_file)), \
         patch("src.server.ACTIVE_STATE_FILE", str(temp_state_file)), \
         patch("src.comms_telegram.send_telegram_alert") as mock_tg:
        
        handler = SREHttpRequestHandler.__new__(SREHttpRequestHandler)
        handler.path = "/api/incidents/INC-SELECT-ENDPOINT-TEST/select"
        handler.headers = {"Content-Length": "0"}
        handler.rfile = MagicMock()
        from io import BytesIO
        handler.wfile = BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_POST()

        res = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert res["incident_id"] == "INC-SELECT-ENDPOINT-TEST"
        assert res["project_id"] == "sre-cluster-alpha"
        assert mock_tg.called

    if os.path.exists(inc_dir):
        shutil.rmtree(inc_dir)

@patch("urllib.request.urlopen")
@patch("urllib.request.Request")
def test_telegram_status_idle_with_fire_status(mock_request, mock_urlopen, tmp_path):
    os.environ["TELEGRAM_BOT_TOKEN"] = "mock-bot-token"
    os.environ["TELEGRAM_CHAT_ID"] = "123456"
    os.environ["TESTING_BOT"] = "true"

    temp_file = tmp_path / "active_state.json"
    with open(temp_file, "w") as f:
        json.dump({"project_id": "prod-ecom-99", "incident_id": "None", "incident_status": "IDLE"}, f)

    mock_updates_resp = MagicMock()
    mock_updates_resp.status = 200
    mock_updates_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 3001,
                "message": {
                    "chat": {"id": 123456},
                    "text": "🚨 Status Check"
                }
            }
        ]
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_updates_resp

    with patch("src.server.ACTIVE_STATE_FILE", str(temp_file)), \
         patch("src.server.get_incidents_list", return_value=[]), \
         patch("src.server.send_raw_telegram_message") as mock_send_msg:
        start_telegram_bot()

        assert mock_send_msg.call_count == 1
        sent_message = mock_send_msg.call_args[0][2]
        assert "Project Benjamin SRE Status" in sent_message
        assert "Target Project:* `prod-ecom-99`" in sent_message
        assert "Active Incident Context:* `None (Idle)`" in sent_message
        assert "No active incidents on fire" in sent_message
