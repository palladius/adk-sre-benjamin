import os
import json
import pytest
import sys
import threading
from unittest.mock import MagicMock, patch
from src.incident import IncidentContext
from src.observability import log_audit_event

def test_local_jsonl_logging(tmp_path):
    log_file = tmp_path / "test-audit.jsonl"
    os.environ["BENJAMIN_AUDIT_LOG_PATH"] = str(log_file)
    
    ctx = IncidentContext(incident_uuid="test-uuid-123", incident_id="INC-test-123")
    ctx.incident_id = "INC-test-123"  # explicit check
    
    log_audit_event(
        incident_context=ctx,
        sender_agent="OpsAgent",
        receiver_agent="ScribeAgent",
        message="Running kubernetes diagnostics.",
        severity="WARNING",
        context={"tool": "list_k8s_api_resources"}
    )
    
    assert log_file.exists()
    
    # Read the lines
    with open(log_file, "r") as f:
        lines = f.read().splitlines()
        
    assert len(lines) == 2
    
    # Verify the JSON line
    json_line = lines[0]
    data = json.loads(json_line)
    
    assert data["incident_uuid"] == "test-uuid-123"
    assert data["incident_id"] == "INC-test-123"
    assert data["sender agent"] == "OpsAgent"
    assert data["sender_agent"] == "OpsAgent"
    assert data["receiver agent"] == "ScribeAgent"
    assert data["receiver_agent"] == "ScribeAgent"
    assert data["message"] == "Running kubernetes diagnostics."
    assert data["severity"] == "WARNING"
    assert data["context"] == {"tool": "list_k8s_api_resources"}
    assert "timestamp" in data
    
    # Verify the human-readable text line
    text_line = lines[1]
    assert "[WARNING]" in text_line
    assert "INC-test-123" in text_line
    assert "test-uuid-123" in text_line
    assert "OpsAgent -> ScribeAgent" in text_line
    assert "Running kubernetes diagnostics." in text_line

def test_local_logging_fallback(tmp_path):
    # Set to a directory path that cannot be created/written to (e.g. empty/invalid name on some OS, or just check it doesn't crash)
    os.environ["BENJAMIN_AUDIT_LOG_PATH"] = "/unwritable_directory/test-audit.jsonl"
    
    ctx = IncidentContext(incident_uuid="test-uuid-123")
    
    # Should not raise any exception
    log_audit_event(
        incident_context=ctx,
        sender_agent="OpsAgent",
        receiver_agent="ScribeAgent",
        message="Checking fallback behavior.",
        severity="INFO"
    )

def test_log_rotation(tmp_path):
    log_file = tmp_path / "test-rotate.jsonl"
    os.environ["BENJAMIN_AUDIT_LOG_PATH"] = str(log_file)
    
    ctx = IncidentContext(incident_uuid="test-uuid-123")
    
    # Write a dummy file that is large to trigger rotation
    with open(log_file, "w") as f:
        f.write("a" * (11 * 1024 * 1024))  # 11MB, greater than 10MB
        
    log_audit_event(
        incident_context=ctx,
        sender_agent="OpsAgent",
        receiver_agent="ScribeAgent",
        message="Triggering rotation.",
        severity="INFO"
    )
    
    # Verify rotation occurred (the 11MB file renamed to .1)
    rotated_file = tmp_path / "test-rotate.jsonl.1"
    assert rotated_file.exists()
    assert log_file.exists()
    
    # The new log file should have the new entry (2 lines: 1 json, 1 text)
    with open(log_file, "r") as f:
        lines = f.read().splitlines()
    assert len(lines) == 2

@patch("src.observability.HAS_CLOUD_LOGGING", True)
def test_gcp_logging_integration():
    mock_client_class = MagicMock()
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    mock_logger = MagicMock()
    mock_client.logger.return_value = mock_logger
    
    # Patch google.cloud.logging
    with patch("sys.modules") as mock_modules:
        import sys
        # Create a mock module structure
        mock_gcp_logging = MagicMock()
        mock_gcp_logging.Client = mock_client_class
        
        # Inject mock into sys.modules
        sys.modules["google.cloud.logging"] = mock_gcp_logging
        sys.modules["google.cloud"] = MagicMock()
        
        # Intercept background thread to run synchronously for test
        def mock_start(thread_self):
            thread_self._target(*thread_self._args, **thread_self._kwargs)
            
        with patch.object(threading.Thread, "start", mock_start):
            ctx = IncidentContext(incident_uuid="gcp-uuid-456", incident_id="INC-gcp-456")
            ctx.incident_id = "INC-gcp-456"
            
            log_audit_event(
                incident_context=ctx,
                sender_agent="OpsAgent",
                receiver_agent="ScribeAgent",
                message="Structured Cloud Logging test.",
                severity="ERROR",
                context={"test": "gcp"}
            )
            
            mock_client_class.assert_called_once()
            mock_client.logger.assert_called_with("benjamin-audit")
            mock_logger.log_struct.assert_called_once()
            
            called_payload = mock_logger.log_struct.call_args[0][0]
            assert called_payload["incident_uuid"] == "gcp-uuid-456"
            assert called_payload["incident_id"] == "INC-gcp-456"
            assert called_payload["sender agent"] == "OpsAgent"
            assert called_payload["message"] == "Structured Cloud Logging test."
            assert called_payload["severity"] == "ERROR"
            assert called_payload["context"] == {"test": "gcp"}
