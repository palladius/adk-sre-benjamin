# Implementation Plan: Unified Incident Lifecycle & Multi-Agent Observability

## Phase 1: Globally Unique Incident Identifiers (UUIDv4)
- [x] Task: Generate and propagate UUIDv4 in IncidentContext (45fddb6)
    - [x] Write unit tests for UUIDv4 generation on incident creation
    - [x] Implement UUIDv4 generation during `IncidentContext` initialization
    - [x] Update ADK agent initialization to propagate the incident UUID in agent metadata
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Globally Unique Incident Identifiers (UUIDv4)' (Protocol in workflow.md)

## Phase 2: Multi-Agent Unified Logging
- [x] Task: Implement Local and Google Cloud Logging (e42e59e)
    - [x] Write unit tests for local JSONL logging schema and text fallback outputs
    - [x] Implement local JSONL logging with configurable path and log rotation/fallbacks
    - [x] Write unit tests for Google Cloud Logging client integration using ADC
    - [x] Implement GCP Cloud Logging integration with structured JSON payloads
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Multi-Agent Unified Logging' (Protocol in workflow.md)

## Phase 3: Discord Incident War-Rooms & Human Steering
- [ ] Task: Implement Discord Bot Channel Creation
    - [ ] Create unit tests and mocks for Discord API interactions (channel creation/bot connection)
    - [ ] Implement dynamic Discord channel creation in Comms Lead (Madhavi) using discord.py
- [ ] Task: Implement Discord Human @mention routing
    - [ ] Write tests for intercepting Discord messages and routing mentions
    - [ ] Implement message event listener to intercept mentions of specific ADK agent roles
    - [ ] Route the request to the target agent, execute their skills/tools, and reply to the Discord channel
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Discord Incident War-Rooms & Human Steering' (Protocol in workflow.md)
