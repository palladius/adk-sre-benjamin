# Implementation Plan - Interactive Telegram Incident Creation

This document maps out the implementation phases, atomic tasks, and test-driven checkpoints to build the interactive Telegram Incident Creation flow in Project Benjamin.

---

## Phase 1: Gemini Intent Parser & Slash Command
- [ ] Task: TDD - Write Unit Tests for Incident Declaration Intent Parser
    - [ ] Create `tests/test_declaration_parser.py`
    - [ ] Test that `parse_declaration_intent` identifies incident declarations from transcript texts
    - [ ] Assert that GKE/Run/SQL events and project IDs are correctly extracted or set to null
- [ ] Task: Implement Gemini Intent Parser in `src/discovery.py` or new `src/declaration.py`
    - [ ] Create `parse_declaration_intent(text: str)` calling live Gemini API or mock parser (depending on `MOCK_TOOLING`)
    - [ ] Verify test suite passes (`uv run pytest tests/test_declaration_parser.py`)
- [ ] Task: TDD - Write Unit Tests for `/newincident` slash command
    - [ ] Assert `/newincident` prompts the user for incident details
- [ ] Task: Implement `/newincident` command handler in `src/server.py`
    - [ ] Update Telegram bot polling loop in `src/server.py` to capture `/newincident`
    - [ ] Store active wizard step context for the chat session
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Gemini Intent Parser & Slash Command' (Protocol in workflow.md)

---

## Phase 2: Project Resolution & Scaffolding Pipeline
- [ ] Task: TDD - Write Unit Tests for Project Resolution Menus
    - [ ] Assert that if project is fuzzy/null, the bot responds with project picker inline buttons
    - [ ] Assert that picking a project triggers incident scaffolding and launches the orchestrator
- [ ] Task: Implement Project ID Resolution & Launch in `src/server.py`
    - [ ] Handle fuzzy project results: check against `get_discovered_projects()`. If missing/fuzzy, build and send project picker inline keyboard.
    - [ ] In callback query handler, intercept `resolve_project:<project_id>` callback queries
    - [ ] Once project is resolved, call `scaffold_incident` and `run_incident_flow`
    - [ ] Synchronize coordinates by posting to `POST /api/active-state`
    - [ ] Send Telegram launch confirmation message with navigation buttons
    - [ ] Verify test suite passes (`uv run pytest`)
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Project Resolution & Scaffolding Pipeline' (Protocol in workflow.md)
