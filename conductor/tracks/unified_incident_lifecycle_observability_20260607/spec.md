# Specification: Unified Incident Lifecycle & Multi-Agent Observability

## 1. Overview
This feature introduces unified tracing, auditing, and human steering across the incident lifecycle in Project Benjamin. We assign every incident a globally unique UUIDv4, log all agent interactions to both a local JSONL audit trail and Google Cloud Logging, and integrate Discord as the collaborative war-room platform where humans can interactively steer specialized ADK agents via `@mentions`.

## 2. Functional Requirements

### 2.1 Globally Unique Incident Identifiers (UUIDv4)
- **Incident Init**: On alert ingestion or manual incident declaration, the Incident Commander (Benjamin) or Scribe generates a UUIDv4.
- **Context Propagation**: The UUID is injected into the shared `IncidentContext` and propagated in the metadata of all downstream agents (Benjamin, Madhavi, Ops Agent, Planning Agent, Logistics Agent, Scribe Agent).
- **Correlation**: Every message, action, log, and communication generated during the incident lifecycle must include this UUID.

### 2.2 Multi-Agent Unified Logging
- **Local JSONL Audit-Trail**:
  - Log all inter-agent messages, thought sequences, and tool executions.
  - File path is configurable via `.env` under `BENJAMIN_AUDIT_LOG_PATH` (defaults to `./logs/benjamin-audit.jsonl`).
  - Logs must contain: timestamp, incident_uuid, incident_id, sender agent, receiver agent, message, severity, and context.
  - Write a clean human-readable text line alongside the JSON entry for quick terminal grepping.
- **Google Cloud Logging**:
  - Send the same structured JSON payload directly to Google Cloud Logging using the Google Cloud Logging Python SDK.
  - Authenticate using Application Default Credentials (ADC).
  - Configurable GCP Project ID via `GCP_PROJECT_ID` in `.env`.

### 2.3 Discord Incident War-Rooms & HITL Interaction
- **Discord Bot & Channel Creation**:
  - Use `discord.py` to run the Discord integration.
  - Configure the bot token via `DISCORD_TOKEN` in `.env`.
  - When an incident is initialized, Madhavi dynamically creates a dedicated Discord channel (e.g., `#inc-<short-uuid>-<incident-name>`).
  - The bot handles sending notifications and timeline updates to this channel.
- **Human @mention Steering**:
  - The Discord bot listens for messages in the incident channels.
  - If a user mentions a specific agent (e.g., `@Ops Agent check replica lag`), that agent intercepts the mention.
  - The agent executes its corresponding ADK tools or skills, and replies back to the channel thread.

## 3. Non-Functional Requirements
- **Performance**: Logging to Cloud Logging should not block the main execution of the agents (use asynchronous/background logging where appropriate).
- **Robustness**: If Discord or Cloud Logging fails, the local logging and core execution of the incident command must continue unaffected.
- **Security**: The `.env` file containing tokens and project IDs must never be checked into git.

## 4. Acceptance Criteria
- [ ] A unique UUIDv4 is generated and attached to new incidents.
- [ ] Local JSONL audit logs are generated at the specified path with the correct schema.
- [ ] Audit logs are successfully sent to GCP Cloud Logging when credentials are present.
- [ ] A Discord bot successfully creates a channel for new incidents.
- [ ] The Discord bot parses `@mentions` to specific agents and routes them to trigger the corresponding agent logic, posting the response back.

## 5. Out of Scope
- Fully automated production cloud infrastructure setup for Discord/GCP (manual config of Discord bot token and ADC is assumed).
- Support for other chat systems (like Slack or Telegram mirroring) within this specific track.
