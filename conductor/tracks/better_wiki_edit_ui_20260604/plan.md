# Implementation Plan - Edit wiki should visualize better (Track: better_wiki_edit_ui_20260604)

## Phase 1: Adapt HTML/CSS Structure
- [x] Task: Adjust layout CSS (5765374)
  - [x] Add `.wiki-edit-active` class to container to collapse side columns (incident, chat) dynamically.
  - [x] Style the wiki edit pane and preview pane to span full width when editing is active.

## Phase 2: Add Javascript Event Handling
- [x] Task: Integrate layout transitions in JS (5765374)
  - [x] Update JS to add `.wiki-edit-active` class to the layout wrapper when entering edit mode.
  - [x] Ensure class is removed when exiting (saving/canceling) edit mode.

## Phase 3: Verification
- [x] Task: Manual Layout Check (5765374)
  - [x] Enter wiki edit mode on a test project and confirm that side columns hide cleanly and the editor/preview spans full width.
  - [x] Exit edit mode and confirm the side columns are correctly restored.
