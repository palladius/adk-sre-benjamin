import os
import json
import pytest
import threading
import urllib.request
import urllib.error
from http.server import HTTPServer
from unittest.mock import patch
from src.server import SREHttpRequestHandler

def test_active_state_api(tmp_path):
    # Setup temporary file path for the active state json
    temp_active_state_file = tmp_path / "active_state.json"
    
    # Start the server on a free port
    server = HTTPServer(('localhost', 0), SREHttpRequestHandler)
    port = server.server_port
    
    # Spin up server thread
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    
    # We patch ACTIVE_STATE_FILE inside src.server and clear/set os.environ to avoid test pollution
    with patch("src.server.ACTIVE_STATE_FILE", str(temp_active_state_file)), \
         patch.dict(os.environ, {"PROJECT_ID": "sre-next"}):
        server_thread.start()
        
        try:
            # 1. Test GET /api/active-state (should return defaults when file doesn't exist)
            url = f"http://localhost:{port}/api/active-state"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                assert response.status == 200
                data = json.loads(response.read().decode('utf-8'))
                assert data["project_id"] == "sre-next"
                assert data["incident_id"] == "None"
                assert data["incident_status"] == "NEW"
                assert data["substatus_rca"] is False
                
            # 2. Test POST /api/active-state (update values)
            payload = {
                "project_id": "sre-next-dev",
                "incident_id": "INC-20260603-abcd",
                "incident_status": "ONGOING",
                "substatus_rca": True
            }
            req_post = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                method="POST"
            )
            with urllib.request.urlopen(req_post) as response_post:
                assert response_post.status == 200
                data_post = json.loads(response_post.read().decode('utf-8'))
                assert data_post["project_id"] == "sre-next-dev"
                assert data_post["incident_id"] == "INC-20260603-abcd"
                assert data_post["incident_status"] == "ONGOING"
                assert data_post["substatus_rca"] is True
                
            # 3. Test GET /api/active-state again (to verify persistence)
            with urllib.request.urlopen(req) as response_get2:
                assert response_get2.status == 200
                data_get2 = json.loads(response_get2.read().decode('utf-8'))
                assert data_get2["project_id"] == "sre-next-dev"
                assert data_get2["incident_id"] == "INC-20260603-abcd"
                assert data_get2["incident_status"] == "ONGOING"
                assert data_get2["substatus_rca"] is True
                
            # 4. Verify temporary file was written
            assert temp_active_state_file.exists()
            with open(temp_active_state_file, "r") as f:
                saved_data = json.load(f)
                assert saved_data["project_id"] == "sre-next-dev"
                
        finally:
            server.shutdown()
            server.server_close()
            server_thread.join()
