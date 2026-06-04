# Specification: Graduate local state to work in the Cloud (Track: graduate_local_state_cloud_20260604)

## 1. Overview
This track graduates the local file-based state storage of Project Benjamin (incident logs, chat history, and the active coordinator state) to a PostgreSQL database hosted in Google Cloud SQL. This ensures multi-instance safety, session consistency, and scalability in a Cloud Run environment.

---

## 2. Functional Requirements
* **Database Connection Pooling**: Initialize a connection pool (using `psycopg2` or similar) pointing to Cloud SQL PostgreSQL.
* **Database Schema**:
  - `incidents`: Store incident details (incident_id, status, target_project, trigger_event, created_at, updated_at).
  - `chats`: Store tactical chat history linked by incident ID.
  - `active_state`: Track the single active project and active incident coordinates.
* **Storage Abstraction**: Update `src/server.py` and other modules to read and write state from the database if database credentials/configuration are present, falling back gracefully to local file storage if not.
* **Telegram Synchronization**: Enable Telegram query commands and interactive buttons to retrieve the active project/incident state dynamically from the database.

---

## 3. Acceptance Criteria
* DB tables are automatically created on server start if they do not exist.
* Selecting an incident or changing a project in the UI updates the state in the database.
* Post history and chats are saved to the database.
* Local files act as a fallback when database environment variables are omitted.
