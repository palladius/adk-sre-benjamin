# 🏰 Project Benjamin - SRE Agentic IMAG Framework

> **A secure, agentic SRE multi-agent framework fully aligned with Google's IMAG (Incident Management At Google) ICS structure.**

---

## 🖥️ Live Incident Command Dashboard

Here is the latest screenshot of the **Project Benjamin Web Dashboard**, featuring real-time incident state monitoring, timeline tracking, and live incident simulation capabilities.

![Project Benjamin Web Dashboard](doc/web_screenshot.png)

---

## 🛠️ Architecture Stack

Project Benjamin is designed as a production-grade, highly secure SRE automation harness built upon the following pillars:

1. **Strict IMAG ICS Command Hierarchy**: Organizational and operational decisions rest with the Incident Commander and flow top-down to four specialized Leads to avoid chaotic, conversational agent swarms.
2. **ADK + Python-Powered Skills**: Built using the **Antigravity Development Kit (ADK)** for Python, leveraging its modular "Skills" architecture to execute SRE playbooks and diagnostic pipelines.
3. **SRE Extension Integration**: Serves as the agentic brain wrapping the [SRE Extension](https://github.com/gemini-cli-extensions/sre), using its CLI utilities and helper scripts to inspect and remediate system infrastructures safely.

---

## 🛰️ IMAG Incident Command System (ICS) Structure

The framework is structured as a hub-and-spoke hierarchical tree reporting directly to the Incident Commander:

```
                              +-----------------------------------+
                              |   ServiceNow / GCP Alerts / SLOs  |
                              +-----------------+-----------------+
                                                | (Operational Triggers)
                                                v
                              +-----------------+-----------------+
                              |      [Agent 1: Benjamin]          |
                              |   Incident Commander / Lead (IC)  |
                              +--------+--------+--------+--------+
                                       |        |        |
         +-----------------------------+        |        +-----------------------------+
         |                                      |                                      |
         v (Delegate Communication)             v (Delegate Operations)                v (Delegate Logistics)
  +------+-------------------+           +------+-------------------+           +------+-------------------+
  |  [Agent 2: Madhavi]      |           |  [Agent 3: Ops Agent]    |           |  [Agent 6: Logi Agent]   |
  |  Communications Lead     |           |  Operations Lead         |           |  Logistics Lead          |
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
                                                 | • Scribe Agent (Scrivano)|
                                                 +--------------------------+
```

### 🏎️ Incident Commander: Benjamin (IC)
* **Identity**: Represents a bald man wearing a Ferrari cap in a medieval castle (*Schloss*), driving a train (*Treno*).
* **Role**: Assumes overall responsibility for the incident's lifecycle and resolution. Ingests operational alerts and coordinates the functional Leads.

### 🔧 Operations Lead (Ops Agent)
* **Role**: Executes diagnostics and recovery workflows.
* **Security Model**: Strictly **Read-Only** by default. Any state-altering changes require clearance from Logistics and delegation to the Mutation Agent.

### 📋 Planning Lead (Planning Agent)
* **Role**: Tracks incident timeline, updates the living documentation (`state.md` and `timeline.md`), and automates postmortem indexing.
* **Delegates**:
  * **Memini**: Custodian of historical runbooks and past incidents.
  * **Discovery Agent**: Crawls GCP assets and highlights potential security vulnerabilities.
  * **Scribe Agent**: Manages the version-controlled Git history of the `investigations/` folders.

### ⚙️ Logistics Lead (Logistics Agent)
* **Role**: Acts as the gatekeeper of safety, environment configurations, and quotas.
* **Delegates**:
  * **Risk Assessment Agent**: Decomposes proposed terminal commands and computes safety coefficients.
  * **Resource Manager**: Securely provides credentials and verifies API/billing quotas.

### 📢 Communications Lead: Madhavi
* **Role**: The single source of truth for external status updates (Slack, Telegram feeds, and GitHub/ServiceNow issue trackers).

---

## 🚀 Getting Started

Ensure you have [uv](https://github.com/astral-sh/uv) installed, then execute the following tasks:

### 1. Install Dependencies
```bash
just install
```

### 2. Launch the Web Dashboard
```bash
uv run python3 src/server.py
```
Open your browser and navigate to: [http://localhost:8080/](http://localhost:8080/)

### 3. Run E2E Incident Simulation
Click the **Trigger Live Simulation** button in the dashboard, or run it directly via the terminal:
```bash
just simulate
```

### 4. Execute Test Suite
```bash
just test
```
