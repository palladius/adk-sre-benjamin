# Specification: Project Explorer UI Improvements (Track: project_explorer_ui_improvements_20260603)

## 1. Overview
This specification addresses UI layout and interaction bugs in the Project Explorer workspace (Issue #2). It moves the navigation tabs to the top header inline with the title, establishes a toggleable Edit/Render mode for Project Wiki and Logical Graphs (defaulting to Render mode), and integrates interactive click-and-drag panning and scroll-wheel zooming for all Graphviz SVG visualizations.

---

## 2. Functional Requirements

### 2.1 Tab Navigation Realignment
- Move the `.project-tabs-nav` row into the `.project-header` at the top of the `#project-discovery-view`.
- Style the tabs as a premium, compact button row inline with the Back button and the compliance status badge.
- Ensure the header and tabs remain sticky at the top of the viewport when scrolling through long asset lists.

### 2.2 Toggleable Edit vs Rendering Modes
- **Project Wiki**:
  - By default, hide the editor pane (`.wiki-editor-pane`) and display ONLY the rendered markdown preview pane (`.wiki-preview-pane`).
  - Add an "✍️ Edit Wiki" button at the top-right of the Wiki panel.
  - Clicking "✍️ Edit Wiki" toggles the split-screen edit workspace (revealing both the textarea editor and the preview side-by-side) and changes the button text to "👁️ View Wiki".
- **Logical Graph**:
  - By default, hide the Graphviz DOT editor pane (`.graph-editor-pane`) and display ONLY the logical graph SVG container.
  - Add an "✍️ Edit Graph" button at the top-right of the Logical Graph panel.
  - Clicking "✍️ Edit Graph" toggles the split-screen workspace (revealing both the DOT textarea editor and the SVG graph side-by-side) and changes the button text to "👁️ View Graph".

### 2.3 Interactive Graphviz SVG Zoom & Pan
- Integrate mouse-wheel/pinch-zoom and click-and-drag pan functionality on all compiled Graphviz SVG diagrams (both Logical Dependency Topology and Physical VPC Network Topology).
- Boundaries: Ensure the SVG translation and scaling remain confined within the `.graph-preview-pane` borders (`overflow: hidden; position: relative;`).
- Cursor: Display a `grab` cursor over the SVG, switching to `grabbing` when actively panning.

---

## 3. Acceptance Criteria
- Tapping tabs switches views correctly. The tabs row is positioned inline with the title inside the top header.
- Opening "Project Wiki" or "Logical Graph" renders the content by default; the raw textareas are hidden. Clicking the Edit toggle button reveals the text editors.
- SVGs can be zoomed smoothly with the mouse scroll wheel and panned by clicking and dragging.
- All automated unit/integration tests continue to pass.
