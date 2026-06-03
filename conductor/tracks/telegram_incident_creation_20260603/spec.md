# Specification: Interactive Telegram Incident Creation (Track: telegram_incident_creation_20260603)

## 1. Overview
This feature enables SRE operators to dynamically declare and initialize new incidents directly from Telegram via voice messages or text notes. Using the Gemini API, the bot parses the incident's event type and target project context. If the project context is fuzzy or missing, the bot presents an interactive project selection menu. Once confirmed, it scaffolds the incident and starts the SRE command pipeline.

---

## 2. Functional Requirements

### 2.1 Intent Detection & Parsing via Gemini
- **Passive Listening**: Any incoming text command or voice note transcription is evaluated to detect if the user wants to declare/create a new incident (e.g. "I'd like to create a new incident...", "declare incident GKE cluster down").
- **Gemini Parsing**:
  - The bot uses the Gemini API to parse the message.
  - Returns structured JSON containing:
    - `is_incident_declaration`: boolean
    - `event_type`: string (inferred event name like `gke_cluster_down` or `latency_high`, defaulted to `manual_alert` if not specified)
    - `project_id`: string (parsed project name, or `null` if not found or fuzzy)
    - `description`: string (short summary of the incident)

### 2.2 Interactive Slash Command `/newincident`
- Supports `/newincident` command to start a guided interactive wizard.
- Tapping or typing `/newincident` prompts the user: "Please describe the incident (e.g. 'GKE cluster down in us-central1')".

### 2.3 Project ID Resolution Menu (Strict Prerequisite)
- **Mandatory Project Context**: An incident MUST ALWAYS have a valid, resolved `project_id` associated with it. Scaffolding, timelines, and alert routing cannot be initialized without a resolved project context. This requirement applies universally to all incidents, including mock incidents and simulation runs.
- **Unresolved/Fuzzy Project Handling**: If the parsed `project_id` does not match any project returned by `get_discovered_projects()`, or is missing/fuzzy:
  - The bot suspends incident initialization.
  - The bot sends a message: "🔍 I could not resolve the target project. Please select from the active project registry below to proceed:"
  - Includes an inline keyboard displaying all discovered projects (loaded dynamically via `get_discovered_projects()`).
  - Tapping a project completes the resolution step, allowing initialization to resume.

### 2.4 Incident Scaffolding & Launch Pipeline
- Once the project ID is resolved and event details are confirmed:
  - Scaffolds a new incident folder under `investigations/INC-YYYYMMDD-<random>` using `scaffold_incident` scaffolding with the resolved `project_id` explicitly attached.
  - Automatically initializes Scribe files `state.md` and `timeline.md`.
  - Triggers the SRE orchestrator pipeline (`run_incident_flow`).
  - Sends a Telegram confirmation card:
    - "✅ *SRE Investigation Started: INC-YYYYMMDD-XXXX*"
    - Lists active incident details and includes inline keyboard buttons: `📋 List Incidents`, `☁️ List Projects`, `🚨 Status Check`.
    - Automatically updates the active shared state (`POST /api/active-state`) so the Web UI switches focus to the new incident immediately!

---

## 3. Acceptance Criteria
- Tapping/typing `/newincident` triggers the creation workflow.
- Sending voice notes with "create incident" or equivalent phrases successfully extracts the event type and starts the flow.
- If the project is unresolved, a project picker menu is shown. Selecting a project continues the launch.
- Creating the incident successfully scaffolds files under `investigations/` and updates `/api/active-state`.
