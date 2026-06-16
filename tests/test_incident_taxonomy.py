import pytest
from src.incident import validate_incident_status, IncidentStatus, IncidentStateError

def test_valid_statuses():
    # Enforce NEW, ONGOING, CLOSED are valid
    assert validate_incident_status("NEW") == "NEW"
    assert validate_incident_status("ONGOING") == "ONGOING"
    assert validate_incident_status("CLOSED") == "CLOSED"

def test_legacy_mappings():
    # Verify legacy mapping
    assert validate_incident_status("UNKNOWN") == "NEW"
    assert validate_incident_status("ACTIVE") == "ONGOING"
    assert validate_incident_status("RESOLVED") == "CLOSED"

def test_invalid_status_raises_error():
    # Any actual invalid status should raise validation error
    with pytest.raises(IncidentStateError):
        validate_incident_status("INVALID")
    with pytest.raises(IncidentStateError):
        validate_incident_status("SOME_OTHER_STATUS")

def test_substatus_fields_default_on_creation():
    # When creating or parsing, check that substatus fields default correctly
    # and validation succeeds for correct types
    from src.incident import IncidentMetadata
    
    metadata = IncidentMetadata()
    assert metadata.status == "NEW"
    assert metadata.substatus_rca is False
    assert metadata.substatus_mitigated is False
    assert metadata.substatus_fixed is False
    assert metadata.substatus_verified is False

def test_substatus_field_validation():
    from src.incident import IncidentMetadata
    
    # Valid assignments
    metadata = IncidentMetadata(
        status="ONGOING",
        substatus_rca=True,
        substatus_mitigated=True,
        substatus_fixed=False,
        substatus_verified=False
    )
    assert metadata.status == "ONGOING"
    assert metadata.substatus_rca is True
    
    # Invalid types/values should raise error
    with pytest.raises(IncidentStateError):
        IncidentMetadata(status="INVALID")
        
    with pytest.raises(IncidentStateError):
        IncidentMetadata(substatus_rca="not_a_bool")


def test_transition_incident_state(tmp_path):
    from src.incident import transition_incident_state
    
    inc_dir = tmp_path / "INC-20260603-test"
    inc_dir.mkdir()
    state_file = inc_dir / "state.md"
    state_file.write_text("""# Active SRE Incident State: INC-20260603-test
## Metadata
- **Status:** NEW
- **RCA Found:** False
- **Mitigated:** False
- **Fixed:** False
- **Verified:** False
""")
    timeline_file = inc_dir / "timeline.md"
    timeline_file.write_text("- **[2026-06-16T10:00:00Z]** [System] Started\n")
    
    transition_incident_state(
        str(inc_dir),
        status="ONGOING",
        substatus_rca=True,
        substatus_mitigated=True,
        operator="Lucia"
    )
    
    state_content = state_file.read_text()
    assert "- **Status:** ONGOING" in state_content
    assert "- **RCA Found:** True" in state_content
    assert "- **Mitigated:** True" in state_content
    assert "- **Fixed:** False" in state_content
    assert "- **Verified:** False" in state_content
    
    timeline_content = timeline_file.read_text()
    assert "Status transitioned from NEW to ONGOING" in timeline_content
    assert "RCA Found transitioned from False to True" in timeline_content
    assert "Mitigated transitioned from False to True" in timeline_content
    assert "[Lucia]" in timeline_content
