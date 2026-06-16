import os
import json
import pytest
import shutil
import threading
import urllib.request
import urllib.error
from http.server import HTTPServer
from datetime import datetime, timezone
from src.server import SREHttpRequestHandler, get_mutation_comments_context

INCIDENT_ID = "INC-MOCK-QUEUE-TEST"
INCIDENT_PATH = os.path.join("investigations", INCIDENT_ID)

@pytest.fixture(scope="module", autouse=True)
def setup_mock_incident():
    # Setup
    if os.path.exists(INCIDENT_PATH):
        shutil.rmtree(INCIDENT_PATH)
    os.makedirs(INCIDENT_PATH, exist_ok=True)
    
    # Create mock state.md
    with open(os.path.join(INCIDENT_PATH, "state.md"), "w") as f:
        f.write("""# Active SRE Incident State: INC-MOCK-QUEUE-TEST
## Metadata
- **Status:** ACTIVE
- **Target Project:** `test-project`
- **Trigger Event:** `test_trigger`
- **Incident Commander:** Benjamin
- **Safety Level:** LOW Risk
""")
        
    # Create mock timeline.md
    with open(os.path.join(INCIDENT_PATH, "timeline.md"), "w") as f:
        f.write("- **[2026-06-01T07:55:00Z]** [System] Incident declared.\n")
        
    # Create mock chat.json
    with open(os.path.join(INCIDENT_PATH, "chat.json"), "w") as f:
        json.dump([], f)
        
    yield
    
    # Teardown
    if os.path.exists(INCIDENT_PATH):
        shutil.rmtree(INCIDENT_PATH)

@pytest.fixture(scope="module")
def server():
    # Start the server on a free port
    server = HTTPServer(('localhost', 0), SREHttpRequestHandler)
    port = server.server_port
    
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    yield port
    
    server.shutdown()
    server.server_close()

def test_get_pending_empty(server):
    port = server
    url = f"http://localhost:{port}/api/incidents/{INCIDENT_ID}/pending"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode('utf-8'))
        assert data == []

def test_post_pending_validation_error(server):
    port = server
    url = f"http://localhost:{port}/api/incidents/{INCIDENT_ID}/pending"
    # Missing fields
    payload = json.dumps({
        "command": "kubectl drain node-1",
        "risk_factor": "HIGH"
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=payload, method="POST")
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 400

def test_post_pending_success(server):
    port = server
    url = f"http://localhost:{port}/api/incidents/{INCIDENT_ID}/pending"
    payload = json.dumps({
        "command": "kubectl drain node-1",
        "risk_factor": "HIGH",
        "risk_reason": "Draining primary services might disrupt user traffic.",
        "justification": "Clears stuck TCP sockets causing the SLO alert."
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=payload, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        data = json.loads(resp.read().decode('utf-8'))
        assert data["id"] == "cmd-01"
        assert "kubectl drain" in data["command"]
        assert "HIGH" in data["risk_factor"]
        assert "🟠" in data["risk_factor"]
        
    # Check GET /pending matches
    req_get = urllib.request.Request(url)
    with urllib.request.urlopen(req_get) as resp_get:
        assert resp_get.status == 200
        data_get = json.loads(resp_get.read().decode('utf-8'))
        assert len(data_get) == 1
        assert data_get[0]["id"] == "cmd-01"
        
    # Check that state.md contains the Markdown table
    state_file = os.path.join(INCIDENT_PATH, "state.md")
    with open(state_file, "r") as f:
        content = f.read()
    assert "## Pending SRE Mutation Actions Queue" in content
    assert "| `cmd-01` | `kubectl drain node-1` | 🟠 HIGH |" in content

def test_post_pending_approve(server):
    port = server
    # Add a second command to test multi-item queue
    url_add = f"http://localhost:{port}/api/incidents/{INCIDENT_ID}/pending"
    payload_add = json.dumps({
        "command": "systemctl restart mysql",
        "risk_factor": "MEDIUM",
        "risk_reason": "Brief interruption to database connection.",
        "justification": "Restarts connections to mysql database."
    }).encode("utf-8")
    
    req_add = urllib.request.Request(url_add, data=payload_add, method="POST")
    with urllib.request.urlopen(req_add) as resp_add:
        assert resp_add.status == 201
        data_add = json.loads(resp_add.read().decode('utf-8'))
        assert data_add["id"] == "cmd-02"
        assert "🟡" in data_add["risk_factor"]
        
    # Approve cmd-01 with a comment
    url_approve = f"http://localhost:{port}/api/incidents/{INCIDENT_ID}/pending/cmd-01/approve"
    payload_approve = json.dumps({
        "comment": "Proceeding with node drain as it is non-production."
    }).encode("utf-8")
    
    req_approve = urllib.request.Request(url_approve, data=payload_approve, method="POST")
    with urllib.request.urlopen(req_approve) as resp_approve:
        assert resp_approve.status == 200
        data_approve = json.loads(resp_approve.read().decode('utf-8'))
        assert data_approve["status"] == "approved"
        assert data_approve["cmd_id"] == "cmd-01"
        
    # Verify cmd-01 is removed, but cmd-02 is still there
    url_pending = f"http://localhost:{port}/api/incidents/{INCIDENT_ID}/pending"
    req_pending = urllib.request.Request(url_pending)
    with urllib.request.urlopen(req_pending) as resp_pending:
        data_pending = json.loads(resp_pending.read().decode('utf-8'))
        assert len(data_pending) == 1
        assert data_pending[0]["id"] == "cmd-02"
        
    # Verify timeline and chat are updated
    timeline_file = os.path.join(INCIDENT_PATH, "timeline.md")
    with open(timeline_file, "r") as f:
        timeline_content = f.read()
    assert "Approved proposed mutation command" in timeline_content
    assert "Executing whitelisted mutation command: kubectl drain node-1" in timeline_content
    assert "Proceeding with node drain" in timeline_content
    
    chat_file = os.path.join(INCIDENT_PATH, "chat.json")
    with open(chat_file, "r") as f:
        chat_content = json.load(f)
    assert any("Approved proposed mutation command 'kubectl drain node-1'" in msg["message"] for msg in chat_content)
    assert any("Proceeding with node drain" in msg["message"] for msg in chat_content)
    
    # Verify incident status updated to CLOSED in state.md
    state_file = os.path.join(INCIDENT_PATH, "state.md")
    with open(state_file, "r") as f:
        state_content = f.read()
    assert "- **Status:** CLOSED" in state_content
    assert "| `cmd-02` | `systemctl restart mysql` |" in state_content
    assert "cmd-01" not in state_content

def test_post_pending_reject(server):
    port = server
    # Reject cmd-02 with a comment
    url_reject = f"http://localhost:{port}/api/incidents/{INCIDENT_ID}/pending/cmd-02/reject"
    payload_reject = json.dumps({
        "comment": "Database restart is too risky right now."
    }).encode("utf-8")
    
    req_reject = urllib.request.Request(url_reject, data=payload_reject, method="POST")
    with urllib.request.urlopen(req_reject) as resp_reject:
        assert resp_reject.status == 200
        data_reject = json.loads(resp_reject.read().decode('utf-8'))
        assert data_reject["status"] == "rejected"
        assert data_reject["cmd_id"] == "cmd-02"
        
    # Verify queue is now empty
    url_pending = f"http://localhost:{port}/api/incidents/{INCIDENT_ID}/pending"
    req_pending = urllib.request.Request(url_pending)
    with urllib.request.urlopen(req_pending) as resp_pending:
        data_pending = json.loads(resp_pending.read().decode('utf-8'))
        assert len(data_pending) == 0
        
    # Verify comment was saved in mutation_comments.json
    comments_file = os.path.join(INCIDENT_PATH, "mutation_comments.json")
    assert os.path.exists(comments_file)
    with open(comments_file, "r") as f:
        comments_data = json.load(f)
    assert len(comments_data) == 2
    assert comments_data[0]["action"] == "approve"
    assert comments_data[0]["comment"] == "Proceeding with node drain as it is non-production."
    assert comments_data[1]["action"] == "reject"
    assert comments_data[1]["comment"] == "Database restart is too risky right now."
    
    # Verify prompt injection context builder
    comments_context = get_mutation_comments_context(INCIDENT_PATH)
    assert "[Recent Mutation Queue Actions & Operator Comments]:" in comments_context
    assert "- Command 'kubectl drain node-1' was approved" in comments_context
    assert "- Command 'systemctl restart mysql' was rejected" in comments_context
    assert "Proceeding with node drain as it is non-production." in comments_context
    assert "Database restart is too risky right now." in comments_context
