# Specification: Better Copilot Sidebar Panel (Track: better_copilot_sidebar_20260603)

## 1. Overview
This feature refactors the right-hand panel of the SRE Web Dashboard. It renames the sidebar from "Copilot" to "SRE Secondary Oncall" (with modern, glowing, walkie-talkie themed icon), adds left-right resizability via a smooth draggable handler, implements voice-to-text dictation directly into the chat input box, and incorporates automated input field autofocusing and keyboard shortcuts.

---

## 2. Functional & Visual Requirements

### 2.1 Sidebar Renaming & Branding
- Rename the sidebar container title to **`📟 SRE SECONDARY ONCALL`** in `src/static/index.html`.
- Incorporate a modern, walkie-talkie styled glowing icon next to the title.

### 2.2 Smooth Left-Right Panel Resizing
- **Draggable Handle**: Add a vertical resizing handle bar (`#sidebar-resizer`) on the left border of the sidebar panel.
- **Drag Interaction**: Users can click and drag the resizer to adjust the sidebar's width dynamically.
- **Boundaries**: Enforce a minimum width of `320px` and a maximum width of `800px` to maintain dashboard layout integrity.
- Store the user's preferred sidebar width in `localStorage` so it persists across reloads.

### 2.3 Input Autofocus & Keyboard Shortcut
- **Context Autofocus**: Automatically autofocus the sidebar chat text input field when:
  - The dashboard is loaded.
  - The active incident context or active project switches.
- **Focus Shortcut**: Pressing the `/` key anywhere on the dashboard (unless typing inside another input element) instantly focuses the sidebar chat input field and prevents default browser behaviors.

### 2.4 Voice Dictation (Microphone Button)
- **UI Element**: Add a microphone button (`🎙️`) inside the sidebar chat input actions area.
- **Interaction**:
  - Tapping the microphone button initiates voice recording (toggles active recording state).
  - Tapping again stops the recording and sends the audio file to `/api/transcribe` (reusing the server's speech-to-text transcription engine).
  - The transcribed text is appended directly to the chat input text field, allowing the operator to review and edit it before sending.
- **Micro-Animations**: Display a red glowing pulse animation around the microphone button while recording is active.

---

## 3. Acceptance Criteria
- Clicking and dragging the resizer smoothly adjusts the sidebar panel width. Width is saved and restored on reload.
- Changing incidents or reloads triggers input autofocus. Pressing `/` focuses the chat input.
- Tapping the microphone button toggles recording with a pulsing animation. The transcribed text is successfully populated into the input field.
- The sidebar panel title is renamed to "SRE SECONDARY ONCALL".
