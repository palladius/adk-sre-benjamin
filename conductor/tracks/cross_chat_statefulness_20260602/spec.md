# Specification - Cross-Chat Statefulness and Memory Synchronization

This specification defines the design, architecture, and requirements for synchronizing state (specifically the active target **GCP Project ID** and the **Incident ID**) between the Web UI Dashboard and the Telegram Bot in Project Benjamin. 

---

## 1.0 Overview
Currently, the Web UI and the Telegram Bot operate with independent UI views. While conversations are mirrored, selecting an incident or a project in one interface does not align the active focus in the other. 
This track introduces a centralized memory store (`investigations/active_state.json`) that tracks the "Default GCP Project" and the "Default Incident ID". It implements real-time synchronization between the two channels, so that selecting Y on Telegram updates the Web UI default selection in real-time, and vice-versa, while allowing operators to override selections locally.

---

## 2.0 Functional Requirements

### 2.1 Central Shared State Persistence
* Maintain a lightweight JSON state file at `investigations/active_state.json` containing:
  ```json
  {
    "default_project_id": "sre-next",
    "default_incident_id": "INC-20260602-7307",
    "updated_at": "2026-06-02T08:52:00Z"
  }
  ```
* The server should load this state in-memory on startup.
* Provide clean API endpoints to query and update the shared state:
  * `GET /api/active-state`: Returns the active defaults.
  * `POST /api/active-state`: Updates the default project and/or incident IDs, writes to file, and updates memory.

### 2.2 Telegram Bot Integration & Triggering
* When the operator selects an incident via `/select <Incident_ID>` or sets a project via `/setproject <Project_ID>` on Telegram:
  * The bot must hit the server's state update routine.
  * Update the shared `investigations/active_state.json` parameters dynamically.

### 2.3 Web Dashboard Alignment & Rendering
* **Sticky Top Bar Buttons**: Add a glowing, premium, transparent pill-badge panel at the top of the SRE Dashboard showing:
  * `📌 Active Project: [sre-next]` (Clickable: automatically selects the project and runs discovery if not yet crawled).
  * `📌 Active Incident: [INC-20260602-7307]` (Clickable: automatically loads/selects the incident workspace).
* **Real-time Workspace Alignment**: 
  * The Web UI's background poll cycle queries `GET /api/active-state`.
  * If a state change initiated from Telegram is detected (i.e. default project or incident has changed), the Web UI automatically shifts focus/selection to align in real-time, while presenting a subtle notification overlay.

### 2.4 Telegram `/status` Quick Inspection Command
* **Focused Telegram Status**: The Telegram bot must handle the command `/status` (or the persistent `🚨 Status Check` reply button tap) to fetch coordinates from `GET /api/active-state` and return a clean, concise card:
  1. Active target Project ID.
  2. Active Incident ID.
  3. Short incident status (e.g. `AWAITING_APPROVAL`, `ACTIVE`, `CLOSED`).
  4. A brief, readable one-sentence narrative summarizing the current state.

### 2.5 Server `/restart` Process Reload Command
* **Server Self-Restart command**: The Telegram bot and REST API must expose a `/restart` command.
* **Mechanism**: When triggered, the server dispatches a confirmation message `"🔄 Server restarting. Reloading fresh code from disk..."` and programmatically reloads its process using `os.execv(sys.executable, [sys.executable] + sys.argv)`. This ensures that all memory caches are cleared, and any newly pulled git code changes are loaded instantly without needing shell shell process management intervention!

---

## 3.0 Non-Functional Requirements
* **Zero Dependencies**: Implementation must use pure standard library Python, standard JS, and standard CSS.
* **Low Latency**: State synchronization endpoints must complete within <50ms.
* **Audit Trail**: Any change to the active project or incident must be logged in the active incident's `chat.json` to keep operators aligned.

---

## 4.0 Acceptance Criteria
* Selecting an incident via Telegram (`/select`) or clicking standard keyboard menus immediately updates `investigations/active_state.json`.
* The Web UI automatically loads the newly selected default incident / project in real-time.
* Web Dashboard displays a glowing sticky header containing clickable pill badges for the default project and incident.
* Clicking those badges manually triggers the corresponding load action in the UI.
* All unit tests pass cleanly without regressions.
