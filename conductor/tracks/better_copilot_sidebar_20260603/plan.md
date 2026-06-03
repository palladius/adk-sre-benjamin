# Implementation Plan - Better Copilot Sidebar Panel

This plan maps out the tasks and verification checkpoints to rename, resize, and enrich the right-hand SRE Secondary Oncall sidebar panel.

---

## Phase 1: Sidebar Rename, Resizing, and Autofocus
- [ ] Task: Update Sidebar Layout & Resizing HTML/CSS markup
    - [ ] Modify `src/static/index.html` to rename the right-hand panel to `📟 SRE SECONDARY ONCALL` and add a new `#sidebar-resizer` vertical dragging handle bar
    - [ ] Modify `src/static/index.css` to define resizing layout flex bases, resizer cursor styles, and outline states
- [ ] Task: Implement Dragging Resizer, Autofocus, and Shortcut in `src/static/index.js`
    - [ ] Implement mouse/touch drag event listeners on `#sidebar-resizer` adjusting container width dynamically
    - [ ] Enforce boundary limits of `320px` to `800px` and persist width in `localStorage`
    - [ ] Bind autofocus triggers on dashboard init and on project/incident changes
    - [ ] Implement global `/` key keydown handler to autofocus the input box (ignoring when focused inside other textareas/inputs)
- [ ] Task: Implement Automated Verification Tests for Phase 1
    - [ ] Add unit tests verifying index.html contains correct element IDs and initial structures
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Sidebar Rename, Resizing, and Autofocus' (Protocol in workflow.md)

---

## Phase 2: Speech-to-Text Transcription API & Voice dictation UI
- [ ] Task: TDD - Write Backend Tests for Audio Transcription endpoint
    - [ ] Create test case asserting `POST /api/transcribe` processes audio payloads and returns transcription text JSON
- [ ] Task: Implement `POST /api/transcribe` REST route in `src/server.py`
    - [ ] Implement the HTTP post request handler reading request payload bytes
    - [ ] Call `transcribe_voice_bytes` and return JSON response: `{"transcription": "..."}`
    - [ ] Verify test suite passes (`uv run pytest`)
- [ ] Task: Implement Voice Dictation UI and Web Audio MediaRecorder in `src/static/index.js`
    - [ ] Modify `src/static/index.html` to add a microphone button next to the chat send button
    - [ ] Add glowing red pulse animation styles in `src/static/index.css`
    - [ ] Implement MediaRecorder API handler inside `src/static/index.js` recording voice notes from the user's microphone, sending the audio blob to `POST /api/transcribe` on stop, and appending the returned transcription directly to the text input
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Speech-to-Text Transcription API & Voice dictation UI' (Protocol in workflow.md)
