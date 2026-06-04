# Specification: Edit wiki should visualize better (Track: better_wiki_edit_ui_20260604)

## 1. Overview
The current SRE dashboard displays 4 columns when editing the project wiki, making the layout extremely cramped and unusable on standard screen widths. This track optimizes the wiki editor's width by introducing a collapsible layout (collapsing sidebars) or a full-width overlay/modal layout when editing.

---

## 2. Functional Requirements
* **Responsive Layout Optimization**:
  - When editing the project wiki, temporarily collapse or hide the left incident panel and the right chat panel, allocating 100% of the screen width to the editor and live preview side-by-side.
  - Or, implement a full-screen overlays/dialogue editor that is clean and readable.
* **Layout Toggle State**: Maintain a toggle state that remembers if sidebars are collapsed, or automatically collapse them when editing begins and restore them when editing is saved or canceled.
* **Modern CSS Styling**: Apply clean layout transitions and glassmorphism styling to match the existing premium design.

---

## 3. Acceptance Criteria
* Clicking the "Edit Wiki" button hides the incident column and chat column to maximize editing workspace.
* Saving or canceling the wiki edits restores the column visibility.
* Side-by-side editing and rendering preview are clearly visible and legible.
