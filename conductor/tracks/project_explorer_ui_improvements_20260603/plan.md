# Implementation Plan - Project Explorer UI Improvements (Track: project_explorer_ui_improvements_20260603)

This plan details the tasks to realign navigation tabs inline inside the project explorer header, hide editing textareas by default for Wiki and Logical Graphs with toggle buttons, and implement custom zoom and pan interactions on Graphviz SVGs.

---

## Phase 1: HTML/CSS Realignment
- [x] Task: Update Project Explorer Header Layout
  - [x] Modify `src/static/index.html` to place the `.project-tabs-nav` row inside `header.project-header` alongside the back button and compliance badge.
  - [x] Modify `src/static/index.css` to align the tabs inline, make `.project-header` sticky, and fix padding/margins.
- [x] Task: Set default hidden styles for editing textareas
  - [x] Add `.wiki-editor-layout:not(.edit-mode) .wiki-editor-pane` rule to hide the editor textarea.
  - [x] Add `.graph-layout:not(.edit-mode) .graph-editor-pane` rule to hide the DOT graph editor.
  - [x] Set `.graph-preview-pane` to `overflow: hidden; position: relative;` for pan-zoom clipping.
- [x] Task: Conductor - User Manual Verification 'Phase 1: HTML/CSS Realignment' (Protocol in workflow.md)

---

## Phase 2: JavaScript Functionality & Event Bindings
- [x] Task: Implement Edit/View toggling logic in `src/static/index.js`
  - [x] Add event listeners to the new "✍️ Edit Wiki" button to toggle the `.edit-mode` class on `.wiki-editor-layout` and update button text to "👁️ View Wiki".
  - [x] Add event listeners to the new "✍️ Edit Graph" button to toggle the `.edit-mode` class on `.graph-layout` and update button text to "👁️ View Graph".
- [x] Task: Develop SVG Zoom & Pan helper
  - [x] Write the `makeSvgInteractive(svg)` function in `src/static/index.js` capturing mousedown, mousemove, mouseup, and wheel events.
  - [x] Call `makeSvgInteractive` after rendering SVGs inside `renderLogicalGraph` and `renderNetworkGraph`.
- [x] Task: Conductor - User Manual Verification 'Phase 2: JavaScript Functionality & Event Bindings' (Protocol in workflow.md)

---

## Phase 3: Verification & Automated Tests
- [x] Task: TDD - Add frontend integration assertions
  - [x] Update `tests/test_server.py` to check that new edit buttons (`btn-edit-wiki`, `btn-edit-graph`) exist in the HTML structure.
  - [x] Verify that all existing unit and integration tests pass successfully (`uv run pytest`).
- [x] Task: Conductor - User Manual Verification 'Phase 3: Verification & Automated Tests' (Protocol in workflow.md)
