import pytest
from src.agents import (
    IncidentCommander,
    CommunicationsLead,
    OperationsLead,
    PlanningLead,
    LogisticsLead
)

def test_incident_commander(monkeypatch):
    monkeypatch.delenv("COMMANDER_NAME", raising=False)
    monkeypatch.delenv("INCIDENT_COMMANDER_NAME", raising=False)
    ic = IncidentCommander()
    assert ic.agent.name == "Benjamin"
    
    decl = ic.declare_incident("latency_alert", "project-x", "INC-999")
    assert "INC-999" in decl
    assert "latency_alert" in decl

def test_communications_lead(monkeypatch):
    monkeypatch.delenv("COMMS_LEAD_NAME", raising=False)
    monkeypatch.delenv("COMMUNICATIONS_LEAD_NAME", raising=False)
    monkeypatch.delenv("MADHAVI_NAME", raising=False)
    cl = CommunicationsLead()
    assert cl.agent.name == "Madhavi"
    
    bc = cl.broadcast_incident("INC-123", "ACTIVE", "prod-1", "Latency high")
    assert "INC-123" in bc
    assert "ACTIVE" in bc
    
    hitl = cl.request_hitl_approval("INC-123", "reboot", "HIGH", ["Dangerous command"])
    assert "reboot" in hitl
    assert "Dangerous command" in hitl

def test_communications_lead_dynamic_name(monkeypatch):
    monkeypatch.setenv("COMMS_LEAD_NAME", "Lucia")
    cl = CommunicationsLead()
    assert cl.agent.name == "Lucia"
    assert "Lucia" in cl.agent.instruction
    
    # Verify interactive run method works under both mock and fallback modes
    resp = cl.run("Hello there!")
    assert "Lucia" in resp
    assert "SRE" in resp or "public" in resp

def test_agent_run_methods():
    from src.agents import IncidentCommander, OperationsLead, PlanningLead, LogisticsLead
    ic = IncidentCommander()
    assert ic.agent.name in ic.run("hello")
    
    ops = OperationsLead()
    assert ops.agent.name in ops.run("status")
    
    planning = PlanningLead()
    assert planning.agent.name in planning.run("hello")
    
    logistics = LogisticsLead()
    assert logistics.agent.name in logistics.run("status")

def test_operations_lead(monkeypatch):
    monkeypatch.delenv("OPS_LEAD_NAME", raising=False)
    monkeypatch.delenv("OPERATIONS_LEAD_NAME", raising=False)
    monkeypatch.delenv("OPS_AGENT_NAME", raising=False)
    ol = OperationsLead()
    assert ol.agent.name == "OpsAgent"
    
    triage = ol.triage_metric("latency", 480.0, 100.0)
    assert "latency" in triage
    
    prop = ol.propose_mutation("rm -rf", "db", "clean state")
    assert "rm -rf" in prop

def test_planning_lead(monkeypatch):
    monkeypatch.delenv("PLANNING_LEAD_NAME", raising=False)
    monkeypatch.delenv("PLANNING_AGENT_NAME", raising=False)
    pl = PlanningLead()
    assert pl.agent.name == "PlanningAgent"
    
    commit = pl.scribe_commit("State updated", "sha123")
    assert "sha123" in commit
    
    disc = pl.discovery_summary("prod-db-999", 5, 2, 0)
    assert "prod-db-999" in disc

def test_logistics_lead(monkeypatch):
    monkeypatch.delenv("LOGISTICS_LEAD_NAME", raising=False)
    monkeypatch.delenv("LOGISTICS_AGENT_NAME", raising=False)
    ll = LogisticsLead()
    assert ll.agent.name == "LogisticsAgent"
    
    eval_msg = ll.command_evaluation("rm -rf", ["rm", "rf"], "HIGH", "BLOCKED", ["Destructive"])
    assert "rm -rf" in eval_msg
    assert "HIGH" in eval_msg
    
    quota = ll.quota_check("prod-1", "GCP_TOKEN", "ACTIVE")
    assert "GCP_TOKEN" in quota

def test_all_agents_dynamic_renaming(monkeypatch):
    monkeypatch.setenv("COMMANDER_NAME", "Ben Treno")
    monkeypatch.setenv("COMMS_LEAD_NAME", "Lucia Treno")
    monkeypatch.setenv("OPS_LEAD_NAME", "Gigi Mutatore")
    monkeypatch.setenv("PLANNING_LEAD_NAME", "Scrivano Reale")
    monkeypatch.setenv("LOGISTICS_LEAD_NAME", "Fornitore Quota")
    
    ic = IncidentCommander()
    cl = CommunicationsLead()
    ol = OperationsLead()
    pl = PlanningLead()
    ll = LogisticsLead()
    
    assert ic.agent.name == "Ben Treno"
    assert cl.agent.name == "Lucia Treno"
    assert ol.agent.name == "Gigi Mutatore"
    assert pl.agent.name == "Scrivano Reale"
    assert ll.agent.name == "Fornitore Quota"
    
    assert "Ben Treno" in ic.agent.instruction
    assert "Lucia Treno" in cl.agent.instruction
    assert "Gigi Mutatore" in ol.agent.instruction
    assert "Scrivano Reale" in pl.agent.instruction
    assert "Fornitore Quota" in ll.agent.instruction
