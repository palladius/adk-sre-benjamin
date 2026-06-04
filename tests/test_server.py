import os
import json
import pytest
import threading
import urllib.request
import urllib.error
from http.server import HTTPServer
from unittest.mock import MagicMock, patch, mock_open
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
             patch("src.server.open", mock_open()):
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
                
        # Test GET /api/projects/test-project-server/discover
        server_cache_dir = os.path.join("discover", "gcp-project", "test-project-server")
        json_file = os.path.join(server_cache_dir, "discover.json")
        md_file = os.path.join(server_cache_dir, "wiki.md")
        
        for fpath in [json_file, md_file]:
            if os.path.exists(fpath):
                os.remove(fpath)
            
        try:
            with patch.dict(os.environ, {"MOCK_TOOLING": "true"}):
                url_discover = f"http://localhost:{port}/api/projects/test-project-server/discover"
                req_discover = urllib.request.Request(url_discover)
                with urllib.request.urlopen(req_discover) as resp_discover:
                    assert resp_discover.status == 200
                    data_discover = json.loads(resp_discover.read().decode('utf-8'))
                    assert data_discover["project_id"] == "test-project-server"
                    assert len(data_discover["resources"]) > 0
                    assert os.path.exists(data_discover["cache_path"])
                    assert os.path.exists(data_discover["wiki_path"])

            # Test route rewriting fallback to index.html
            for fallback_path in ["/projects/test-project-server", "/clouds"]:
                url_fallback = f"http://localhost:{port}{fallback_path}"
                req_fallback = urllib.request.Request(url_fallback)
                with urllib.request.urlopen(req_fallback) as resp_fallback:
                    assert resp_fallback.status == 200
                    content = resp_fallback.read().decode('utf-8')
                    assert "<!DOCTYPE html>" in content or "<html" in content

            # Test wiki and graph API endpoints (expected to fail during Red Phase)
            # 1. Wiki endpoint test
            url_wiki = f"http://localhost:{port}/api/projects/test-project-server/wiki"
            # Try to get (should start with a default/autogenerated template or empty notes)
            req_wiki_get = urllib.request.Request(url_wiki)
            with urllib.request.urlopen(req_wiki_get) as resp_wiki_get:
                assert resp_wiki_get.status == 200
                data_wiki = json.loads(resp_wiki_get.read().decode('utf-8'))
                assert "content" in data_wiki
            
            # Try to post custom wiki notes
            req_wiki_post = urllib.request.Request(
                url_wiki,
                data=json.dumps({"content": "# Custom Wiki Content"}).encode("utf-8"),
                method="POST"
            )
            with urllib.request.urlopen(req_wiki_post) as resp_wiki_post:
                assert resp_wiki_post.status == 200
                data_wiki_post = json.loads(resp_wiki_post.read().decode('utf-8'))
                assert data_wiki_post["content"] == "# Custom Wiki Content"

            # 2. Graph endpoint test
            url_graph = f"http://localhost:{port}/api/projects/test-project-server/graph"
            # Try to get (should return default DOT template or empty)
            req_graph_get = urllib.request.Request(url_graph)
            with urllib.request.urlopen(req_graph_get) as resp_graph_get:
                assert resp_graph_get.status == 200
                data_graph = json.loads(resp_graph_get.read().decode('utf-8'))
                assert "content" in data_graph
            
            # Try to post custom graph DOT
            req_graph_post = urllib.request.Request(
                url_graph,
                data=json.dumps({"content": "digraph G {}"}).encode("utf-8"),
                method="POST"
            )
            with urllib.request.urlopen(req_graph_post) as resp_graph_post:
                assert resp_graph_post.status == 200
                data_graph_post = json.loads(resp_graph_post.read().decode('utf-8'))
                assert data_graph_post["content"] == "digraph G {}"

        finally:
            for fpath in [json_file, md_file]:
                if os.path.exists(fpath):
                    os.remove(fpath)
            
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join()

def test_get_discovered_projects_env_var():
    from src.server import get_discovered_projects
    with patch.dict(os.environ, {"SAMPLE_PROJECT_IDS": "env-proj-1,env-proj-2"}), \
         patch("os.path.exists", return_value=False):
        projs = get_discovered_projects()
        assert projs == ["env-proj-1", "env-proj-2"]

def test_api_transcribe():
    # Start the server on a free port
    server = HTTPServer(('localhost', 0), SREHttpRequestHandler)
    port = server.server_port
    
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    try:
        with patch("src.server.transcribe_voice_bytes") as mock_transcribe:
            mock_transcribe.return_value = "This is a test transcription from Gemini."
            url = f"http://localhost:{port}/api/transcribe"
            audio_data = b"fake-audio-bytes"
            req = urllib.request.Request(url, data=audio_data, method="POST", headers={"Content-Type": "audio/webm"})
            with urllib.request.urlopen(req) as response:
                assert response.status == 200
                data = json.loads(response.read().decode('utf-8'))
                assert data["transcription"] == "This is a test transcription from Gemini."
                mock_transcribe.assert_called_once_with(audio_data)
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join()

def test_static_html_elements():
    html_path = "src/static/index.html"
    assert os.path.exists(html_path)
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verify the sidebar is renamed
    assert "SRE SECONDARY ONCALL" in content
    # Verify resizer element is present
    assert 'id="sidebar-resizer"' in content
    # Verify mic button is present
    assert 'id="btn-chat-mic"' in content
    # Verify chat column has ID
    assert 'id="chat-column"' in content
    # Verify edit toggle buttons are present
    assert 'id="btn-edit-wiki"' in content
    assert 'id="btn-edit-graph"' in content


def test_server_basic_auth():
    import socket
    import threading
    import time
    import urllib.request
    import urllib.error
    import base64
    from src.server import run_server

    # Clean env just in case
    old_user = os.environ.pop("WEB_USERNAME", None)
    old_pwd = os.environ.pop("WEB_PASSWORD", None)

    # Find free port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()

    # Start server in thread
    server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    server_thread.start()
    time.sleep(0.5) # Wait for startup

    try:
        # 1. Request should succeed with 200 without auth (when env vars are unset)
        url = f"http://localhost:{port}/api/config"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200

        # 2. Test when basic auth IS enabled
        os.environ["WEB_USERNAME"] = "testuser"
        os.environ["WEB_PASSWORD"] = "testpass"

        # Request without headers should fail with 401
        req = urllib.request.Request(url)
        try:
            urllib.request.urlopen(req)
            assert False, "Should have failed with HTTP 401"
        except urllib.error.HTTPError as e:
            assert e.code == 401
            assert "Basic" in e.headers.get("WWW-Authenticate", "")

        # Request with correct headers should succeed
        req = urllib.request.Request(url)
        auth_bytes = b"testuser:testpass"
        auth_str = base64.b64encode(auth_bytes).decode("utf-8")
        req.add_header("Authorization", f"Basic {auth_str}")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200

    finally:
        # Restore environment variables
        if old_user:
            os.environ["WEB_USERNAME"] = old_user
        else:
            os.environ.pop("WEB_USERNAME", None)

        if old_pwd:
            os.environ["WEB_PASSWORD"] = old_pwd
        else:
            os.environ.pop("WEB_PASSWORD", None)


def test_server_iap_auth():
    import socket
    import threading
    import time
    import urllib.request
    import urllib.error
    from src.server import run_server

    # Setup environment
    old_identity = os.environ.pop("GCLOUD_IDENTITY", None)
    os.environ["GCLOUD_IDENTITY"] = "operator@google.com"

    # Find free port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()

    # Start server
    server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    server_thread.start()
    time.sleep(0.5)

    try:
        url = f"http://localhost:{port}/api/config"

        # 1. Request without x-goog-authenticated-user-email header should fail with 403
        req = urllib.request.Request(url)
        try:
            urllib.request.urlopen(req)
            assert False, "Should have failed with HTTP 403"
        except urllib.error.HTTPError as e:
            assert e.code == 403

        # 2. Request with incorrect email header should fail with 403
        req = urllib.request.Request(url)
        req.add_header("x-goog-authenticated-user-email", "accounts.google.com:attacker@google.com")
        try:
            urllib.request.urlopen(req)
            assert False, "Should have failed with HTTP 403"
        except urllib.error.HTTPError as e:
            assert e.code == 403

        # 3. Request with correct email header (with prefix) should succeed
        req = urllib.request.Request(url)
        req.add_header("x-goog-authenticated-user-email", "accounts.google.com:operator@google.com")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200

        # 4. Request with correct email header (no prefix) should succeed
        req = urllib.request.Request(url)
        req.add_header("x-goog-authenticated-user-email", "operator@google.com")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200

    finally:
        # Restore environment
        if old_identity:
            os.environ["GCLOUD_IDENTITY"] = old_identity
        else:
            os.environ.pop("GCLOUD_IDENTITY", None)





