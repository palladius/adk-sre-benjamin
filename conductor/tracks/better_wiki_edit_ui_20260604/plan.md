# Implementation Plan - Edit wiki should visualize better (Track: better_wiki_edit_ui_20260604)

## Phase 1: Adapt HTML/CSS Structure
- [ ] Task: Adjust layout CSS
  - [ ] Add `.wiki-edit-active` class to container to collapse side columns (incident, chat) dynamically.
  - [ ] Style the wiki edit pane and preview pane to span full width when editing is active.

## Phase 2: Add Javascript Event Handling
- [ ] Task: Integrate layout transitions in JS
  - [ ] Update JS to add `.wiki-edit-active` class to the layout wrapper when entering edit mode.
  - [ ] Ensure class is removed when exiting (saving/canceling) edit mode.

## Phase 3: Verification
- [ ] Task: Manual Layout Check
  - [ ] Enter wiki edit mode on a test project and confirm that side columns hide cleanly and the editor/preview spans full width.
  - [ ] Exit edit mode and confirm the side columns are correctly restored.
