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
   * An **always-visible SRE chat assistant** powered by the Gemini 2.5 Flash API.
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
PYTHONPATH=. uv run python3 src/cli.py telegram set "605724096" "8936005425:AAEjkDi0r25p2vKpTkkopAgLpXSwESFilLI"
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
   * **`📋 List Incidents`**: Lists all active and historical incidents recorded inside the SRE repository.
   * **`☁️ Target Project`**: Displays the active GCP Project context.
   * **`🆔 Select Incident`**: Instructs how to safely swap active incident coordinates.
2. **Context-Switching Control Commands**:
   * **`/select <Incident_ID>`**: Dynamically switches the active incident chat and status context (e.g. `/select INC-PLAYGROUND`).
   * **`/setproject <Project_ID>`**: Updates the core GCP Project ID config inside `.env` on-the-fly and syncs active environment states.
3. **🎙️ Voice Note Transcription & SRE Actioning (On-The-Fly STT)**:
   * **Send Voice Notes**: You can record and send standard Telegram **voice messages** or audio notes directly to the bot.
   * **Auto-Transcription**: The bot immediately downloads the audio file, processes it through Google's Gemini 2.5 Flash API with zero local dependencies, and replies back with a clean text transcription.
   * **Intelligent Actioning**: The transcribed text is automatically routed as a direct operational chat message to SRE Commander Benjamin, updating the incident's timeline chat log in real-time, mirroring onto the Web Dashboard, and replying back with the commander's strategic SRE instructions!
4. **Active Incident Conversation Mirroring**:
   * Any text message or transcribed voice command you send is automatically appended to the incident's `chat.json` logs, enabling **flawless dual-screen alignment** between your Telegram app and your Web Command Dashboard!

---

## 📟 4. SRE Command Line Tools Reference

Project Benjamin ships with several automation scripts configured in the project `justfile` or accessed via the direct python CLI:

| Command | Purpose | Description |
| :--- | :--- | :--- |
| `just web` | **Relaunch Web Server** | Runs the Python http dashboard server on port `8080` |
| `just test` | **Run Test Deck** | Runs all 49 pytest checkers and integration suites |
| `just simulate` | **Incident Simulator** | Launches the complete E2E Incident ICS delegation simulation |
| `just clean` | **Purge Cache** | Wipes build files, test covers, and local project crawl JSONs |
| `PYTHONPATH=. uv run python3 src/cli.py telegram set <ID> <TOKEN>` | **Telegram Connect** | Connects and saves Telegram credentials to `.env` |
| `PYTHONPATH=. uv run python3 src/cli.py telegram send "<MSG>"` | **Telegram Send** | Sends a live, direct alert message to Telegram |
