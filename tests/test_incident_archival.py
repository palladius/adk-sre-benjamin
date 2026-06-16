import os
import json
import shutil
import pytest
import threading
import urllib.request
import urllib.error
from http.server import HTTPServer
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from src.server import (
    parse_incident_folder,
    set_incident_archived,
    get_incident_date,
    auto_archive_incidents,
    SREHttpRequestHandler,
    get_active_state,
    save_active_state,
    start_telegram_bot
)

def create_mock_incident(tmp_path, incident_id, status, archived=None):
    inc_dir = tmp_path / incident_id
    inc_dir.mkdir()
    state_file = inc_dir / "state.md"
    archived_line = f"\n- **Archived:** {str(archived).lower()}" if archived is not None else ""
    state_file.write_text(f"""# Active SRE Incident State: {incident_id}
## Metadata
- **Status:** {status}
- **Target Project:** `prod-db-999`
- **Trigger Event:** `frontend_latency_slo_violated`{archived_line}
""")
    # Touch timeline and registry
    (inc_dir / "timeline.md").write_text("- **[timestamp]** [System] Started")
    (inc_dir / "artifacts_registry.json").write_text("[]")
    return inc_dir

def test_archived_parsing(tmp_path):
    # Test unarchived default
    inc_dir = create_mock_incident(tmp_path, "INC-20260601-aaaa", "CLOSED")
    parsed = parse_incident_folder(str(inc_dir))
    assert parsed["archived"] is False

    # Test archived true
    inc_dir2 = create_mock_incident(tmp_path, "INC-20260601-bbbb", "CLOSED", archived=True)
    parsed2 = parse_incident_folder(str(inc_dir2))
    assert parsed2["archived"] is True

    # Test setting archived status
    success = set_incident_archived(str(inc_dir), True)
    assert success is True
    parsed_after = parse_incident_folder(str(inc_dir))
    assert parsed_after["archived"] is True

def test_incident_date_extraction():
    assert get_incident_date("INC-20260602-abcd") == datetime(2026, 6, 2, tzinfo=timezone.utc)
    assert get_incident_date("INC-invalid-abcd") is None

def test_auto_archival_logic(tmp_path):
    # Mock investigations directory
    with patch("src.server.parse_incident_folder") as mock_parse, \
         patch("src.server.set_incident_archived") as mock_archive, \
         patch("os.path.exists") as mock_exists, \
         patch("os.path.isdir") as mock_isdir, \
         patch("os.listdir") as mock_listdir:
         
         mock_exists.return_value = True
         mock_isdir.return_value = True
         mock_listdir.return_value = [
             "INC-20260601-old",  # Older than 3 days
             "INC-20260615-new",  # Newer than 3 days
             "INC-20260601-notclosed"
         ]
         
         # Mocking parse results
         # Note: current date is 2026-06-16
         def parse_side_effect(folder_path):
             folder = os.path.basename(folder_path)
             if "old" in folder:
                 return {"status": "CLOSED", "archived": False}
             elif "new" in folder:
                 return {"status": "CLOSED", "archived": False}
             else:
                 return {"status": "ACTIVE", "archived": False}
                 
         mock_parse.side_effect = parse_side_effect
         
         # Call auto archival
         auto_archive_incidents()
         
         # Should archive the old closed incident only
         # We expect mock_archive to be called with: (os.path.join("investigations", "INC-20260601-old"), True)
         expected_call_path = os.path.join("investigations", "INC-20260601-old")
         mock_archive.assert_any_call(expected_call_path, True)
         assert mock_archive.call_count == 1

def test_server_endpoints():
    # Ensure investigations dir exists
    os.makedirs("investigations", exist_ok=True)
    inc_id = "INC-20260610-testarchive"
    inc_dir = os.path.join("investigations", inc_id)
    if os.path.exists(inc_dir):
        shutil.rmtree(inc_dir)
        
    os.makedirs(inc_dir)
    state_file = os.path.join(inc_dir, "state.md")
    with open(state_file, "w") as f:
        f.write(f"""# Active SRE Incident State: {inc_id}
## Metadata
- **Status:** CLOSED
- **Target Project:** `prod-db-999`
- **Trigger Event:** `frontend_latency_slo_violated`
""")
    # Touch timeline
    with open(os.path.join(inc_dir, "timeline.md"), "w") as f:
        f.write("- **[timestamp]** [System] Started")
    
    # Start the server on a free port
    server = HTTPServer(('localhost', 0), SREHttpRequestHandler)
    port = server.server_port
    
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    try:
        # 1. GET /api/incidents (without include_archived, should contain our incident because it is not archived)
        url_list = f"http://localhost:{port}/api/incidents"
        req = urllib.request.Request(url_list)
        with urllib.request.urlopen(req) as response:
            assert response.status == 200
            data = json.loads(response.read().decode('utf-8'))
            ids = [inc["incident_id"] for inc in data]
            assert inc_id in ids
            
        # 2. POST /api/incidents/<id>/archive
        url_archive = f"http://localhost:{port}/api/incidents/{inc_id}/archive"
        req_archive = urllib.request.Request(url_archive, data=b"", method="POST")
        with urllib.request.urlopen(req_archive) as response:
            assert response.status == 200
            res_data = json.loads(response.read().decode('utf-8'))
            assert res_data["status"] == "success"
            
        # Verify it is now marked archived in state.md
        parsed = parse_incident_folder(inc_dir)
        assert parsed["archived"] is True
        
        # 3. GET /api/incidents (without include_archived, should NOT contain our incident since it is archived)
        with urllib.request.urlopen(url_list) as response:
            assert response.status == 200
            data = json.loads(response.read().decode('utf-8'))
            ids = [inc["incident_id"] for inc in data]
            assert inc_id not in ids
            
        # 4. GET /api/incidents?include_archived=true (should contain our incident)
        url_list_archived = f"http://localhost:{port}/api/incidents?include_archived=true"
        with urllib.request.urlopen(url_list_archived) as response:
            assert response.status == 200
            data = json.loads(response.read().decode('utf-8'))
            ids = [inc["incident_id"] for inc in data]
            assert inc_id in ids

        # 5. DELETE /api/incidents/<id>
        url_delete = f"http://localhost:{port}/api/incidents/{inc_id}"
        req_delete = urllib.request.Request(url_delete, method="DELETE")
        with urllib.request.urlopen(req_delete) as response:
            assert response.status == 200
            res_data = json.loads(response.read().decode('utf-8'))
            assert res_data["status"] == "success"
            
        # Verify the folder is actually deleted
        assert not os.path.exists(inc_dir)
        
    finally:
        server.shutdown()
        server.server_close()
        if os.path.exists(inc_dir):
            shutil.rmtree(inc_dir)

@pytest.fixture
def temp_active_state(tmp_path):
    temp_file = tmp_path / "active_state.json"
    default_state = {
        "project_id": "sre-next-dev",
        "incident_id": "None",
        "incident_status": "UNKNOWN"
    }
    with open(temp_file, "w") as f:
        json.dump(default_state, f)
    
    with patch("src.server.ACTIVE_STATE_FILE", str(temp_file)):
        yield temp_file

@patch("urllib.request.urlopen")
@patch("urllib.request.Request")
def test_telegram_bot_archive_command(mock_request, mock_urlopen, temp_active_state):
    os.environ["TELEGRAM_BOT_TOKEN"] = "mock-bot-token"
    os.environ["TELEGRAM_CHAT_ID"] = "123456"
    os.environ["TESTING_BOT"] = "true"
    
    mock_updates_resp = MagicMock()
    mock_updates_resp.status = 200
    mock_updates_resp.read.return_value = json.dumps({
        "ok": True,
        "result": [
            {
                "update_id": 1008,
                "message": {
                    "chat": {"id": 123456},
                    "text": "/archive INC-ARCHIVE-CMD"
                }
            }
        ]
    }).encode("utf-8")
    
    mock_urlopen.return_value.__enter__.return_value = mock_updates_resp
    
    with patch("os.path.exists", return_value=True), \
         patch("src.server.set_incident_archived", return_value=True) as mock_archive_func, \
         patch("src.server.send_raw_telegram_message") as mock_send_msg:
        start_telegram_bot()
        
        mock_archive_func.assert_called_once_with(os.path.join("investigations", "INC-ARCHIVE-CMD"), True)
        mock_send_msg.assert_called_once_with("mock-bot-token", "123456", "✅ Incident `INC-ARCHIVE-CMD` has been successfully archived.")
