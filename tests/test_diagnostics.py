import os
import pytest
from src.diagnostics import query_logs, query_metrics

def test_query_logs_mock(monkeypatch):
    monkeypatch.setenv("SRE_MODE", "MOCK")
    logs = query_logs("prod-db-999", "error")
    assert "lock contention" in logs
    assert "timeout" in logs

def test_query_logs_live(monkeypatch):
    monkeypatch.setenv("SRE_MODE", "LIVE")
    with pytest.raises(NotImplementedError):
        query_logs("prod-db-999", "error")

def test_query_metrics_mock(monkeypatch):
    monkeypatch.setenv("SRE_MODE", "MOCK")
    metrics = query_metrics("prod-db-999", "frontend_latency")
    assert isinstance(metrics, list)
    assert len(metrics) > 0
    assert any(x >= 400.0 for x in metrics) # Mocking active latency spikes

def test_query_metrics_live(monkeypatch):
    monkeypatch.setenv("SRE_MODE", "LIVE")
    with pytest.raises(NotImplementedError):
        query_metrics("prod-db-999", "frontend_latency")
