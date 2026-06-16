# Implementation Plan - Graduate local state to work in the Cloud (Track: graduate_local_state_cloud_20260604)

## Phase 1: Database Setup and Connection
- [x] Task: Install dependencies
  - [x] Add `psycopg2-binary` to `requirements.txt`.
- [x] Task: Database connection helper
  - [x] Create `src/db.py` to handle PostgreSQL connection pooling and connection resilience.
  - [x] Define database credentials env reader (DB_USER, DB_PASS, DB_NAME, DB_HOST).

## Phase 2: Schema Initialization
- [x] Task: Write migrations/DDL
  - [x] Write startup schema creator in `src/db.py` to build `incidents`, `chats`, and `active_state` tables.

## Phase 3: Update Server State Persistence
- [x] Task: Adapt server state routines
  - [x] Refactor `get_active_state()` and `save_active_state()` in `src/server.py` to use database storage.
  - [x] Refactor `parse_incident_folder()` and incident listing endpoints to query database rows.

## Phase 4: Verification
- [x] Task: Add test deck
  - [x] Implement unit tests validating database connectivity and state fallback mechanism.
