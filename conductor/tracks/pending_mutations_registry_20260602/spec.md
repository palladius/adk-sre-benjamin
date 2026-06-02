# Specification - Pending Mutation Approvals Queue

This specification details the design, architecture, and requirements for implementing a structured, persistent **Pending Approvals Queue** for proposed SRE incident mutations (actions).

---

## 1.0 Overview
Currently, when the SRE Incident Commander proposes a dangerous mutation (e.g. `systemctl restart mysql`), the incident is paused on a single safety gate, which blocks standard chat interaction. However, in complex scenarios, the agentic framework might generate *multiple* distinct conjectures/options to resolve the problem. 
This track introduces a structured queue of **Pending Approvals**. Each item in the queue represents a proposed mutation with safety details, dynamic risk emojis, risk reasoning, and justification for the action. The operator can view this list, selectively approve/reject commands from either Telegram or the Web UI, and audit the results.

---

## 2.0 Functional Requirements

### 2.1 Structured Queue Data Schema
Each proposed mutation in the queue must contain:
1. `id`: Unique incremental ID (e.g., `cmd-01`).
2. `command`: The raw proposed command string (e.g. `kubectl drain node-1`).
3. `timestamp`: ISO-8601 timestamp when proposed.
4. `risk_factor`: Risk level mapped to standard color emojis:
   * 🟢 **LOW**: Safe, standard diagnostics/read queries.
   * 🟡 **MEDIUM**: Moderate impact, standard service status checks.
   * 🟠 **HIGH**: Disruptive, log rotation/reloads.
   * 🔴 **CRITICAL**: Destructive, drop tables, restart databases.
5. `risk_reason`: Contextual explanation from the Logistics Lead explaining the risk.
6. `justification`: Contextual justification from the Operations Lead explaining why we believe this command will resolve the incident (e.g., "Clears stuck TCP sockets causing the SLO alert").

### 2.2 Persistence and REST API
* **File persistence**: Save the pending approvals array within `<incident_folder>/pending_approvals.json` and automatically compile a clean visualization table inside the incident's `state.md`.
* **API Endpoints**:
  * `GET /api/incidents/<id>/pending`: Returns the active pending mutation queue.
  * `POST /api/incidents/<id>/pending`: Adds a new mutation to the queue.
  * `POST /api/incidents/<id>/pending/<cmd_id>/approve`: Approves the specific mutation by executing it, logging in timeline/chat, and removing it from the queue. Supports a non-mandatory JSON body parameter `"comment": "operator feedback string"` which is logged and piggybacked to the LLM agent prompt.
  * `POST /api/incidents/<id>/pending/<cmd_id>/reject`: Rejects the mutation, logging it as blocked, and removing it from the queue. Supports a non-mandatory JSON body parameter `"comment": "operator feedback string"` to redirect model strategies.

### 2.3 Telegram `/pending` Commands & Inline Keyboards
* Introduce a Telegram bot command: `/pending`.
* It lists all active pending approvals in the current incident formatted with their risk emojis, justifications, and risk reasons.
* It displays dynamic inline keyboard buttons for each item (e.g., `💥 Approve cmd-01` | `❌ Reject cmd-01`), enabling operators to clear selections directly from mobile!
* Supports adding optional text comments by simply typing a message right after clicking a button or typing it inline.

### 2.4 Web Dashboard "Pending Actions Queue" Widget
* Implement a styled card widget in the SRE dashboard workspace showing the list of proposed commands.
* Display each item's command, risk badge with color emoji, justification, and independent clickable approval/rejection button panel controls.
* **Non-Mandatory Operator Comment Input**: Provide a text input field next to the action buttons for each command, allowing the operator to type feedback (e.g. `"go with it bro"` or `"I think youre draining the wrong service for reason XXXX"`).
* Clicking **Approve** or **Reject** immediately executes/rejects the command with the accompanying feedback comment, records the operation in the central tailing audit, routes the comment back to the SRE Incident Commander agent loop, and removes the item from the queue.

---

## 3.0 Acceptance Criteria
* The SRE Commander can queue multiple concurrent mutations using `POST /api/incidents/<id>/pending`.
* Queue is fully persisted inside `pending_approvals.json` and displayed in `state.md`.
* Telegram `/pending` successfully lists all items and permits instant callback approval with explosion emojis.
* The Web UI renders a gorgeous, premium list of mutations with individual approval buttons.
* All unit tests pass cleanly without regressions.
