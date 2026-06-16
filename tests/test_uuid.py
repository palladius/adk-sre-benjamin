import uuid
import os
import pytest
from src.incident import IncidentContext
from src.scaffolding import scaffold_incident, Incident
from src.trigger import Trigger
from src.agents import (
    IncidentCommander,
    CommunicationsLead,
    OperationsLead,
    PlanningLead,
    LogisticsLead
)
from src.orchestrator import run_incident_flow

def is_valid_uuid4(val: str) -> bool:
    try:
        uuid_obj = uuid.UUID(val, version=4)
        return str(uuid_obj) == val
    except ValueError:
        return False

def test_incident_context_uuid_generation():
    # Test default initialization generates a valid UUIDv4
    ctx = IncidentContext()
    assert ctx.incident_uuid is not None
    assert is_valid_uuid4(ctx.incident_uuid)

def test_incident_context_uuid_explicit():
    # Test explicit UUID is preserved
    test_uuid = str(uuid.uuid4())
    ctx = IncidentContext(incident_uuid=test_uuid)
    assert ctx.incident_uuid == test_uuid

def test_agent_uuid_propagation():
    ctx = IncidentContext()
    
    # Initialize agents with context and assert metadata propagation
    ic = IncidentCommander(incident_context=ctx)
    cl = CommunicationsLead(incident_context=ctx)
    ol = OperationsLead(incident_context=ctx)
    pl = PlanningLead(incident_context=ctx)
    ll = LogisticsLead(incident_context=ctx)
    
    for lead in [ic, cl, ol, pl, ll]:
        assert lead.metadata is not None
        assert lead.metadata.get("incident_uuid") == ctx.incident_uuid
        assert lead.agent.metadata is not None
        assert lead.agent.metadata.get("incident_uuid") == ctx.incident_uuid

def test_orchestrator_uuid_propagation(tmp_path):
    payload = {
        "event_type": "frontend_latency_slo_violated",
        "project_id": "prod-db-999"
    }
    incident_id, folder_path = run_incident_flow(payload, base_dir=str(tmp_path))
    
    # Verify we can run and get the incident ID
    assert incident_id.startswith("INC-")
    
    # Check that incident state directory was created
    assert os.path.exists(folder_path)
