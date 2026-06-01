# Specification: comms_integration_20260601

## Overview
This specification defines the interfaces, patterns, and behaviors for integrating the **Communications Lead (Madhavi)** with external channels: **Telegram Bot API** (real-time notification hub) and **GitHub Issues** (ticketing and incident resolution ledger). It bridges Project Benjamin's internal SRE command chain with external engineering coordinators and stakeholders.

## Requirements & Scope

1. **Telegram Channel Dispatcher (`src/comms_telegram.py`):**
   - Read `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from environment variables (`.env`).
   - If credentials are empty or missing, run in a high-fidelity **Mock Notification Mode** logging dispatches to `investigations/INC-XXXX/artifacts/telegram_feed.json` so the suite is fully verified in standard CI environments.
   - Send beautifully structured Markdown alert payloads on critical state transitions:
     - **Active Declaration:** Brief incident header, target project, and trigger event.
     - **Triage Alerts:** Notice of logs query results and metric collection.
     - **Logistics Safety Alerts:** Detailed risk gate summaries including command, risk category (LOW, MEDIUM, HIGH), and safety status.
     - **Resolution Alerts:** Final summary, mutation applied, and closure state.

2. **GitHub Ticketing Engine (`src/comms_github.py`):**
   - Read `GITHUB_TOKEN` and `GITHUB_REPO` (e.g. `owner/repo`) from environment variables.
   - If credentials are missing, execute in **Mock Issue Mode** saving issue payloads under `investigations/INC-XXXX/artifacts/github_issue.json`.
   - Implement the following lifecycle coordinates:
     - `create_incident_issue(incident_id: str, trigger_event: str, project_id: str) -> str`: Creates a tracking ticket titled `🚨 ACTIVE: [incident_id] - [trigger_event]` returning an issue number or mock ID.
     - `add_issue_comment(issue_id: str, author: str, message: str)`: Posts timeline updates as formal issue comments as events occur.
     - `close_incident_issue(issue_id: str, summary: str)`: Appends a final resolution comment and closes the issue ticket successfully.

3. **Orchestrator Integration:**
   - Modify the simulation engine (`run_simulation.py`) to hydrate Madhavi's channel dispatchers on each event.
   - Register the telegram feed and github ticket artifacts in `artifacts_registry.json` for live UI synchronization.

## Acceptance Criteria
- Executing `just simulate` successfully dispatches mock or live Telegram messages and creates mock or live GitHub issues.
- All artifact files (`telegram_feed.json`, `github_issue.json`) are compiled and indexed in the registry.
- Standard test coverage for the communication engines remains above >80%.
