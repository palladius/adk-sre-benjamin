import os
import json
import shutil
from io import BytesIO
from unittest.mock import patch, MagicMock
import pytest

import src.db as db
from src.storage import (
    DatabaseStateManager,
    FileStateManager,
    get_state_manager,
    set_state_manager,
)
from src.incident import get_investigations_dir, IncidentStatus
from src.server import (
    SREHttpRequestHandler,
    get_active_state,
    save_active_state,
    set_active_incident,
    set_active_project,
    get_incidents_list,
    start_telegram_bot,
)


@pytest.fixture(autouse=True)
def reset_state_manager():
    set_state_manager(None)
    yield
    set_state_manager(None)


def _make_handler(method: str, path: str, payload: dict = None):
    handler = SREHttpRequestHandler.__new__(SREHttpRequestHandler)
    handler.path = path
    if payload is not None:
        raw = json.dumps(payload).encode("utf-8")
        handler.headers = {"Content-Length": str(len(raw))}
        handler.rfile = BytesIO(raw)
    else:
        handler.headers = {"Content-Length": "0"}
        handler.rfile = BytesIO(b"")
    handler.wfile = BytesIO()
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    return handler


def test_database_state_manager_single_write_and_outage_fallback(tmp_path):
    state_file = tmp_path / "active_state.json"
    fallback = FileStateManager(state_file_path_resolver=lambda: str(state_file))
    mgr = DatabaseStateManager(fallback_manager=fallback)

    # 1. When DB is inactive, reads and writes fall back to FileStateManager
    assert not db.is_db_active()
    state = mgr.get_active_state()
    assert state["incident_status"] == IncidentStatus.NEW.value

    state["incident_id"] = "INC-REAL-1"
    state["project_id"] = "real-proj"
    state["incident_status"] = IncidentStatus.ONGOING.value
    mgr.save_active_state(state)
    assert state_file.exists()

    reloaded = mgr.get_active_state()
    assert reloaded["incident_id"] == "INC-REAL-1"

    # 2. When DB is active, save_active_state writes to DB exactly ONCE (no double write via FileStateManager)
    mock_db_state = {
        "project_id": "cloud-proj",
        "incident_id": "INC-DB-123",
        "incident_status": IncidentStatus.CLOSED.value,
        "substatus_rca": True,
        "substatus_mitigated": True,
        "substatus_fixed": True,
        "substatus_verified": True,
    }
    with patch("src.db.is_db_active", return_value=True), \
         patch("src.db.get_active_state", return_value=mock_db_state) as mock_get, \
         patch("src.db.save_active_state", return_value=True) as mock_save:
        state_from_db = mgr.get_active_state()
        assert state_from_db["project_id"] == "cloud-proj"
        assert state_from_db["incident_id"] == "INC-DB-123"
        assert mock_get.call_count == 1

        mgr.save_active_state(state_from_db)
        assert mock_save.call_count == 1

    # 3. Transient DB outage during get_active_state falls back to FileStateManager instead of wiping state to None
    with patch("src.db.is_db_active", return_value=True), \
         patch("src.db.get_active_state", side_effect=RuntimeError("connection reset by peer")):
        recovered = mgr.get_active_state()
        assert recovered["incident_id"] == "INC-DB-123"
        assert recovered["project_id"] == "cloud-proj"


def test_storage_backend_local_never_calls_db(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND_STATE", "local")
    set_state_manager(None)
    temp_state_file = tmp_path / "active_state.json"

    with patch("src.server.get_active_state_file", return_value=str(temp_state_file)), \
         patch("src.db.is_db_active", return_value=True), \
         patch("src.db.get_active_state") as mock_db_get, \
         patch("src.db.save_active_state") as mock_db_save:
        mgr = get_state_manager()
        assert isinstance(mgr, FileStateManager)

        st = mgr.get_active_state()
        st["project_id"] = "strictly-local-proj"
        mgr.save_active_state(st)

        assert mock_db_get.call_count == 0
        assert mock_db_save.call_count == 0
        assert json.loads(temp_state_file.read_text())["project_id"] == "strictly-local-proj"


def test_path_traversal_and_reserved_filenames_rejected(tmp_path, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    temp_state_file = tmp_path / "active_state.json"

    with patch("src.server.get_active_state_file", return_value=str(temp_state_file)), \
         patch("src.server.ACTIVE_STATE_FILE", str(temp_state_file)):
        for bad_id in ("../../escaped", "../outside", "active_state.json", "state.md"):
            handler = _make_handler("POST", "/api/active-state", {"incident_id": bad_id})
            handler.do_POST()
            handler.send_response.assert_called_with(400)
            assert not os.path.exists(os.path.join(get_investigations_dir(), bad_id, "artifacts"))
            assert not os.path.exists("escaped")

            sel_handler = _make_handler("POST", f"/api/incidents/{bad_id}/select")
            sel_handler.do_POST()
            sel_handler.send_response.assert_called_with(400)


def test_phantom_incident_rejected_and_creates_no_directory(tmp_path, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    temp_state_file = tmp_path / "active_state.json"
    ghost_dir = os.path.join(get_investigations_dir(), "INC-GHOST-404")
    if os.path.exists(ghost_dir):
        shutil.rmtree(ghost_dir)

    with patch("src.server.get_active_state_file", return_value=str(temp_state_file)), \
         patch("src.server.ACTIVE_STATE_FILE", str(temp_state_file)):
        handler = _make_handler("POST", "/api/active-state", {"incident_id": "INC-GHOST-404"})
        handler.do_POST()
        handler.send_response.assert_called_with(404)
        assert not os.path.exists(ghost_dir)
        assert all(i["id"] != "INC-GHOST-404" for i in get_incidents_list())

        sel_handler = _make_handler("POST", "/api/incidents/INC-GHOST-404/select")
        sel_handler.do_POST()
        sel_handler.send_response.assert_called_with(404)
        assert not os.path.exists(ghost_dir)


def test_archived_incident_cannot_be_activated(tmp_path):
    inc_dir = os.path.join(get_investigations_dir(), "INC-ARCHIVED-TEST")
    os.makedirs(inc_dir, exist_ok=True)
    temp_state_file = tmp_path / "active_state.json"
    try:
        with open(os.path.join(inc_dir, "state.md"), "w") as f:
            f.write(
                "# Active SRE Incident State: INC-ARCHIVED-TEST\n"
                "## Metadata\n"
                "- **Status:** CLOSED\n"
                "- **Target Project:** `proj-arch`\n"
                "- **Archived:** true\n"
            )
        with patch("src.server.get_active_state_file", return_value=str(temp_state_file)), \
             patch("src.server.ACTIVE_STATE_FILE", str(temp_state_file)):
            handler = _make_handler("POST", "/api/incidents/INC-ARCHIVED-TEST/select")
            handler.do_POST()
            handler.send_response.assert_called_with(400)
            body = json.loads(handler.wfile.getvalue().decode("utf-8"))
            assert "archived" in body["error"].lower()
    finally:
        if os.path.exists(inc_dir):
            shutil.rmtree(inc_dir)


def test_stateless_cloud_run_selects_and_reads_db_only_incident(tmp_path):
    """Verifies that on a fresh Cloud Run instance (no local folder in investigations/),
    an incident stored in Cloud SQL can be listed, viewed, chatted with, and selected via HTTP & Telegram.
    """
    temp_state_file = tmp_path / "active_state.json"
    db_only_id = "INC-CLOUD-DB-ONLY"
    local_folder = os.path.join(get_investigations_dir(), db_only_id)
    if os.path.exists(local_folder):
        shutil.rmtree(local_folder)

    db_incident_record = {
        "incident_id": db_only_id,
        "status": "ONGOING",
        "substatus_rca": True,
        "substatus_mitigated": False,
        "substatus_fixed": False,
        "substatus_verified": False,
        "project_id": "cloud-sql-prod-1",
        "domain_id": "sre-demo-prod",
        "trigger_event": "cloudsql_connection_pool_exhausted",
        "incident_uuid": "uuid-cloud-123",
        "archived": False,
        "timeline": [{"timestamp": "2026-11-11T10:00:00Z", "agent": "Incident Commander", "message": "Triaging DB pool"}],
        "artifacts": [],
    }

    with patch("src.server.get_active_state_file", return_value=str(temp_state_file)), \
         patch("src.server.ACTIVE_STATE_FILE", str(temp_state_file)), \
         patch("src.db.is_db_active", return_value=True), \
         patch("src.db.get_incident", side_effect=lambda iid: dict(db_incident_record) if iid == db_only_id else None), \
         patch("src.db.list_incidents", return_value=[{"id": db_only_id, "status": "ONGOING", "project_id": "cloud-sql-prod-1", "trigger_event": "cloudsql_connection_pool_exhausted", "archived": False}]), \
         patch("src.db.get_active_state", return_value=None), \
         patch("src.db.save_active_state", return_value=True), \
         patch("src.comms_telegram.send_telegram_alert") as mock_tg:
        # 1. GET /api/incidents/<id> succeeds without a local folder
        get_handler = _make_handler("GET", f"/api/incidents/{db_only_id}")
        get_handler.do_GET()
        get_handler.send_response.assert_called_with(200)
        inc_detail = json.loads(get_handler.wfile.getvalue().decode("utf-8"))
        assert inc_detail["incident_id"] == db_only_id
        assert inc_detail["project_id"] == "cloud-sql-prod-1"

        # 2. POST /api/incidents/<id>/select succeeds without a local folder and maps project_id
        sel_handler = _make_handler("POST", f"/api/incidents/{db_only_id}/select")
        sel_handler.do_POST()
        sel_handler.send_response.assert_called_with(200)
        sel_state = json.loads(sel_handler.wfile.getvalue().decode("utf-8"))
        assert sel_state["incident_id"] == db_only_id
        assert sel_state["project_id"] == "cloud-sql-prod-1"
        assert sel_state["incident_status"] == "ONGOING"
        assert mock_tg.call_count == 1
        assert not os.path.exists(local_folder)


def test_q2_q3_q4_project_and_incident_transitions(tmp_path):
    inc_known_dir = os.path.join(get_investigations_dir(), "INC-KNOWN-PROJ")
    inc_unknown_dir = os.path.join(get_investigations_dir(), "INC-UNKNOWN-PROJ")
    os.makedirs(inc_known_dir, exist_ok=True)
    os.makedirs(inc_unknown_dir, exist_ok=True)
    temp_state_file = tmp_path / "active_state.json"

    try:
        with open(os.path.join(inc_known_dir, "state.md"), "w") as f:
            f.write(
                "# Active SRE Incident State: INC-KNOWN-PROJ\n"
                "## Metadata\n"
                "- **Status:** ONGOING\n"
                "- **Target Project:** `alpha-project`\n"
                "- **Trigger Event:** `cpu_high`\n"
            )
        with open(os.path.join(inc_unknown_dir, "state.md"), "w") as f:
            f.write(
                "# Active SRE Incident State: INC-UNKNOWN-PROJ\n"
                "## Metadata\n"
                "- **Status:** NEW\n"
                "- **Target Project:** `UNKNOWN`\n"
                "- **Trigger Event:** `mystery_alert`\n"
            )

        with patch("src.server.get_active_state_file", return_value=str(temp_state_file)), \
             patch("src.server.ACTIVE_STATE_FILE", str(temp_state_file)), \
             patch("src.comms_telegram.send_telegram_alert") as mock_tg:
            # Q3: Selecting INC-KNOWN-PROJ forces project_id to alpha-project even if caller passes explicit_project_id
            st1 = set_active_incident("INC-KNOWN-PROJ", source="Test", explicit_project_id="ignored-override")
            assert st1["incident_id"] == "INC-KNOWN-PROJ"
            assert st1["project_id"] == "alpha-project"
            assert mock_tg.call_count == 1

            # Q4: Re-selecting the already active incident does NOT spam a duplicate Telegram notification
            st1_repeat = set_active_incident("INC-KNOWN-PROJ", source="Test")
            assert st1_repeat["incident_id"] == "INC-KNOWN-PROJ"
            assert mock_tg.call_count == 1

            # Q3: Selecting INC-UNKNOWN-PROJ preserves current project_id (alpha-project) unless explicit_project_id is given
            st2 = set_active_incident("INC-UNKNOWN-PROJ", source="Test")
            assert st2["incident_id"] == "INC-UNKNOWN-PROJ"
            assert st2["project_id"] == "alpha-project"
            assert mock_tg.call_count == 2

            st2_override = set_active_incident("INC-UNKNOWN-PROJ", source="Test", explicit_project_id="custom-beta")
            assert st2_override["project_id"] == "custom-beta"

            # Q2: Selecting a different project when INC-KNOWN-PROJ is active clears incident_id to "None"
            set_active_incident("INC-KNOWN-PROJ", source="Test")
            st3 = set_active_project("gamma-project", source="Test")
            assert st3["project_id"] == "gamma-project"
            assert st3["incident_id"] == "None"
            assert st3["incident_status"] == IncidentStatus.NEW.value
    finally:
        for d in (inc_known_dir, inc_unknown_dir):
            if os.path.exists(d):
                shutil.rmtree(d)


@patch("urllib.request.urlopen")
@patch("urllib.request.Request")
def test_telegram_status_idle_and_unknown_status_warning(mock_request, mock_urlopen, tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock-bot-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456")
    monkeypatch.setenv("TESTING_BOT", "true")

    temp_file = tmp_path / "active_state.json"
    with open(temp_file, "w") as f:
        json.dump(
            {"project_id": "prod-ecom-99", "incident_id": "None", "incident_status": IncidentStatus.NEW.value},
            f,
        )

    mock_updates_resp = MagicMock()
    mock_updates_resp.status = 200
    mock_updates_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 3001,
                "message": {
                    "chat": {"id": 123456},
                    "text": "🚨 Status Check",
                },
            }
        ],
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_updates_resp

    # 1. Idle with no incidents -> All clear
    with patch("src.server.get_active_state_file", return_value=str(temp_file)), \
         patch("src.server.ACTIVE_STATE_FILE", str(temp_file)), \
         patch("src.server.get_incidents_list", return_value=[]), \
         patch("src.server.send_raw_telegram_message") as mock_send_msg:
        start_telegram_bot()

        assert mock_send_msg.call_count == 1
        sent_message = mock_send_msg.call_args[0][2]
        assert "Project Benjamin SRE Status" in sent_message
        assert "Target Project:* `prod-ecom-99`" in sent_message
        assert "Active Incident Context:* `None (Idle)`" in sent_message
        assert "No active incidents on fire" in sent_message

    # 2. Incident with UNKNOWN status -> surfaces warning instead of "All clear"
    with open(temp_file, "w") as f:
        json.dump(
            {"project_id": "prod-ecom-99", "incident_id": "INC-MYSTERY-1", "incident_status": IncidentStatus.ONGOING.value},
            f,
        )
    with patch("src.server.get_active_state_file", return_value=str(temp_file)), \
         patch("src.server.ACTIVE_STATE_FILE", str(temp_file)), \
         patch("src.server.get_incidents_list", return_value=[{"id": "INC-MYSTERY-1", "status": "UNKNOWN", "archived": False}]), \
         patch("src.server.resolve_incident", return_value={"incident_id": "INC-MYSTERY-1", "status": "UNKNOWN", "project_id": "prod-ecom-99", "trigger_event": "unknown_err", "timeline": []}), \
         patch("src.server.send_raw_telegram_message") as mock_send_msg2:
        start_telegram_bot()

        assert mock_send_msg2.call_count == 1
        sent_message2 = mock_send_msg2.call_args[0][2]
        assert "UNKNOWN status" in sent_message2
        assert "All clear" not in sent_message2
