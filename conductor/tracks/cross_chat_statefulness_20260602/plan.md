# Implementation Plan - Cross-Chat Statefulness and Memory Synchronization

This document maps out the atomic tasks and test-driven checkpoints to implement shared, real-time default project/incident memory synchronization across SRE Web Dashboard and Telegram Bot channels.

---

## Phase 1: Shared Backend State Store & REST APIs
- [ ] Task: TDD - Write Unit Tests for Active State JSON Store and REST Endpoints
    - [ ] Create `tests/test_active_state.py`
    - [ ] Assert `GET /api/active-state` yields default parameters
    - [ ] Assert `POST /api/active-state` validates inputs, writes `investigations/active_state.json`, and returns updated coordinates
- [ ] Task: Implement Active State Store and REST Endpoints in `src/server.py`
    - [ ] Define initial in-memory defaults and path to `investigations/active_state.json`
    - [ ] Load persisted state from file on server start
    - [ ] Implement `GET /api/active-state` handler
    - [ ] Implement `POST /api/active-state` handler supporting project and incident updates
    - [ ] Verify test suite passes (`uv run pytest tests/test_active_state.py`)
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

---

## Phase 2: Telegram Bot Integration
- [ ] Task: TDD - Write Unit Tests for Telegram Command Interceptors for Selection and Projects
    - [ ] Create `tests/test_telegram_active_state.py`
    - [ ] Assert `/select` command updates the shared state store
    - [ ] Assert `/setproject` command updates the shared state store
    - [ ] Assert `/status` command returns the formatted status card containing project_id, incident_id, and incident status summary
    - [ ] Assert `/restart` command triggers process replacement or signals self-restart
- [ ] Task: Implement Selection/Project/Status/Restart Updates inside Telegram bot loop in `src/server.py`
    - [ ] Update `/select` handler to hit `POST /api/active-state` state update routine
    - [ ] Update `/setproject` handler to hit `POST /api/active-state` state update routine
    - [ ] Handle `/status` command (and `🚨 Status Check` menu button) to query active state, load incident context, and return a concise card summary
    - [ ] Handle `/restart` command to dispatch confirmation and programmatically execute self-restart via `os.execv`
    - [ ] Log active state switches dynamically within the incident's `chat.json` log
    - [ ] Verify test suite passes (`uv run pytest`)
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

---

## Phase 3: Web UI Dashboard Rendering & Real-time Alignment
- [ ] Task: TDD - Write Integration Tests for Web UI Poll & State Synchronization
    - [ ] Add tests verifying `/api/active-state` coordinates align with UI active states
- [ ] Task: Implement Sticky Top Bar Pill-Badges in Web Frontend
    - [ ] Modify `src/static/index.html` to add a transparent, sticky pill badge widget showing active project & incident
    - [ ] Add premium glowing neon styles in `src/static/index.css` for pill-badges
    - [ ] Make default badges clickable: clicking manually selects/loads that incident or project
- [ ] Task: Implement Real-time Workspace Alignment in `src/static/index.js`
    - [ ] Update front-end polling cycle to request `/api/active-state`
    - [ ] If default project or incident changes from the current UI selection, automatically load/align focus to it in real-time
    - [ ] Add a subtle, non-intrusive glow notification overlay when alignment shifts
    - [ ] Run full E2E verify suite (`uv run pytest`)
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)
