from enum import Enum
from typing import Any, Dict

class IncidentStatus(str, Enum):
    NEW = "NEW"
    ONGOING = "ONGOING"
    CLOSED = "CLOSED"

class IncidentStateError(ValueError):
    """Raised when incident status or substatus validation fails."""
    pass

def validate_incident_status(status: Any) -> str:
    """Enforces that the status must be a valid IncidentStatus enum value."""
    if isinstance(status, IncidentStatus):
        return status.value
    if isinstance(status, str):
        val = status.upper().strip()
        if val == "ACTIVE":
            return IncidentStatus.ONGOING.value
        if val == "RESOLVED":
            return IncidentStatus.CLOSED.value
        if val == "UNKNOWN":
            return IncidentStatus.NEW.value
        if val in IncidentStatus.__members__:
            return val
    raise IncidentStateError(f"Invalid incident status: {status}. Must be one of {[e.value for e in IncidentStatus]}")

class IncidentMetadata:
    """Represents and validates the metadata of an incident, including status and substatus fields."""
    
    def __init__(
        self,
        status: Any = "NEW",
        substatus_rca: Any = False,
        substatus_mitigated: Any = False,
        substatus_fixed: Any = False,
        substatus_verified: Any = False
    ):
        self.status = validate_incident_status(status)
        
        # Enforce that substatus modifiers must be booleans
        if not isinstance(substatus_rca, bool):
            raise IncidentStateError(f"substatus_rca must be a boolean, got {type(substatus_rca).__name__}")
        if not isinstance(substatus_mitigated, bool):
            raise IncidentStateError(f"substatus_mitigated must be a boolean, got {type(substatus_mitigated).__name__}")
        if not isinstance(substatus_fixed, bool):
            raise IncidentStateError(f"substatus_fixed must be a boolean, got {type(substatus_fixed).__name__}")
        if not isinstance(substatus_verified, bool):
            raise IncidentStateError(f"substatus_verified must be a boolean, got {type(substatus_verified).__name__}")
            
        self.substatus_rca = substatus_rca
        self.substatus_mitigated = substatus_mitigated
        self.substatus_fixed = substatus_fixed
        self.substatus_verified = substatus_verified

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the metadata to a dictionary."""
        return {
            "status": self.status,
            "substatus_rca": self.substatus_rca,
            "substatus_mitigated": self.substatus_mitigated,
            "substatus_fixed": self.substatus_fixed,
            "substatus_verified": self.substatus_verified
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IncidentMetadata":
        """Deserializes metadata from a dictionary with validation and defaults."""
        return cls(
            status=data.get("status", "NEW"),
            substatus_rca=data.get("substatus_rca", False),
            substatus_mitigated=data.get("substatus_mitigated", False),
            substatus_fixed=data.get("substatus_fixed", False),
            substatus_verified=data.get("substatus_verified", False)
        )
