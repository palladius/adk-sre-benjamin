# Implementation Plan: Track cross_chat_mirroring_20260602

## Phase 1: Gemini API 404 Error Fix
- [ ] Task: Fix invalid Gemini model references and verify agent API queries.
    - [ ] Write failing unit test inside `tests/test_prompts.py` or `tests/test_agents.py` to assert that model defaults are properly set to a valid Gemini API model "gemini-1.5-flash".
    - [ ] Modify model default variables from "gemini-2.5-flash" to "gemini-1.5-flash" in `src/agents/commander.py`, `src/server.py`, `src/agents/logistics_lead.py`, `src/agents/planning_lead.py`, `src/agents/ops_lead.py`, and `src/agents/comms.py`.
    - [ ] Verify unit tests pass and ensure no 404 errors when making live Gemini API calls.
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Dangerous Action Emoji Upgrade
- [ ] Task: Upgrade SRE mutation approval buttons to use the explosion emoji.
    - [ ] Write failing unit test in `tests/test_telegram_safety_gate.py` to assert that safety validation buttons contain "💥 Yes, I am sure".
    - [ ] Modify `src/server.py` to display the "💥 Yes, I am sure" button in safety gate dispatches.
    - [ ] Update `src/server.py`'s Telegram bot polling loop message checks to detect and process the "💥 Yes, I am sure" string instead of "✅ Yes, I am sure".
    - [ ] Update `/api/incidents/<id>/approve` web route in `src/server.py` to log "Approved proposed mutation command via SRE Web Panel." to `chat.json` with appropriate danger descriptions.
    - [ ] Update the mock assertions inside `tests/test_telegram_safety_gate.py` to match the new "💥 Yes, I am sure" emoji.
    - [ ] Update the User Manual documentation `doc/USER_MANUAL.md` to reference the "💥 Yes, I am sure" validation buttons.
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Cross-Chat Mirroring and Telegram Idle Fix
- [ ] Task: Enable cross-visibility and real-time chat mirroring between Web and Telegram.
    - [ ] Write failing unit or integration tests verifying that messages posted to `/api/incidents/<id>/chat` trigger a push message to Telegram, and that Telegram messages are properly saved to the central `chat.json` log.
    - [ ] Modify the POST handler for `/api/incidents/<id>/chat` in `src/server.py` to call `send_raw_telegram_message` with `💬 *[Web Operator]:* <message>` when a message is received from the Web Operator UI.
    - [ ] Resolve Telegram chatbot idle/no-reply issues by ensuring that the standard chat polling loop forwards incoming messages to Benjamin IC and appends them to the common `chat.json` log.
    - [ ] Verify dynamic mirroring: verify that messages from Web UI instantly send push alerts to Telegram, and that Telegram messages automatically mirror onto the Web UI via `chat.json` polling.
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)
