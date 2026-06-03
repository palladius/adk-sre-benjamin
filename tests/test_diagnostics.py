import os
import pytest
import json
from unittest.mock import MagicMock, patch
from src.diagnostics import query_logs, query_metrics

def test_query_logs_mock(monkeypatch):
    monkeypatch.setenv("SRE_MODE", "MOCK")
    logs = query_logs("prod-db-999", "error")
    assert "lock contention" in logs
    assert "timeout" in logs

def test_query_logs_live(monkeypatch):
    monkeypatch.setenv("SRE_MODE", "LIVE")
    
    mock_entry = {
        "timestamp": "2026-06-03T11:17:33Z",
        "severity": "ERROR",
        "textPayload": "test error payload"
    }
    
    mock_run_result = MagicMock()
    mock_run_result.stdout = json.dumps([mock_entry])
    
    with patch("subprocess.run", return_value=mock_run_result) as mock_run:
        logs = query_logs("prod-db-999", "error")
        assert "test error payload" in logs
        assert "ERROR" in logs
        mock_run.assert_called_once()

def test_query_metrics_mock(monkeypatch):
    monkeypatch.setenv("SRE_MODE", "MOCK")
    metrics = query_metrics("prod-db-999", "frontend_latency")
    assert isinstance(metrics, list)
    assert len(metrics) > 0
    assert any(x >= 400.0 for x in metrics) # Mocking active latency spikes

def test_query_metrics_live(monkeypatch):
    monkeypatch.setenv("SRE_MODE", "LIVE")
    
    mock_token_result = MagicMock()
    mock_token_result.stdout = "fake-token"
    
    mock_api_response = {
        "timeSeries": [
            {
                "points": [
                    {
                        "value": {"doubleValue": 0.45}
                    },
                    {
                        "value": {"doubleValue": 0.32}
                    }
                ]
            }
        ]
    }
    
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_api_response).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    
    with patch("subprocess.run", return_value=mock_token_result), \
         patch("urllib.request.urlopen", return_value=mock_response):
         
         metrics = query_metrics("prod-db-999", "cpu")
         # Reverted order of [0.45, 0.32] is [0.32, 0.45], scaled by 100.0 is [32.0, 45.0]
         assert metrics == [32.0, 45.0]
