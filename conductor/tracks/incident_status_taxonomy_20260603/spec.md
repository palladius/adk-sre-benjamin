# Specification: Incident Status Taxonomy (Track: incident_status_taxonomy_20260603)

## 1. Overview
Establishes a formal status enum and metadata tracking system for incidents, resolving the generic 'UNKNOWN' status. All transitions are logged to maintain an audit trail for post-mortems.

---

## 2. Functional Requirements
* **Status Schema**: Define statuses: `NEW`, `ONGOING`, `CLOSED`.
* **Substatus Modifiers**: Track `rca_found` (bool), `mitigated` (bool), `fixed` (bool), and `verified` (bool).
* **Audit Trail**: Every change of status or substatus writes a chronological log entry into the incident's timeline.

---

## 3. Acceptance Criteria
* Incident state defaults to `NEW` on creation.
* Incident timeline lists all status changes with timestamps and operator details.
* Dashboard and bot show status/substatus badge details clearly.
