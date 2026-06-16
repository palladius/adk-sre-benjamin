# Implementation Plan - Incident Archival & Deletion (Track: incident_delete_archive_20260603)

## Phase 1: State & Endpoint Updates
- [x] 79173ae Task: Extend Incident properties
  - [x] Add `archived` attribute in JSON incidents.
  - [x] Filter active incidents endpoint.

## Phase 2: UI Buttons & Modals
- [x] 79173ae Task: Sidebar & Chat UI
  - [x] Add Archive button inside list item.
  - [x] Add Delete button showing confirmation dialog before calling DELETE endpoint.
- [x] 79173ae Task: Telegram Bot Command
  - [x] Support `/archive` command.

## Phase 3: Auto-Archival Scheduler
- [x] 79173ae Task: Cron Auto-Archive
  - [x] Write a clean auto-archive check running daily.
