# Implementation Plan - Incident Status Taxonomy (Track: incident_status_taxonomy_20260603)

## Phase 1: Database & Model Updates
- [x] c2957dd Task: Schema validation
  - [x] Update incident JSON structure to enforce status enums.
  - [x] Introduce fields: `status`, `substatus_rca`, `substatus_mitigated`, `substatus_fixed`, `substatus_verified`.

## Phase 2: Timeline Transition Logging
- [x] b29ecae Task: Log State Transitions
  - [x] Implement transition helper in `src/incident.py` writing updates to the incident timeline logs.

## Phase 3: Dashboard & Telegram Integration
- [x] b29ecae Task: UI Representation
  - [x] Update dashboard sidebar list and main pane to display status/substatus badges.
  - [x] Update Telegram command formats to report status metadata.
