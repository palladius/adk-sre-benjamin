import os
import json
import pytest
from unittest.mock import patch, MagicMock
from src.declaration import parse_declaration_intent, get_projects_list
from src.server import start_telegram_bot, get_active_state, save_active_state

def test_get_projects_list():
    with patch("os.path.exists", return_value=True), \
         patch("os.path.isdir", return_value=True), \
         patch("os.listdir", return_value=["sre-next", "sre-demo"]):
        projects = get_projects_list()
        assert "sre-next" in projects
        assert "sre-demo" in projects

@patch("src.declaration.get_projects_list", return_value=["sre-next", "sre-demo"])
def test_parse_declaration_intent_heuristics_mock(mock_get_projects):
    # Test when MOCK_TOOLING is true or no API key
    with patch.dict(os.environ, {"MOCK_TOOLING": "true", "GEMINI_API_KEY": ""}):
        # Valid declaration with exact project ID
        res = parse_declaration_intent("declare incident GKE cluster down in sre-next")
        assert res["is_incident_declaration"] is True
        assert res["event_type"] == "gke_cluster_down"
        assert res["project_id"] == "sre-next"
        assert "GKE cluster down" in res["description"]

        # Valid declaration with fuzzy/unknown project ID
        res = parse_declaration_intent("create incident latency high in some-other-project")
        assert res["is_incident_declaration"] is True
        assert res["event_type"] == "latency_high"
        assert res["project_id"] is None

        # Slash command /newincident
        res = parse_declaration_intent("/newincident SQL instance crashed in sre-demo")
        assert res["is_incident_declaration"] is True
        assert res["event_type"] == "sql_instance_down"
        assert res["project_id"] == "sre-demo"

        # Not an incident declaration
        res = parse_declaration_intent("just checking CPU usage")
        assert res["is_incident_declaration"] is False

@patch("src.declaration.get_projects_list", return_value=["sre-next", "sre-demo"])
@patch("urllib.request.urlopen")
@patch("urllib.request.Request")
def test_parse_declaration_intent_live_mock(mock_request, mock_urlopen, mock_get_projects):
    # Test when MOCK_TOOLING is false and API key is set
    with patch.dict(os.environ, {"MOCK_TOOLING": "false", "GEMINI_API_KEY": "fake-key"}):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps({
                                    "is_incident_declaration": True,
                                    "event_type": "gke_cluster_down",
                                    "project_id": "sre-next",
                                    "description": "GKE cluster down in us-central1"
                                })
                            }
                        ]
                    }
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = parse_declaration_intent("declare incident GKE cluster down in sre-next")
        assert res["is_incident_declaration"] is True
        assert res["event_type"] == "gke_cluster_down"
        assert res["project_id"] == "sre-next"
        assert res["description"] == "GKE cluster down in us-central1"

@pytest.fixture
def temp_active_state(tmp_path):
    temp_file = tmp_path / "active_state.json"
    default_state = {
        "project_id": "sre-next",
        "incident_id": "None",
        "incident_status": "UNKNOWN"
    }
    with open(temp_file, "w") as f:
        json.dump(default_state, f)
    with patch("src.server.ACTIVE_STATE_FILE", str(temp_file)):
        yield temp_file

@patch("src.server.run_incident_flow", return_value=("INC-MOCK-123", "investigations/INC-MOCK-123"))
@patch("src.server.get_discovered_projects", return_value=["sre-next", "sre-demo"])
@patch("urllib.request.urlopen")
@patch("urllib.request.Request")
def test_telegram_new_incident_command_with_desc(mock_req, mock_urlopen, mock_projects, mock_run_flow, temp_active_state):
    os.environ["TELEGRAM_BOT_TOKEN"] = "mock-bot-token"
    os.environ["TELEGRAM_CHAT_ID"] = "123456"
    os.environ["TESTING_BOT"] = "true"

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 2001,
                "message": {
                    "chat": {"id": 123456},
                    "text": "/newincident GKE down in sre-next"
                }
            }
        ]
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    start_telegram_bot()

    mock_run_flow.assert_called_once()
    payload = mock_run_flow.call_args[0][0]
    assert payload["project_id"] == "sre-next"
    assert payload["event_type"] == "gke_cluster_down"

    state = get_active_state()
    assert state["incident_id"] == "INC-MOCK-123"
    assert state["project_id"] == "sre-next"

@patch("src.server.run_incident_flow", return_value=("INC-MOCK-123", "investigations/INC-MOCK-123"))
@patch("src.server.get_discovered_projects", return_value=["sre-next", "sre-demo"])
@patch("urllib.request.urlopen")
@patch("urllib.request.Request")
def test_telegram_new_incident_command_no_desc(mock_req, mock_urlopen, mock_projects, mock_run_flow, temp_active_state):
    os.environ["TELEGRAM_BOT_TOKEN"] = "mock-bot-token"
    os.environ["TELEGRAM_CHAT_ID"] = "123456"
    os.environ["TESTING_BOT"] = "true"

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 2002,
                "message": {
                    "chat": {"id": 123456},
                    "text": "/newincident"
                }
            }
        ]
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    from src.server import session_states
    session_states.clear()

    start_telegram_bot()

    assert session_states["123456"]["state"] == "AWAITING_DESCRIPTION"
    mock_run_flow.assert_not_called()

@patch("src.server.run_incident_flow", return_value=("INC-MOCK-123", "investigations/INC-MOCK-123"))
@patch("src.server.get_discovered_projects", return_value=["sre-next", "sre-demo"])
@patch("urllib.request.urlopen")
@patch("urllib.request.Request")
def test_telegram_new_incident_awaiting_desc(mock_req, mock_urlopen, mock_projects, mock_run_flow, temp_active_state):
    os.environ["TELEGRAM_BOT_TOKEN"] = "mock-bot-token"
    os.environ["TELEGRAM_CHAT_ID"] = "123456"
    os.environ["TESTING_BOT"] = "true"

    from src.server import session_states
    session_states["123456"] = {"state": "AWAITING_DESCRIPTION"}

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 2003,
                "message": {
                    "chat": {"id": 123456},
                    "text": "GKE cluster down in sre-next"
                }
            }
        ]
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    start_telegram_bot()

    assert "123456" not in session_states or session_states["123456"].get("state") is None
    mock_run_flow.assert_called_once()
    payload = mock_run_flow.call_args[0][0]
    assert payload["project_id"] == "sre-next"
    assert payload["event_type"] == "gke_cluster_down"

@patch("src.server.run_incident_flow", return_value=("INC-MOCK-123", "investigations/INC-MOCK-123"))
@patch("src.server.get_discovered_projects", return_value=["sre-next", "sre-demo"])
@patch("urllib.request.urlopen")
@patch("urllib.request.Request")
def test_telegram_project_resolution_fuzzy(mock_req, mock_urlopen, mock_projects, mock_run_flow, temp_active_state):
    os.environ["TELEGRAM_BOT_TOKEN"] = "mock-bot-token"
    os.environ["TELEGRAM_CHAT_ID"] = "123456"
    os.environ["TESTING_BOT"] = "true"

    from src.server import session_states
    session_states.clear()

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 2004,
                "message": {
                    "chat": {"id": 123456},
                    "text": "/newincident latency high in fuzzy-project"
                }
            }
        ]
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    start_telegram_bot()

    mock_run_flow.assert_not_called()
    assert session_states["123456"]["state"] == "AWAITING_PROJECT_RESOLUTION"
    assert session_states["123456"]["event_type"] == "latency_high"

    # Now simulate the callback query selecting "sre-demo"
    mock_cb_resp = MagicMock()
    mock_cb_resp.status = 200
    mock_cb_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 2005,
                "callback_query": {
                    "id": "cb_query_456",
                    "message": {
                        "chat": {"id": 123456},
                        "message_id": 1001
                    },
                    "data": "resolve_project:sre-demo"
                }
            }
        ]
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_cb_resp

    start_telegram_bot()

    mock_run_flow.assert_called_once()
    payload = mock_run_flow.call_args[0][0]
    assert payload["project_id"] == "sre-demo"
    assert payload["event_type"] == "latency_high"
    assert "123456" not in session_states or session_states["123456"].get("state") is None
