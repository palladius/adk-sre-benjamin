# Implementation Plan - Incident Archival & Deletion (Track: incident_delete_archive_20260603)

## Phase 1: State & Endpoint Updates
- [ ] Task: Extend Incident properties
  - [ ] Add `archived` attribute in JSON incidents.
  - [ ] Filter active incidents endpoint.

## Phase 2: UI Buttons & Modals
- [ ] Task: Sidebar & Chat UI
  - [ ] Add Archive button inside list item.
  - [ ] Add Delete button showing confirmation dialog before calling DELETE endpoint.
- [ ] Task: Telegram Bot Command
  - [ ] Support `/archive` command.

## Phase 3: Auto-Archival Scheduler
- [ ] Task: Cron Auto-Archive
  - [ ] Write a clean auto-archive check running daily.
