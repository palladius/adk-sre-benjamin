import os
import uuid
from enum import Enum
from typing import Any, Dict

def get_investigations_dir() -> str:
    env = os.getenv("SRE_ENV")
    if not env and "PYTEST_CURRENT_TEST" in os.environ:
        env = "test"
    if not env:
        env = os.getenv("RAILS_ENV") or "development"
    env = env.lower().strip()
    print(f"DEBUG get_investigations_dir: SRE_ENV={os.getenv('SRE_ENV')}, RAILS_ENV={os.getenv('RAILS_ENV')}, resolved={env}")
    if env in ("prod", "production"):
        return "investigations/prod"
    elif env in ("test", "testing"):
        return "investigations/test"
    else:
        return "investigations/dev"

def get_discover_dir() -> str:
    env = os.getenv("SRE_ENV")
    if not env and "PYTEST_CURRENT_TEST" in os.environ:
        env = "test"
    if not env:
        env = os.getenv("RAILS_ENV") or "development"
    env = env.lower().strip()
    if env in ("prod", "production"):
        return "discovery/prod"
    elif env in ("test", "testing"):
        return "discovery/test"
    else:
        return "discovery/dev"

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

class IncidentContext:
    """Shared context for the SRE incident lifecycle, maintaining correlation identifiers."""
    def __init__(self, incident_uuid: str = None, incident_id: str = None, **kwargs):
        self.incident_uuid = incident_uuid or str(uuid.uuid4())
        self.incident_id = incident_id
        self.metadata = kwargs
        self.metadata["incident_uuid"] = self.incident_uuid
        if incident_id:
            self.metadata["incident_id"] = incident_id


def transition_incident_state(
    incident_path: str,
    status: str = None,
    substatus_rca: bool = None,
    substatus_mitigated: bool = None,
    substatus_fixed: bool = None,
    substatus_verified: bool = None,
    operator: str = "System"
) -> None:
    import os
    import re
    from datetime import datetime, timezone
    
    state_path = os.path.join(incident_path, "state.md")
    if not os.path.exists(state_path):
        raise FileNotFoundError(f"State file not found at {state_path}")
        
    with open(state_path, "r") as f:
        content = f.read()

    def parse_field(pattern, text, is_bool=False):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = match.group(2 if len(match.groups()) > 1 else 1).strip()
            if is_bool:
                return val.lower() == "true"
            return val
        return None

    curr_status = parse_field(r'\-\s+\*\*Status:\*\*\s*([A-Za-z0-9_-]+)', content)
    curr_rca = parse_field(r'\-\s+\*\*(RCA Found|rca_found|substatus_rca):\*\*\s*([A-Za-z0-9_-]+)', content, is_bool=True)
    curr_mitigated = parse_field(r'\-\s+\*\*(Mitigated|mitigated|substatus_mitigated):\*\*\s*([A-Za-z0-9_-]+)', content, is_bool=True)
    curr_fixed = parse_field(r'\-\s+\*\*(Fixed|fixed|substatus_fixed):\*\*\s*([A-Za-z0-9_-]+)', content, is_bool=True)
    curr_verified = parse_field(r'\-\s+\*\*(Verified|verified|substatus_verified):\*\*\s*([A-Za-z0-9_-]+)', content, is_bool=True)

    if curr_status is None:
        curr_status = "NEW"
    if curr_rca is None:
        curr_rca = False
    if curr_mitigated is None:
        curr_mitigated = False
    if curr_fixed is None:
        curr_fixed = False
    if curr_verified is None:
        curr_verified = False

    timeline_entries = []

    if status is not None:
        validated_status = validate_incident_status(status)
        if validated_status != curr_status:
            timeline_entries.append(f"Status transitioned from {curr_status} to {validated_status}")
            curr_status = validated_status
            pattern = r'(\-\s+\*\*Status:\*\*\s*)([A-Za-z0-9_-]+)'
            if re.search(pattern, content, re.IGNORECASE):
                content = re.sub(pattern, r'\g<1>' + curr_status, content, flags=re.IGNORECASE)
            else:
                content += f"\n- **Status:** {curr_status}"

    def update_bool_field(field_name, display_names, new_val, curr_val, log_label):
        nonlocal content
        if new_val is not None and new_val != curr_val:
            timeline_entries.append(f"{log_label} transitioned from {curr_val} to {new_val}")
            pattern = r'(\-\s+\*\*(?:' + '|'.join(display_names) + r'):\*\*\s*)([A-Za-z0-9_-]+)'
            if re.search(pattern, content, re.IGNORECASE):
                content = re.sub(pattern, r'\g<1>' + str(new_val), content, flags=re.IGNORECASE)
            else:
                content += f"\n- **{display_names[0]}:** {str(new_val)}"
            return new_val
        return curr_val

    curr_rca = update_bool_field("substatus_rca", ["RCA Found", "rca_found", "substatus_rca"], substatus_rca, curr_rca, "RCA Found")
    curr_mitigated = update_bool_field("substatus_mitigated", ["Mitigated", "mitigated", "substatus_mitigated"], substatus_mitigated, curr_mitigated, "Mitigated")
    curr_fixed = update_bool_field("substatus_fixed", ["Fixed", "fixed", "substatus_fixed"], substatus_fixed, curr_fixed, "Fixed")
    curr_verified = update_bool_field("substatus_verified", ["Verified", "verified", "substatus_verified"], substatus_verified, curr_verified, "Verified")

    if timeline_entries:
        with open(state_path, "w") as f:
            f.write(content)
            
        timeline_path = os.path.join(incident_path, "timeline.md")
        timestamp = datetime.now(timezone.utc).isoformat()
        with open(timeline_path, "a") as f:
            for entry in timeline_entries:
                f.write(f"- **[{timestamp}]** [{operator}] {entry}\n")
