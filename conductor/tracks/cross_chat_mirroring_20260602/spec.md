# Specification: Track cross_chat_mirroring_20260602

## 1. Overview
The goal of this track is to enable cross-visibility and full real-time mirroring between the SRE Web Dashboard chat panel (port 8080) and the `@SREBenjaminBot` Telegram bot under the same incident. Additionally, this track will resolve the Gemini API 404 HTTP Error by correcting invalid model name configurations across all agents, fix the idle state where Telegram messages did not receive a response, and update the dangerous safety gate confirmation buttons to utilize the explosion emoji (`💥 Yes, I am sure`) instead of the green tranquillity emoji.

## 2. Functional Requirements

### 2.1 Gemini API Model Name Correction
* Update default model and hardcoded strings from `"gemini-2.5-flash"` to a valid, live Gemini API model name `"gemini-1.5-flash"` in:
  - `src/agents/commander.py`
  - `src/server.py`
  - `src/agents/logistics_lead.py`
  - `src/agents/planning_lead.py`
  - `src/agents/ops_lead.py`
  - `src/agents/comms.py`
* Verify that these changes resolve the HTTP 404 Not Found error and restore full AI response capabilities to the Incident Commander.

### 2.2 Cross-Chat Mirroring
* **Web UI -> Telegram Push Notifications**:
  - In `src/server.py` POST handler for `/api/incidents/<id>/chat`, when a message is received from the Web Operator (`Operator (You)`), write it to the common `chat.json` file.
  - If a Telegram session is configured (`TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`), dispatch a push message containing the Operator's message directly to Telegram using `send_raw_telegram_message` (e.g. `💬 *[Web Operator]:* <message>`).
* **Telegram -> Web UI Real-Time Updates**:
  - In `start_telegram_bot` polling loop, when a standard chat message or STT-transcribed voice message is received from Telegram, ensure it is written to the incident's `chat.json`.
  - Because the SRE Web Dashboard periodically polls `/api/incidents/<id>/chat` every few seconds, updating the shared `chat.json` ensures full real-time cross-visibility of conversations.
* **Appropriate Senders**:
  - Mirrored messages from the Web UI should appear on Telegram under the sender marker `💬 *[Web Operator]:* <message>`.
  - Telegram messages should appear in the Web UI log under the sender name `"Operator (Telegram)"`.

### 2.3 Telegram Idle Fix
* Ensure that the standard chat message dispatcher in `start_telegram_bot` processes and forwards messages to the Incident Commander and replies back properly without hitting silent/idle timeouts.

### 2.4 Dangerous Action Emoji Upgrade
* Replace the button text `"✅ Yes, I am sure"` with `"💥 Yes, I am sure"` across all safety gate keyboard dispatches and input verification loops:
  - Inside `src/server.py` safety gate message interceptions and keyboard markups.
  - Inside `src/server.py` web REST API `/api/incidents/<id>/approve` and `/api/incidents/<id>/reject` handlers.
  - Inside automated test suites (`tests/test_telegram_safety_gate.py`).
  - Inside the user manual documentation `doc/USER_MANUAL.md`.

## 3. Out of Scope
* Creating new SRE agents or playbooks.
* Altering the visual design theme of the Web UI.
