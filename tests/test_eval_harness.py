import pytest
from tests.eval.eval_runner import (
    compute_rouge_scores,
    run_isolated_agent_evals,
    run_integration_eval,
    run_all_evaluations
)

def test_rouge_computation():
    ref = "Hello, SRE. I am Incident Commander Benjamin."
    cand = "Hello, SRE. I am Incident Commander Benjamin. Ready to coordinate."
    scores = compute_rouge_scores(ref, cand)
    assert "rouge1" in scores
    assert "rouge2" in scores
    assert "rougeL" in scores
    assert scores["rouge1"] > 0.5

def test_isolated_agent_evals_pass():
    passed = run_isolated_agent_evals()
    assert passed is True

def test_integration_eval_pass():
    passed = run_integration_eval()
    assert passed is True

def test_master_eval_harness():
    passed = run_all_evaluations()
    assert passed is True
