# Implementation Plan: Unified Incident Lifecycle & Multi-Agent Observability

## Phase 1: Globally Unique Incident Identifiers (UUIDv4)
- [ ] Task: Generate and propagate UUIDv4 in IncidentContext
    - [ ] Write unit tests for UUIDv4 generation on incident creation
    - [ ] Implement UUIDv4 generation during `IncidentContext` initialization
    - [ ] Update ADK agent initialization to propagate the incident UUID in agent metadata
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Globally Unique Incident Identifiers (UUIDv4)' (Protocol in workflow.md)

## Phase 2: Multi-Agent Unified Logging
- [ ] Task: Implement Local and Google Cloud Logging
    - [ ] Write unit tests for local JSONL logging schema and text fallback outputs
    - [ ] Implement local JSONL logging with configurable path and log rotation/fallbacks
    - [ ] Write unit tests for Google Cloud Logging client integration using ADC
    - [ ] Implement GCP Cloud Logging integration with structured JSON payloads
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
