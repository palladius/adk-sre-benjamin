# Implementation Plan - Cross-Chat Statefulness and Memory Synchronization

This document maps out the atomic tasks and test-driven checkpoints to implement shared, real-time default project/incident memory synchronization across SRE Web Dashboard and Telegram Bot channels.

---

## Phase 1: Shared Backend State Store & REST APIs
- [x] Task: TDD - Write Unit Tests for Active State JSON Store and REST Endpoints
    - [x] Create `tests/test_active_state.py`
    - [x] Assert `GET /api/active-state` yields default parameters
    - [x] Assert `POST /api/active-state` validates inputs, writes `investigations/active_state.json`, and returns updated coordinates
- [x] Task: Implement Active State Store and REST Endpoints in `src/server.py`
    - [x] Define initial in-memory defaults and path to `investigations/active_state.json`
    - [x] Load persisted state from file on server start
    - [x] Implement `GET /api/active-state` handler
    - [x] Implement `POST /api/active-state` handler supporting project and incident updates
    - [x] Verify test suite passes (`uv run pytest tests/test_active_state.py`)
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

---

## Phase 2: Telegram Bot Integration
- [x] Task: TDD - Write Unit Tests for Telegram Command Interceptors for Selection and Projects
    - [x] Create `tests/test_telegram_active_state.py`
    - [x] Assert `/select` command updates the shared state store
    - [x] Assert `/setproject` command updates the shared state store
    - [x] Assert `/status` command returns the formatted status card containing project_id, incident_id, and incident status summary
    - [x] Assert `/restart` command triggers process replacement or signals self-restart
- [x] Task: Implement Selection/Project/Status/Restart Updates inside Telegram bot loop in `src/server.py`
    - [x] Update `/select` handler to hit `POST /api/active-state` state update routine
    - [x] Update `/setproject` handler to hit `POST /api/active-state` state update routine
    - [x] Handle `/status` command (and `🚨 Status Check` menu button) to query active state, load incident context, and return a concise card summary
    - [x] Handle `/restart` command to dispatch confirmation and programmatically execute self-restart via `os.execv`
    - [x] Log active state switches dynamically within the incident's `chat.json` log
    - [x] Verify test suite passes (`uv run pytest`)
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

---

## Phase 3: Web UI Dashboard Rendering & Real-time Alignment
- [x] Task: TDD - Write Integration Tests for Web UI Poll & State Synchronization
    - [x] Add tests verifying `/api/active-state` coordinates align with UI active states
- [x] Task: Implement Sticky Top Bar Pill-Badges in Web Frontend
    - [x] Modify `src/static/index.html` to add a transparent, sticky pill badge widget showing active project & incident
    - [x] Add premium glowing neon styles in `src/static/index.css` for pill-badges
    - [x] Make default badges clickable: clicking manually selects/loads that incident or project
- [x] Task: Implement Real-time Workspace Alignment in `src/static/index.js`
    - [x] Update front-end polling cycle to request `/api/active-state`
    - [x] If default project or incident changes from the current UI selection, automatically load/align focus to it in real-time
    - [x] Add a subtle, non-intrusive glow notification overlay when alignment shifts
    - [x] Run full E2E verify suite (`uv run pytest`)
- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

