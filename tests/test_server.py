import os
import json
import pytest
import threading
import urllib.request
import urllib.error
from http.server import HTTPServer
from unittest.mock import MagicMock, patch
from src.server import parse_incident_folder, SREHttpRequestHandler

def test_parse_incident_folder(tmp_path):
    # Set up mock incident folder structure
    inc_dir = tmp_path / "INC-20260601-test"
    inc_dir.mkdir()
    
    # Write a mock state.md
    state_file = inc_dir / "state.md"
    state_file.write_text("""# Active SRE Incident State: INC-20260601-test
## Metadata
- **Status:** RESOLVED
- **Target Project:** `prod-db-999`
- **Trigger Event:** `frontend_latency_slo_violated`
- **Incident Commander:** Benjamin
- **Safety Level:** LOW Risk
""")
    
    # Write a mock timeline.md
    timeline_file = inc_dir / "timeline.md"
    timeline_file.write_text("""- **[2026-06-01T07:55:00Z]** [Incident Commander Benjamin] Alert received.
- **[2026-06-01T07:55:05Z]** [Operations Lead] Initiating metrics diagnostic collection.
""")
    
    # Write a mock artifacts_registry.json
    registry_file = inc_dir / "artifacts_registry.json"
    registry_file.write_text(json.dumps([
        {"file_path": "artifacts/metrics.csv", "source_type": "MCP"}
    ]))
    
    parsed = parse_incident_folder(str(inc_dir))
    
    assert parsed["incident_id"] == "INC-20260601-test"
    assert parsed["status"] == "RESOLVED"
    assert parsed["project_id"] == "prod-db-999"
    assert parsed["trigger_event"] == "frontend_latency_slo_violated"
    assert len(parsed["timeline"]) == 2
    assert parsed["timeline"][0]["agent"] == "Incident Commander Benjamin"
    assert "Alert received" in parsed["timeline"][0]["message"]
    assert len(parsed["artifacts"]) == 1
    assert parsed["artifacts"][0]["source_type"] == "MCP"

def test_server_integration():
    # Start the server on a free port
    server = HTTPServer(('localhost', 0), SREHttpRequestHandler)
    port = server.server_port
    
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    try:
        # Test GET /api/incidents
        url_list = f"http://localhost:{port}/api/incidents"
        req = urllib.request.Request(url_list)
        with urllib.request.urlopen(req) as response:
            assert response.status == 200
            data = json.loads(response.read().decode('utf-8'))
            assert isinstance(data, list)
            
        # Test GET /api/incidents/invalid-id-123 (should return 404)
        url_single = f"http://localhost:{port}/api/incidents/invalid-id-123"
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(url_single)
        assert exc_info.value.code == 404
        
        # Test OPTIONS request
        url_options = f"http://localhost:{port}/api/incidents"
        req_opt = urllib.request.Request(url_options, method="OPTIONS")
        with urllib.request.urlopen(req_opt) as resp_opt:
            assert resp_opt.status == 200
            assert resp_opt.headers.get("Access-Control-Allow-Origin") == "*"
            
        # Test GET /api/config
        url_config = f"http://localhost:{port}/api/config"
        req_config = urllib.request.Request(url_config)
        with urllib.request.urlopen(req_config) as resp_config:
            assert resp_config.status == 200
            data_config = json.loads(resp_config.read().decode('utf-8'))
            assert "project_id" in data_config

        # Test POST /api/incidents/INC-MOCK-123/approve (mocked)
        with patch("src.server.resume_simulation") as mock_resume, \
             patch("src.server.parse_incident_folder") as mock_parse, \
             patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            mock_parse.return_value = {"incident_id": "INC-MOCK-123", "status": "CLOSED"}
            url_approve = f"http://localhost:{port}/api/incidents/INC-MOCK-123/approve"
            req_approve = urllib.request.Request(url_approve, data=b"", method="POST")
            with urllib.request.urlopen(req_approve) as resp_approve:
                assert resp_approve.status == 200
                data_approve = json.loads(resp_approve.read().decode('utf-8'))
                assert data_approve["status"] == "CLOSED"
                mock_resume.assert_called_once_with("INC-MOCK-123", approved=True)

        # Test POST /api/incidents/INC-MOCK-123/reject (mocked)
        with patch("src.server.resume_simulation") as mock_resume, \
             patch("src.server.parse_incident_folder") as mock_parse, \
             patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            mock_parse.return_value = {"incident_id": "INC-MOCK-123", "status": "ABORTED"}
            url_reject = f"http://localhost:{port}/api/incidents/INC-MOCK-123/reject"
            req_reject = urllib.request.Request(url_reject, data=b"", method="POST")
            with urllib.request.urlopen(req_reject) as resp_reject:
                assert resp_reject.status == 200
                data_reject = json.loads(resp_reject.read().decode('utf-8'))
                assert data_reject["status"] == "ABORTED"
                mock_resume.assert_called_once_with("INC-MOCK-123", approved=False)
            
        # Test GET /api/incidents/INC-MOCK-123/chat (mocked)
        with patch("os.path.exists") as mock_exists, \
             patch("src.server.parse_incident_folder") as mock_parse:
            mock_exists.side_effect = lambda p: not p.endswith("chat.json")
            mock_parse.return_value = {"trigger_event": "frontend_latency_slo_violated", "project_id": "sre-next"}
            url_chat_get = f"http://localhost:{port}/api/incidents/INC-MOCK-123/chat"
            req_chat_get = urllib.request.Request(url_chat_get)
            with urllib.request.urlopen(req_chat_get) as resp_chat_get:
                assert resp_chat_get.status == 200
                data_chat_get = json.loads(resp_chat_get.read().decode('utf-8'))
                assert isinstance(data_chat_get, list)
                assert len(data_chat_get) > 0
                assert "Benjamin" in data_chat_get[0]["sender"]

        # Test POST /api/incidents/INC-MOCK-123/chat (mocked)
        with patch("os.path.exists") as mock_exists, \
             patch("src.server.parse_incident_folder") as mock_parse, \
             patch("builtins.open", MagicMock()):
            mock_exists.side_effect = lambda p: not p.endswith("chat.json")
            mock_parse.return_value = {"status": "AWAITING_APPROVAL", "trigger_event": "frontend_latency_slo_violated", "project_id": "sre-next"}
            url_chat_post = f"http://localhost:{port}/api/incidents/INC-MOCK-123/chat"
            payload_chat = json.dumps({"message": "Hello Benjamin"}).encode("utf-8")
            req_chat_post = urllib.request.Request(url_chat_post, data=payload_chat, method="POST")
            with urllib.request.urlopen(req_chat_post) as resp_chat_post:
                assert resp_chat_post.status == 200
                data_chat_post = json.loads(resp_chat_post.read().decode('utf-8'))
                assert isinstance(data_chat_post, list)
                assert len(data_chat_post) >= 3
                assert data_chat_post[-2]["sender"] == "Operator (You)"
                assert data_chat_post[-2]["message"] == "Hello Benjamin"
            
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join()
