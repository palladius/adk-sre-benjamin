# Implementation Plan: Unified Incident Lifecycle & Multi-Agent Observability

## Phase 1: Globally Unique Incident Identifiers (UUIDv4) [checkpoint: a49ef2e]
- [x] Task: Generate and propagate UUIDv4 in IncidentContext (45fddb6)
    - [x] Write unit tests for UUIDv4 generation on incident creation
    - [x] Implement UUIDv4 generation during `IncidentContext` initialization
    - [x] Update ADK agent initialization to propagate the incident UUID in agent metadata
- [x] Task: Conductor - User Manual Verification 'Phase 1: Globally Unique Incident Identifiers (UUIDv4)' (Protocol in workflow.md) (0adc943)

## Phase 2: Multi-Agent Unified Logging [checkpoint: bfc4967]
- [x] Task: Implement Local and Google Cloud Logging (e42e59e)
    - [x] Write unit tests for local JSONL logging schema and text fallback outputs
    - [x] Implement local JSONL logging with configurable path and log rotation/fallbacks
    - [x] Write unit tests for Google Cloud Logging client integration using ADC
    - [x] Implement GCP Cloud Logging integration with structured JSON payloads
- [x] Task: Conductor - User Manual Verification 'Phase 2: Multi-Agent Unified Logging' (Protocol in workflow.md) (55d3bdd)

## Phase 3: Discord Incident War-Rooms & Human Steering [checkpoint: 9f35914]
- [x] Task: Implement Discord Bot Channel Creation (4fdf3f4)
    - [x] Create unit tests and mocks for Discord API interactions (channel creation/bot connection)
    - [x] Implement dynamic Discord channel creation in Comms Lead (Madhavi) using discord.py
- [x] Task: Implement Discord Human @mention routing (88f6562)
    - [x] Write tests for intercepting Discord messages and routing mentions
    - [x] Implement message event listener to intercept mentions of specific ADK agent roles
    - [x] Route the request to the target agent, execute their skills/tools, and reply to the Discord channel
- [x] Task: Conductor - User Manual Verification 'Phase 3: Discord Incident War-Rooms & Human Steering' (Protocol in workflow.md) (f962771)

