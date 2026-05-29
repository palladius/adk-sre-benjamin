# Technology Stack

This document details the software, languages, databases, and third-party integrations comprising **Project Benjamin**.

---

## 💻 1. Core Programming Language & SDKs
* **Language:** Python 3.11+
  * *Rationale:* The Python environment is standard for SRE diagnostics and supports the Modular Skills framework natively.
* **Agent Framework:** **Google Agent Development Kit (ADK) for Python**
  * *Rationale:* Implements modular, reliable agent structures, callbacks, and native tool integrations.

## 🕸️ 2. Multi-Agent Orchestration
* **Pattern:** **Pure ADK Hierarchical Tree**
  * *Topology:* Incident Commander (Benjamin) coordinates tasks and delegates to Operations (Ops Agent), Planning (Planning Agent), Logistics (Logistics Agent), and Communications (Madhavi).
  * *Flow:* Top-down, strictly non-conversational to maintain clean operational boundaries.

## 💾 3. Storage & State Management
* **Incident Timeline & Logs:** Local File System (Markdown)
  * *Rationale:* High durability, auditability, and absolute transparency.
* **Event Transport / Coupling:** **File-Based Tailing (`raw_audit.jsonl`)**
  * *Rationale:* Operations logs are durable, survive agent crashes, and allow Scribe to tail/parse and replay them without synchronous write blocking.
* **File Concurrency:** **Strict Scribe Write-Ownership**
  * *Rationale:* Only Scribe writes to `state.md` and `timeline.md` in the active investigation folder. Ops Agent is strictly read-only relative to the directory and only writes to `raw_audit.jsonl` to emit signals.
* **Audit Trail:** **Git Notes (`git notes`)**
  * *Rationale:* Appends fine-grained operational event logs and metadata to Git commits without polluting the main repository timeline.

## ⚙️ 4. Operational Requirements & Tooling
* **Credentials Management:** **Local `.env` file loaded via `python-dotenv`**
  * *Rationale:* Easy configuration decoupling, securely guarded by `.gitignore`.
* **Testing Toolchain:** **`pytest` + `pytest-asyncio` + `pytest-cov`**
  * *Rationale:* Industry-standard Python testing suite offering rich async testing capabilities and coverage percentage reports.

## 📢 5. Communication & Integrations
* **Real-time & HITL Notifications:** **Telegram Bot API**
  * *Rationale:* Instant mobile push alerts with interactive callback buttons for human-in-the-loop approvals.
* **Formal Ticketing & Bug Filing:** **GitHub Issues API & ServiceNow**
  * *Rationale:* Standard logging for post-incident reviews, compliance audits, and team tracking.
