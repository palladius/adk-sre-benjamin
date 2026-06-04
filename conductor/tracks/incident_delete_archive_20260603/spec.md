# Specification: Incident Archival & Deletion (Track: incident_delete_archive_20260603)

## 1. Overview
Adds capabilities to archive or delete incidents. Archive removes them from active lists without deleting raw files. Delete removes files after showing a confirmation dialog. Auto-archive scans for old closed incidents.

---

## 2. Functional Requirements
* **Archival state**: Hide archived incidents from dashboard sidebar and bot views.
* **Confirmation Dialog**: Require explicit verification modal before delete actions.
* **Auto-Archive Job**: Automatically archive incidents closed more than 3 days ago (configurable).

---

## 3. Acceptance Criteria
* Clicking Archive hides the incident.
* Clicking Delete prompts user; confirming deletes JSON file.
* Incidents closed > 3 days are moved to archived state.
