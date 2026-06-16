import uuid

class IncidentContext:
    """Shared context for the SRE incident lifecycle, maintaining correlation identifiers."""
    def __init__(self, incident_uuid: str = None, **kwargs):
        self.incident_uuid = incident_uuid or str(uuid.uuid4())
        self.metadata = kwargs
        self.metadata["incident_uuid"] = self.incident_uuid
