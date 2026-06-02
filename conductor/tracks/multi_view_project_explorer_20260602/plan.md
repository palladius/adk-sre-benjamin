# Implementation Plan: Multi-View Project Explorer (multi_view_project_explorer_20260602)

---

## Phase 1: Backend Route-Rewriting and Asset Discovery API Upgrades

### Task 1: Route Rewriting and API Verification (TDD)
- [ ] **Task: Write failing route rewriting tests**
  - [ ] Add unit tests in `tests/test_server.py` verifying that GET requests to `/projects/<project_id>`, `/projects/<project_id>/wiki`, and `/clouds` correctly respond with 200 OK and return the standard `index.html` content (allowing deep-linking fallback).
- [ ] **Task: Implement route rewrites in server**
  - [ ] Modify the `do_GET` handler in `src/server.py` to rewrite any path prefixing `/projects/` or `/clouds` (that are not API or static assets) to serve `src/static/index.html`.
  - [ ] Run the tests and confirm they pass (Green Phase).

### Task 2: Wiki and Graph Topology Storage API
- [ ] **Task: Write failing storage API tests**
  - [ ] Add unit tests in `tests/test_server.py` verifying `GET/POST /api/projects/<project_id>/wiki` and `GET/POST /api/projects/<project_id>/graph` endpoints.
- [ ] **Task: Implement custom wiki and graph endpoints**
  - [ ] Implement `GET/POST` REST routes in `src/server.py` to read/write `<project_id>.md` and `<project_id>.dot` files inside the `discover/gcp-project/` cache directory.
  - [ ] Verify unit tests pass (Green Phase).

### Task 3: Filtering 'Boring' GKE/Dataproc Node Resources
- [ ] **Task: Write VM resource exclusion tests**
  - [ ] Add a unit test in `tests/test_discovery.py` validating that VM instances with `gke-` prefix or Dataproc workers are excluded from discovery/wiki templates.
- [ ] **Task: Implement filter logic in discovery crawler**
  - [ ] Modify `src/discovery.py` to identify and ignore GKE system node pool instances (e.g. name starting with `gke-` and belonging to standard GKE pools) and Dataproc instances.
  - [ ] Confirm all tests are passing.

- [ ] **Task: Conductor - User Manual Verification 'Phase 1: Backend' (Protocol in workflow.md)**

---

## Phase 2: Cloud Directory Landing Page and Routing Integration

### Task 4: Client-side URL Routing Engine
- [ ] **Task: Implement History API Client Router**
  - [ ] Create a client-side navigation handler in `src/static/index.js` using `history.pushState` and intercepting link clicks.
  - [ ] Implement a `popstate` window event listener to render views correctly when the user clicks browser Back/Forward buttons.

### Task 5: Clouds Directory landing view
- [ ] **Task: Develop Clouds Main Page UI**
  - [ ] Construct a glassmorphic dashboard in `src/static/index.html` and `src/static/index.js` displaying card panels for Google Cloud, AWS, Azure, and Vercel.
  - [ ] Generate dynamic lists of discoverable projects dynamically loaded from cache.
  - [ ] Make each project fully clickable, routing seamlessly to `/projects/<project_id>` with updated address URLs.

- [ ] **Task: Conductor - User Manual Verification 'Phase 2: Clouds Directory' (Protocol in workflow.md)**

---

## Phase 3: Interactive Wiki and Graphviz DOT Views

### Task 6: Editable Project Wiki Markdown UI
- [ ] **Task: Implement Wiki Markdown Tab View**
  - [ ] Add a "Wiki Notes" tab to the project explorer panel in `src/static/index.js`.
  - [ ] Load wiki markdown from `/api/projects/<project_id>/wiki`.
  - [ ] Integrate a responsive text editor pane with a "Save Wiki" button to persist modifications to the backend cache directory.

### Task 7: Graphviz DOT Render Engine and Network Graph Views
- [ ] **Task: Integrate browser Viz.js compiler**
  - [ ] Embed the standard Viz.js CDN library in `src/static/index.html` for interactive on-the-fly compiling of DOT notation into browser SVGs.
- [ ] **Task: Build Logical Dependency and VPC Network Views**
  - [ ] Design a "Logical Topology" view providing editing and drawing of dependency links, with interactive SVG node clicks.
  - [ ] Design a "VPC Network attachment" view dynamically mapping discovered VMs and SQL instances inside their parent VPC networks as styled DOT subgraph clusters.
  - [ ] Add storage syncing to persist operator-modified `.dot` network topologies.

- [ ] **Task: Conductor - User Manual Verification 'Phase 3: Interactive Views' (Protocol in workflow.md)**
