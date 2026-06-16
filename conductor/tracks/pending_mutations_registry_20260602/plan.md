# Implementation Plan - Pending Mutation Approvals Queue

This document maps out the implementation phases, atomic tasks, and test-driven checkpoints to build the structured SRE Mutation Pending Approvals Queue in Project Benjamin.

---

## Phase 1: Shared JSON Persistence & REST Endpoints
- [x] Task: TDD - Write Backend Tests for Mutation Queue API
    - [x] Create `tests/test_mutation_queue.py`
    - [x] Test `GET /api/incidents/<id>/pending` returns empty list originally
    - [x] Test `POST /api/incidents/<id>/pending` queues a mutation with schema validation (risk emoji, justification, risk reason)
    - [x] Test `POST /api/incidents/<id>/pending/<cmd_id>/approve` triggers mock execution and removes from queue
    - [x] Test `POST /api/incidents/<id>/pending/<cmd_id>/approve` with a non-mandatory `"comment"` payload, asserting it is logged and parsed into the timeline
    - [x] Test `POST /api/incidents/<id>/pending/<cmd_id>/reject` with a `"comment"` payload to redirect agent strategies
- [x] Task: Implement Mutation Queue Backend in `src/server.py`
    - [x] Create data schema helper and file loader/writer for `<incident_folder>/pending_approvals.json`
    - [x] Implement automatic Markdown table compiler to visually append pending queue inside `state.md`
    - [x] Implement `GET` and `POST` handlers under `/api/incidents/<id>/pending`
    - [x] Implement approval/rejection endpoints with timeline, audit logger, and comment parsing hookups
    - [x] Implement prompt injection helper that "piggybacks" the operator's comment back into the active agent conversation context
    - [x] Verify test suite passes (`uv run pytest tests/test_mutation_queue.py`)
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

---

## Phase 2: Telegram Command `/pending` and Inline Buttons
- [ ] Task: TDD - Write Tests for Telegram Bot Mutation Queue Integration
    - [ ] Assert `/pending` bot action returns structured text with risk emojis
    - [ ] Assert callback button dispatches execute approval API calls with feedback routing
    - [ ] Assert `📥 Pending Approvals` is present in the reply keyboard when incident state is active
- [ ] Task: Implement `/pending` bot command and inline keyboards in `src/server.py`
    - [ ] Handle `/pending` command to query `/api/incidents/<id>/pending` and render a formatted text response with 🟢, 🟡, 🟠, 🔴 indicators
    - [ ] Attach interactive inline keyboard markup for quick approvals/rejections of each item
    - [ ] Wire callback update listeners to approve or reject items in real-time, supporting reply-to-comment inputs
    - [ ] Update the `send_telegram_menu` keyboard layout to dynamically include the **`📥 Pending Approvals`** reply button once the incident context/state is active/consolidated
    - [ ] Verify test suite passes (`uv run pytest`)
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

---

## Phase 3: Web UI dashboard Mutations Queue Widget
- [ ] Task: Design and Implement SRE Mutations Queue Widget in HTML & CSS
    - [ ] Modify `src/static/index.html` to add a new sidebar or workspace card called "Pending SRE Mutation Actions Queue"
    - [ ] Style glowing glassmorphic grid list elements showing proposed commands, risk status, risk reasons, and justifications in Outfit font
    - [ ] Add a non-mandatory Operator Comment Text Input field next to the action buttons for each command
    - [ ] Add styled "Approve" (with explosion emoji `💥`) and "Reject" buttons
- [ ] Task: Implement Interactive Frontend Logic in `src/static/index.js`
    - [ ] Update frontend poll cycles to fetch `/api/incidents/<id>/pending` and render list items dynamically
    - [ ] Bind click handlers to extract input comments and POST them as JSON body to approval/rejection REST endpoints
    - [ ] Trigger real-time workspace workspace refresh upon successful mutation approval or rejection
    - [ ] Run full test suite validation (`uv run pytest`)
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)
