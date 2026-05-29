import pytest
from src.agents import (
    IncidentCommander,
    CommunicationsLead,
    OperationsLead,
    PlanningLead,
    LogisticsLead
)

def test_incident_commander():
    ic = IncidentCommander()
    assert ic.agent.name == "Benjamin"
    
    decl = ic.declare_incident("latency_alert", "project-x", "INC-999")
    assert "INC-999" in decl
    assert "latency_alert" in decl

def test_communications_lead():
    cl = CommunicationsLead()
    assert cl.agent.name == "Madhavi"
    
    bc = cl.broadcast_incident("INC-123", "ACTIVE", "prod-1", "Latency high")
    assert "INC-123" in bc
    assert "ACTIVE" in bc
    
    hitl = cl.request_hitl_approval("INC-123", "reboot", "HIGH", ["Dangerous command"])
    assert "reboot" in hitl
    assert "Dangerous command" in hitl

def test_operations_lead():
    ol = OperationsLead()
    assert ol.agent.name == "OpsAgent"
    
    triage = ol.triage_metric("latency", 480.0, 100.0)
    assert "latency" in triage
    
    prop = ol.propose_mutation("rm -rf", "db", "clean state")
    assert "rm -rf" in prop

def test_planning_lead():
    pl = PlanningLead()
    assert pl.agent.name == "PlanningAgent"
    
    commit = pl.scribe_commit("State updated", "sha123")
    assert "sha123" in commit
    
    disc = pl.discovery_summary("prod-db-999", 5, 2, 0)
    assert "prod-db-999" in disc

def test_logistics_lead():
    ll = LogisticsLead()
    assert ll.agent.name == "LogisticsAgent"
    
    eval_msg = ll.command_evaluation("rm -rf", ["rm", "rf"], "HIGH", "BLOCKED", ["Destructive"])
    assert "rm -rf" in eval_msg
    assert "HIGH" in eval_msg
    
    quota = ll.quota_check("prod-1", "GCP_TOKEN", "ACTIVE")
    assert "GCP_TOKEN" in quota
