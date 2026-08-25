"""Tests for Agent Quality Flywheel evaluation runner."""

import os
import pytest
from eval.runner import run_agent_isolation_evals, run_integration_evals, run_all_evals

def test_run_agent_isolation_evals():
    results = run_agent_isolation_evals()
    assert isinstance(results, dict)
    assert "commander" in results
    assert "ops" in results
    assert "logistics" in results
    assert "planning" in results
    assert "comms" in results
    for agent, metrics in results.items():
        assert "passed" in metrics
        assert "score" in metrics

def test_run_integration_evals():
    results = run_integration_evals()
    assert isinstance(results, dict)
    assert "scenarios" in results
    assert "overall_score" in results

def test_run_all_evals():
    summary = run_all_evals()
    assert summary["status"] == "SUCCESS"
    assert "isolation" in summary
    assert "integration" in summary
