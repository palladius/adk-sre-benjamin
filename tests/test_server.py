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
            
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join()
