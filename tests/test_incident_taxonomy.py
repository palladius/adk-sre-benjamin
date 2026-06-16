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
