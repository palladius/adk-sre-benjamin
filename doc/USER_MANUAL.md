# 🏰 Project Benjamin SRE User Manual

Welcome to **Project Benjamin**, a production-grade automation and command platform for Site Reliability Engineering (SRE), built using Google's **Agent Development Kit (ADK) for Python** and structured around the **IMAG (Incident Management At Google) Incident Command System (ICS)**.

This manual explains how to operate the SRE Command Center, navigate GCP project discoveries, execute interactive agent diagnostics, and configure live Telegram alerting integrations.

---

## 🖥️ 1. SRE Dashboard Layout

The SRE Dashboard is designed as a three-column command console, giving you unified control over incidents and project telemetry.

```
+-------------------+-----------------------------------+-------------------+
|  Control Center   |         Dynamic Workspace         |    AI Co-Pilot    |
|     (Sidebar)     |             (Middle)              |      (Right)      |
|                   |                                   |                   |
| - GCP Project ID  | - Dynamic Telemetry Metrics       | - Persistent chat |
| - Discovery Search| - Timeline Logging Streams        |   with Benjamin   |
| - Clickable History| - SRE Least-Privilege Verification|   (Incident IC)   |
| - Active Incidents| - Collapsible Asset Panels        |                   |
+-------------------+-----------------------------------+-------------------+
```

### 🛰️ Three-Column Workspace Structure
1. **Left Sidebar (Control Center)**:
   * **GCP Project Config**: Inputs the target Project ID. Click the `🔍` icon to start resource crawls.
   * **GCP Projects History**: Displays cached projects. Click any project to load its audited inventory.
   * **Simulation Trigger**: Click **Trigger Live Simulation** to initiate end-to-end incident drill sequences.
   * **Incident Repository**: Lists historical and active SRE incident records.
2. **Middle Panel (Dynamic Workspace)**:
   * Dynamically switches between the **Incident Playbook & Diagnostic Metrics View** and the **GCP Project Asset Discovery panels** (GKE, GCS, VPC, GCE VMs, SQL, Cloud Run).
   * Features interactive telemetry graphs, safety gate clearance controls, and live broadcast dispatch logs.
3. **Right Panel (SRE AI Co-Pilot Chat Console)**:
   * An **always-visible SRE chat assistant** powered by the dynamically resolved Gemini API.
   * Automatically ingests active screen metadata, status changes, and target project parameters on every message, providing genuine context-aware SRE troubleshooting guidance.

---

## 🛡️ 2. Verbose Vulnerabilities Audits

To maintain a clean, space-efficient interface capable of tracking hundreds of cloud assets, detailed warning descriptions are collapsed by default.

### 🔍 Inspecting Vulnerabilities
* **Warning Icon (🚨)**: If a resource is flagged as exposed/vulnerable, a red warning emoji appears in its header. Hovering over `🚨` shows the warning category.
* **Metric Cards**: The **Exposed/Vulnerable** box at the top highlights active warnings.
* **Full Verbose Modal**: Clicking either a card's `🚨` icon or the **Exposed/Vulnerable** metric card opens a glassmorphic report modal containing:
  * ⚠️ Direct vulnerability impact descriptions.
  * ⚙️ Expandable JSON raw metadata blocks (`View raw metadata`).
  * 🔗 Direct authenticated console shortcuts (`Open in GCP Console`) pointing directly to the vulnerable resource inside the Google Cloud Console for rapid remediation.

---

## 📢 3. Telegram Alerts Integration Setup

The SRE framework is pre-wired to dispatch live event notifications to engineering Telegram channels or chat groups during incident simulation runs.

### 🛠️ Method A: Setup via the SRE CLI (Recommended)
You can configure and test your Telegram bot credentials directly into your environment using the SRE Agent CLI harness:

```bash
# 1. Set your Telegram alert channel/group ID and bot HTTP API token
PYTHONPATH=. uv run python3 src/cli.py telegram set "<CHAT_ID>" "<BOT_TOKEN>"

# 2. Send a live test alert to verify the connection is active
PYTHONPATH=. uv run python3 src/cli.py telegram send "Hello, SRE! Live alert test complete."
```

*Example:*
```bash
PYTHONPATH=. uv run python3 src/cli.py telegram set "605724096" "8936005425:AAEjkDi0rXXXXXXX..."
PYTHONPATH=. uv run python3 src/cli.py telegram send "Castle Security Breach Simulated!"
```

The set command will automatically parse, secure, and write the credentials into your local `.env` configuration file, and the send command will instantly dispatch a live alert using the configured credentials.

### 📝 Method B: Manual Configuration
Alternatively, open your local `.env` file and append the following variables manually:

```env
# Telegram Bot Integration Keys
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
TELEGRAM_CHAT_ID="your_telegram_chat_id"
```

### 💬 Two-Way Interactive SRE Chatbot & Voice Commands

Once your credentials are connected, `@SREBenjaminBot` functions as a fully interactive two-way SRE Command Console directly inside Telegram. Message the bot `/start` or `help` to initialize the control hub interface:

1. **Structured Quick Navigation Menu**:
    * **`🚨 Status Check`**: Instantly prints the live status, target project, alert trigger event, and timeline logs count for the active selected incident.
    * **`📋 List Incidents`** (or command `/incidents`): Displays the 5 latest incidents as clickable inline keyboard buttons, prefixed with `🟢` (open/active) or `⚪` (closed/resolved) status emojis for rapid context switching.
    * **`☁️ Set Project`** (or command `/projects`): Displays discovered GCP projects as clickable inline keyboard buttons for rapid project context switching.
    * **`🆔 Select Incident`**: Displays a helpful guide explaining how to target a specific incident ID.
2. **Context-Switching Control Commands (4 Primitives)**:
    * **`/incidents`**: Lists the 5 latest incidents as clickable inline buttons.
    * **`/projects`**: Lists discovered GCP projects as clickable inline buttons.
    * **`/incident <id>`** (legacy support for `/select <id>`): Directly sets the active SRE incident context.
    * **`/project <id>`** (legacy support for `/setproject <id>`): Directly sets the active GCP project context.
3. **🎙️ Voice Note Transcription & SRE Actioning (On-The-Fly STT)**:
   * **Send Voice Notes**: You can record and send standard Telegram **voice messages** or audio notes directly to the bot.
   * **Auto-Transcription**: The bot immediately downloads the audio file, processes it through Google's dynamically resolved Gemini API with zero local dependencies, and replies back with a clean text transcription.
   * **Intelligent Actioning**: The transcribed text is automatically routed as a direct operational chat message to SRE Commander Benjamin, updating the incident's timeline chat log in real-time, mirroring onto the Web Dashboard, and replying back with the commander's strategic SRE instructions!
4. **Active Incident Conversation Mirroring**:
   * Any text message or transcribed voice command you send is automatically appended to the incident's `chat.json` logs, enabling **flawless dual-screen alignment** between your Telegram app and your Web Command Dashboard!

### 🔒 5. Human-in-the-Loop (HITL) Safety Gates & Approvals

When a dangerous system mutation (e.g. `systemctl restart mysql`) is proposed by SRE Commander Benjamin, the incident is placed on a safety gate hold, transitioning to the `AWAITING_APPROVAL` status. During this hold:
* **Safety Gate Interception**: Standard chat commands are intercepted, and the Telegram bot dispatches a safety confirmation warning containing the proposed command, safety risk level, and a specialized confirmation keyboard.
* **Specialized Clearance Buttons**:
  * **`💥 Yes, I am sure`**: Authorizes the mutation command. This executes the action via `resume_simulation`, recovers SRE services, closes the incident, logs the response in the incident's `chat.json` feed, and resets the operator's Telegram keyboard back to standard navigation.
  * **`❌ No, abort mutation`**: Aborts and blocks the mutation. This halts the operation, updates the incident state as blocked/aborted, logs the abort action in `chat.json`, and resets the Telegram keyboard back to standard.
* **Two-Way Synchronization**: If an operator authorizes or rejects the pending mutation directly from the Web Command Dashboard, the active Telegram session is instantly notified, sending a confirmation log message and automatically resetting the operator's Telegram keyboard back to standard.

---

## 🌐 6. Multi-View Project Workspace, Editable Wiki & Graphviz Topologies

Project Benjamin provides an interactive, highly visual project exploration workspace. For any targeted GCP Project ID entered in the sidebar or discovered in your network, you can toggle between four rich, deep-linked views:

### 1. 🔍 Discovery Audit
* **Purpose**: Raw asset classification tab showing your discovered Compute Engine VMs, GKE clusters, Cloud SQL instances, Cloud Run serverless deployments, GCS storage buckets, and VPC networks in an ugly but highly functional, clean and collapsible asset panel grid.
* **Telemetry**: Automatically indicates whether the telemetry was loaded from dynamic local mock caches or a live authenticated Google Cloud API sweep.

### 2. 📝 Project Wiki (Editable Markdown)
* **Purpose**: An interactive Markdown documentation notebook. 
* **Editing & Preview**: Features a dual-pane editor (left) and live-rendered HTML preview (right) for recording project structure, custom runbooks, or structural highlights.
* **Regex Compiler**: Ingests basic markdown syntax (`#`, `##`, `- bullet points`, `**bold**`, `` `inline code` ``) with zero external library dependencies.
* **Saving & Syncing**: Click **💾 Save Wiki** to post the notes back to the server. The document is automatically persisted inside `discover/gcp-project/<project-id>.md`.

### 3. ☸️ Logical Graph (Graphviz DOT)
* **Purpose**: A logical dependency mapping tool.
* **Editing**: Edit custom Graphviz DOT dependency scripts inside a clean text editor.
* **Compiling**: Instantly compiles your Graphviz scripts to premium interactive SVGs client-side using Viz.js CDN modules.
* **Saving & Syncing**: Click **💾 Save Logical Graph** to persist the DOT file inside `discover/gcp-project/<project-id>.dot`.

### 4. 🌐 Physical Network Graph (Auto-Generated VPC Topology)
* **Purpose**: An interactive, dynamic topology map displaying VPC networks, subnets, and active resource attachments.
* **Automated Map Generation**: Dynamically maps VM instances, GKE control planes, GCS buckets, and SQL databases, grouping them inside beautifully styled VPC cluster subgraphs.
* **Visual Annotations**: Exposed resources are colored red and styled with alert metrics, allowing you to instantly pinpoint security breaches at a glance.

### 🧭 Global Router & Clouds Directory Page
* **Deep Links**: Navigate seamlessly using clean SPA paths (`/projects/<id>` or `/clouds`) powered by the HTML5 History API (with fallback support in `src/server.py`).
* **Clouds Directory**: View the index of active multi-cloud accounts (Google Cloud, AWS, Azure, Vercel) showing dynamic active project counts and deep-linking straight into detailed discovery views.

---

## 📟 4. SRE Command Line Tools Reference

Project Benjamin ships with several automation scripts configured in the project `justfile` or accessed via the direct python CLI:

| Command | Purpose | Description |
| :--- | :--- | :--- |
| `just check` | **Check Environment** | Validates python dependencies, `.env` file structure, active gcloud configuration, and impersonated SA credentials |
| `just test-logging` | **Validate Cloud Logging** | Queries live GCP Cloud Logging using active credentials and outputs formatted warnings/errors |
| `just test-metrics` | **Validate Cloud Metrics** | Queries live GCP Cloud Monitoring and outputs CPU time-series lists |
| `just web` | **Relaunch Web Server** | Runs the Python http dashboard server on port `8080` |
| `just test` | **Run Test Deck** | Runs all 49 pytest checkers and integration suites |
| `just simulate` | **Incident Simulator** | Launches the complete E2E Incident ICS delegation simulation |
| `just clean` | **Purge Cache** | Wipes build files, test covers, and local project crawl JSONs |
| `PYTHONPATH=. uv run python3 src/cli.py telegram set <ID> <TOKEN>` | **Telegram Connect** | Connects and saves Telegram credentials to `.env` |
| `PYTHONPATH=. uv run python3 src/cli.py telegram send "<MSG>"` | **Telegram Send** | Sends a live, direct alert message to Telegram |
