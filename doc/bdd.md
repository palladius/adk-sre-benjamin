# 🏰 Project Benjamin - SRE Agentic IMAG Framework (v1.13)
*A secure, agentic SRE multi-agent framework fully aligned with Google's IMAG (Incident Management At Google) ICS structure.*

---

## 🛠️ 1. Implementation Stack

Project Benjamin is designed as a production-grade, highly secure automation harness. The core implementation stack consists of the following foundational pillars:

1. **Strict IMAG ICS Command Hierarchy:** 
   Instead of chaotic, conversational agent swarms, Project Benjamin enforces a **very strict top-down operational hierarchy** based on Google's **IMAG (Incident Management At Google) Incident Command System (ICS)**. Under this model, organizational and operational decisions rest with the Incident Commander and are executed from the top down.
2. **ADK + Skills (Python-Powered Engine):**
   The framework is built using the **Antigravity Development Kit (ADK)**. Specifically, it leverages the **Python implementation of ADK**, as it is currently the only ADK runtime that fully supports the modular **"Skills" architecture**. This allows the framework to import, share, and execute complex, pre-authored SRE skills, procedural playbooks, and diagnostic pipelines seamlessly.
3. **SRE Extension Integration:**
   The framework acts as the agentic brain wrapping your existing **SRE Extension**. It leverages the SRE Extension's underlying CLI utilities, helper scripts, and automated bash commands to safely inspect, query, and remediate target cloud and system infrastructures.

---

## 🛰️ 2. IMAG Incident Command System (ICS) Structure

Under the IMAG ICS model, the framework is structured as a **hub-and-spoke hierarchical tree** of 4 distinct functional Leads reporting directly to a single central leader (all organized under strict, clean boundaries):

```
                              +-----------------------------------+
                              |   ServiceNow / GCP Alerts / SLOs  |
                              +-----------------+-----------------+
                                                | (Operational Triggers)
                                                v
                              +-----------------+-----------------+
                              | [Incident Commander (IC)]         |
                              | Role (default: Benjamin)          |
                              +--------+--------+--------+--------+
                                       |        |        |
         +-----------------------------+        |        +-----------------------------+
         |                                      |                                      |
         v (Delegate Communication)             v (Delegate Operations)                v (Delegate Logistics)
  +------+-------------------+           +------+-------------------+           +------+-------------------+
  | [Communications Lead]    |           |  [Agent 3: Ops Agent]    |           |  [Agent 6: Logi Agent]   |
  | Role (default: Madhavi)  |           |  Operations Lead         |           |  Logistics Lead          |
  +------+-------------------+           +------+-------------------+           +------+-------------------+
         |                                      |                                      |
         | (Updates & Bug Filing)               | (Diagnostics & Remediation)          | (Credentials, Quotas & Risk)
         v                                      v                                      v
  +------+-------------------+           +------+-------------------+           +------+-------------------+
  | • Telegram Chat          |           | • Diagnostic Subagents   |           | • Risk Assessor          |
  | • GitHub / ServiceNow    |           | • Logs Agent             |           | • Resource Manager       |
  +--------------------------+           | • Metrics Agent          |           +--------------------------+
                                         | • Mutation Agent         |
                                         +--------------------------+
                                                        ^
                                                        | (Delegate Documenting & Runbooks)
                                                        v
                                                 +------+-------------------+
                                                 |  [Agent 4: Planning Agt] |
                                                 |  Planning Lead           |
                                                 +------+-------------------+
                                                        |
                                                        | (Filing Chronology, Docs & Assets)
                                                        v
                                                 +------+-------------------+
                                                 | • Memini (Memory)        |
                                                 | • Discovery Agent        |
                                                 | • Scribe: Scrivano Foss|
                                                 +--------------------------+
```

### 🏎️ 1. Incident Commander: Benjamin (IC)
* **Visual:** Bald man, Ferrari cap, inside a castle.
* **IMAG Role:** **Incident Commander (IC)**. Holds overall responsibility for the incident's lifecycle and resolution.
* **Responsibility:** Exposes Pub/Sub and Webhook subscribers to ingest operational triggers (GCP Alerts, SLO violations, ServiceNow tickets). He creates the incident context, declares it active, and delegates the respective functional leads.

### 🔧 2. Operations Lead: Ops Agent
* **IMAG Role:** **Operations Lead (Ops)**. In charge of making tactical, hands-on changes and investigations to mitigate/resolve the immediate problem.
* **Responsibility:** Formulates the active troubleshooting strategy, executes diagnostics, and drives recovery workflows.
* **ReadOnly Identity:** The Ops Agent is strictly **Read-Only** by default. To execute any state-altering modifications, it must request approval from the Logistics Lead and delegate execution to the Mutation Agent.
* **Delegates to:**
  * **Diagnostic Subagents:** Executes lightweight ReadOnly diagnostic commands, scrapes logs, and checks CPU/Memory metrics.
  * **Logs Agent:** Specialized in querying, streaming, and filtering massive text logs (e.g. from Google Cloud Logging). By isolating log search and parsing to this dedicated subagent, we prevent core agent token bloating.
  * **Metrics Agent:** Specialized in querying time-series data and monitoring metrics (e.g. CPU, RAM, throughput) from GCP Cloud Monitoring or Prometheus, checking thresholds and error budgets.
  * **Mutation Agent:** The physical remediator, guarded by an extremely strict **"bulletproof prompt" (prompt cazzuto)**, executing only approved writes (e.g. log rotation, service restarts) once cleared by the Logistics Lead.

### 📋 3. Planning Lead: Planning Agent
* **IMAG Role:** **Planning Lead (Planning)**. Supports other leads, tracks status, maintains the timeline, files tracking issues, and aligns documentation/postmortem resources.
* **Responsibility:** Manages all knowledge retrieval, cataloging, and postmortem indexing.
* **Delegates to:**
  * **Memini (Memory Agent):** Custodian of historical runbooks, incidents, and postmortems (*from the Latin 'remember'*). It is queried to find past solutions for recurring issues and logs the final postmortem of resolved incidents.
  * **Discovery Agent (GCP Asset & Security Auditor):** Autonomous asset discovery and security posture scanning. Crawls GCP resources on given `project_id`s, highlights security vulnerabilities (e.g., public GCS buckets, open firewalls), and formats them in interlinked Obsidian-style Wiki pages with an automatically updated index page (**Karpathy autoupdate**).
  * **Scribe Agent (Scrivano Fossati):** The chronicler of the incident. It manages the active **Investigation Folder** (`investigations/INC-YYYYMMDD-ID/`) and maintains the living `state.md` (representing the current "State of the World") and `timeline.md` (the "Running Doc" of executed commands and events). Every state transition is version-controlled via Git commits (`git commit`), providing a complete, audit-safe "Time Machine" of the incident's mental model and actions.

### ⚙️ 4. Logistics Lead: Logistics Agent
* **IMAG Role:** **Logistics Lead (Logistics)**. In charge of securing necessary resources, tools, software licenses, API quotas, credentials, and environmental requirements for the Operations team.
* **Responsibility:** Acts as the gatekeeper of resources and safety.
* **Delegates to:**
  * **Risk Assessment Agent:** Analyzes proposed operations and calculates the **Risk Coefficient** (High, Medium, Low). It decomposes complex commands (especially those containing shell **PIPES** like `|`, `&&`, `;`) into discrete parts to detect dangerous patterns before execution.
  * **Resource & Credential Manager:** Securely fetches active API keys, checks GCP service quotas/billing limits, validates environment variables, and ensures the target host has required dependencies (e.g. packages, Python venv) configured properly before the Mutation Agent runs.

### 📢 5. Communications Lead: Madhavi
* **IMAG Role:** **Communications Lead (CL)**. The *only* designated spokesperson communicating the incident's state to audiences outside the immediate team (including users, executives, and external stakeholders).
* **Responsibility:** Manages Slack updates, status page entries, sends periodic progress notifications to Telegram, and automates bug-filing/ticket updates in ServiceNow or GitHub.

---

## 🏰 3. The Legend & Iconography of Benjamin
* **The Tribute:** The project is named in honor of **Ben Treynor Sloss**, the legendary founder of the SRE discipline at Google.
* **The Visual Pun:** "Sloss" sounds like *"Schloss"* (German for Castle), and "Treynor" sounds like **Treno** (Italian for Train).
* **The Iconic Avatar:** The primary entry point agent is visually represented as a smiling bald man wearing a red **Ferrari cap** inside a medieval castle driving a train (named **Ben Treno**).

---

## 📋 4. BDD Specifications (Behavior-Driven Development)

### Feature 1: IMAG Top-Down Delegation
**As an** SRE Automation System  
**I want** the Incident Commander to ingest alerts and delegate to the four dedicated IMAG ICS Leads  
**So that** incident roles are strictly separated according to Google's best practices.

* **Scenario: Incident Commander activates the 4 ICS Leads on a Latency SLO Violation**
  * **Given** the Incident Commander's operational harness receives a GCP alert "frontend_latency_slo_violated"
  * **When** the Incident Commander declares the incident active
  * **Then** the Incident Commander delegates Operations to the Ops Agent (Ops Lead)
  * **And** delegates Communication to the Communications Lead
  * **And** delegates Planning to the Planning Agent (Planning Lead)
  * **And** delegates Logistics to the Logistics Agent (Logistics Lead)
  * **And** the Communications Lead notifies the user on Telegram and updates the status page.

---

### Feature 2: Planning Lead diagnostics and Runbook check
**As an** SRE Planning Lead  
**I want** to search for historical solutions and run resource discovery  
**So that** the Operations Lead has full context of the incident and target assets.

* **Scenario: Memini runbook retrieval & Discovery Agent GCP audit**
  * **Given** the Ops Agent requires diagnostic context
  * **When** the Planning Lead queries Memini for "DATABASE_CONN_TIMEOUT"
  * **And** instructs the Discovery Agent to crawl GCP project "prod-db-999"
  * **Then** Memini returns the past postmortem "Restart GCS cluster (Risk Low)"
  * **And** the Discovery Agent identifies active SQL instances and audits GCS bucket exposure, highlighting public buckets in **bold red warnings**
  * **And** compiles everything into the Obsidian Wiki notes, triggering a Karpathy autoupdate.

---

### Feature 3: Logistics Lead Risk Gate & Credential Provisioning
**As an** SRE Operations Lead  
**I want** the Logistics Lead to validate my credentials and calculate risk  
**So that my proposed mutations are safe and authenticated before execution.**

* **Scenario: High-risk drop database request gets blocked by Logistics**
  * **Given** the Ops Agent proposes to execute `DROP DATABASE prod_db` to recover from a corruption
  * **When** the Logistics Agent evaluates the command
  * **And** runs the Risk Assessment Agent which returns a **Risk Coefficient** of `HIGH`
  * **Then** the Logistics Agent **blocks** the execution of the Mutation Agent
  * **And** notifies the Communications Lead of the blocked high-risk escalation
  * **And** the Communications Lead logs a ServiceNow ticket and requests explicit human approval on Telegram.

---

### Feature 4: Dynamic Communications Lead Rename & SRE Extension Skills Loader
**As an** SRE Architect  
**I want** to dynamically configure the Communications Lead agent's name via environment variables  
**And** automatically discover and load skills from the cloned SRE Extension Git repository (`https://github.com/gemini-cli-extensions/sre`)  
**So that the framework dynamically adapts to organizational roles and leverages external expert playbooks.**

* **Scenario: Renaming the Communications Lead to Lucia and resolving Git skills**
  * **Given** the environment variable `COMMS_LEAD_NAME` is configured as `Lucia`
  * **And** the environment variable `GEMINI_CLI_SRE_DIR` points to `/home/riccardo/git/sre`
  * **When** Project Benjamin initializes the SRE Command leads
  * **And** the `SkillAdapter` resolves the `anomaly-detection` skill
  * **Then** the Communications Lead's agent name is set to `Lucia`
  * **And** her system instruction prompt replaces all `Madhavi` references with `Lucia`
  * **And** the `SkillAdapter` successfully parses `anomaly-detection/SKILL.md` from the SRE extension repository
  * **And** appends the instructions directly to the hydrated ADK agent instructions.

---

## 🛠️ 5. Tech Stack & ADK (Antigravity Development Kit)

| Technology | 🟢 Pros (Advantages) | 🔴 Cons (Disadvantages) |
| :--- | :--- | :--- |
| **Go (Golang)** | • Single self-contained static binary.<br>• Blazing fast, minimal memory footprint.<br>• Perfect for cross-platform deployment. | • More rigid for rapid experimentation with LLM/agentic workflows. |
| **Python** | • Fast prototyping, ideal for cognitive reasoning.<br>• Outstanding library ecosystem (LangGraph, ADK, GenAI SDKs). | • Package and virtual environment dependency management overhead. |

---

## 📊 6. Risk Coefficient Model (Logical Matrix Example)

```python
RISK_MATRIX = {
    "read_only": "LOW",           # queries, cat, grep, state checks
    "restart_service": "LOW",     # systemctl restart non-critical
    "config_change": "MEDIUM",    # modifying .env or configs
    "package_install": "MEDIUM",  # apt-get install, pip install
    "database_mutation": "HIGH",  # drop, truncate, migrate
    "system_reboot": "HIGH",      # sudo reboot, shutdown
    "destructive_rm": "HIGH"      # rm -rf outside temp dirs
}
```


---

## 🔮 7. Open Points & Active Brainstorming (Google SRE Collaboration)

While the high-level architecture of Project Benjamin is established, we are actively brainstorming several technical implementation decisions to share with our Google SRE/Engineering colleagues. We welcome feedback on these specific trade-offs:

### ❓ Point 1: Event Transport & Coupling between Ops Agent and Scribe
How should the real-time event feed (`Async Event Feed`) travel from the **Ops Agent** to the **Scribe Agent** on a local Mac-mini/workstation system?
*   **Option A: In-Memory Async Queue (`asyncio.Queue`)**
    *   *Pros:* Extremely fast, zero external dependencies, zero disk I/O overhead.
    *   *Cons:* Volatile. If the execution harness crashes, pending timeline events not yet flushed to disk are lost forever.
*   **Option B: File-Based Tailing (`raw_audit.jsonl`)**
    *   *Pros:* Highly durable. The Ops Agent appends raw execution events to a local JSONL file; the Scribe Agent tails/polls this file to build the human-friendly Markdown documents. Survives agent crash/restarts.
    *   *Cons:* Disk I/O contention, slightly higher latency, file polling overhead.
*   **Option C: Lightweight Local Pub/Sub (e.g., SQLite-backed queue or local Redis)**
    *   *Pros:* Robust decoupling, structured schemas, support for multiple concurrent listeners (e.g., Madhavi or secondary logging systems).
    *   *Cons:* Introduces external operational dependencies (e.g., managing a local Redis daemon or database connection locking).

### 🟢 Point 2: Event Filtering & Log Noise Mitigation (La "Merda nei Log") - RESOLVED FOR METRICS
SRE commands often emit massive amounts of text or data points. We have split this problem into two domains:
1.  **Numerical Metric Data (Resolved):** Our custom SRE Extension skills delegate high-frequency metric polling to dedicated subagents. A local Python script (using Pandas/Matplotlib) processes raw dataframes (even those with 10,000+ records), computes high-level statistics (min, max, average), and generates a compact **ASCII sparkline / trend chart** (sparkline string). This allows the LLM and the `running_doc.md` to see the performance trend in less than 80 characters, with zero token pollution.
2.  **Raw Text Logs (Active Brainstorming):** For massive log outputs (e.g., standard Kubernetes stack traces), we rely on targeted `grep` operations or regex streaming filters via the dedicated **Logs Agent**, ensuring only matching lines or high-level summaries reach the Scribe Agent's timeline. We also use referential separation, writing the raw full output to a standalone file (e.g., `logs/cmd-04-output.txt`) inside the Investigation Folder, and only writing a short reference link in the main timeline.

### ❓ Point 3: File Concurrency & Write Ownership
Within the shared **Investigation Folder** (`investigations/INC-XYZ/`), how do we prevent write-write conflicts?
*   **Option A: Strict Scribe Write-Ownership (Recommended)**
    *   *Model:* ONLY the Scribe Agent is allowed to write to `state.md` and `running_doc.md`. The Ops Agent is strictly read-only relative to the investigation folder; it merely emits signals.
    *   *Pros:* Elegant, prevents write conflicts, single source of truth for updates.
*   **Option B: Shared File Access with Locking**
    *   *Model:* Both Ops Agent and Scribe Agent can write directly to files. Uses POSIX file locks (`fcntl` or file-locking libraries) to coordinate writes.
    *   *Pros:* Immediate, low-latency updates for direct commands.
    *   *Cons:* Risk of file contention, potential deadlock bugs, and disorganized summaries.

### 🟢 Point 4: Git Metadata & Commit Pollution - RESOLVED (Git Notes)
We version-control state changes and timelines to provide an audit-safe "Time Machine" of the incident. To prevent polluting the main repository history with dozens of micro-commits (e.g., 50 commits during a 20-minute incident), we have resolved this design decision:
*   **The Solution: Git Notes (`git notes`) / Git Annotations**
    Instead of polluting the main commit history with noisy operational commits, we utilize the native Git feature **Git Notes** (`git notes`). The Scribe Agent appends structured operational notes, state changes, and congetture directly to existing commit objects as metadata. This keeps the primary repository history 100% clean and pristine for human SRE developers, while fully preserving the high-granularity audit trail and "Time Machine" state transitions for our AI agentic team.
