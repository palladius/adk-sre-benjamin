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
* **Client-side Rendering & Compilation:** **Viz.js CDN Library** (for client-side Graphviz DOT SVG compilation)
* **Client-side Router:** **HTML5 History API** (for SPA path-based routing fallbacks)


## 📢 5. Communication & Integrations
* **Real-time & HITL Notifications:** **Telegram Bot API**
  * *Rationale:* Instant mobile push alerts with interactive callback buttons for human-in-the-loop approvals.
* **Formal Ticketing & Bug Filing:** **GitHub Issues API & ServiceNow**
  * *Rationale:* Standard logging for post-incident reviews, compliance audits, and team tracking.

---

# Aligned Architectural Decisions (v1.13)

Based on the interactive alignment interview (`/grill-me`), the following structural and design boundaries are established:

1. **Agent Topology & Orchestration:**
   - **Model:** Explicit Scripted Workflow. Instead of a single-tier ADK hierarchical tree, each specialized Lead is instantiated as a standalone framework module.
   - **Orchestration:** A dedicated master controller programmatically drives sequential and parallel tasks, cleanly handling high-granularity subagent interactions (e.g. Ops Agent delegating to Logs/Metrics/Mutation).

2. **Incident State & Recovery:**
   - **Model:** Shared `IncidentContext` object.
   - **Durability:** The context is dynamically hydrated and serialized to local files (`state.md` and `raw_audit.jsonl`) by the Scribe Agent, ensuring zero loss of operational history in the event of an orchestrator restart.

3. **Discovery Wiki Layout:**
   - **Model:** Directory-to-Index Compiler ("Karpathy autoupdate").
   - **Structure:** Permanent GCP asset audits are compiled into discrete, clean Markdown files per `project_id` matching the layout `wiki/gcp/<PROJECT_ID>/README.md`. VPC networks, databases, and GCE instances are cross-linked to form a semantic, self-indexing topology.

4. **Human-In-The-Loop (HITL) Gate:**
   - **Model:** Terminal Keyboard Prompts (`input()`) for out-of-the-box local SRE operations, with an extensible path to integrate interactive Telegram callbacks and microphone voice transcriptions.

5. **Operations Interface:**
   - **Model:** Domain-Specific ADK Function Tools (e.g., `query_logs`, `get_cpu_metrics`). The Ops Agent interacts through strictly structured, whitelisted function parameters rather than raw shell tools.

6. **Large Asset Standardization & Provenance (Registry):**
   - **Model:** An `artifacts_registry.json` index is maintained by Scribe inside `investigations/INC-XYZ/artifacts/`.
   - **Lineage (Provenance):** Every downloaded or generated large file (e.g., a huge 55MB log, CSV report, or database dump) is cataloged with its size, checksum, and exact source command (e.g., `gcloud logging ...` or `MCP://google-workspace/drive.downloadFile(fileId=...)`).
   - **Caching:** If the same command or MCP function is re-requested within the incident context, the system serves the cached local copy to avoid network overhead and API quota consumption.
   - **Referential Separation:** To prevent LLM context bloating, large files are kept in the `/artifacts/` folder. Only a summarized diagnostic digest is fed to the agents, while the primary Scribe timeline references the relative file path.


