# Implementation Plan: Multi-View Project Explorer (multi_view_project_explorer_20260602)

---

## Phase 1: Backend Route-Rewriting and Asset Discovery API Upgrades

### Task 1: Route Rewriting and API Verification (TDD)
- [x] **Task: Write failing route rewriting tests** (bc7073f)
  - [x] Add unit tests in `tests/test_server.py` verifying that GET requests to `/projects/<project_id>`, `/projects/<project_id>/wiki`, and `/clouds` correctly respond with 200 OK and return the standard `index.html` content (allowing deep-linking fallback).
- [x] **Task: Implement route rewrites in server** (bc7073f)
  - [x] Modify the `do_GET` handler in `src/server.py` to rewrite any path prefixing `/projects/` or `/clouds` (that are not API or static assets) to serve `src/static/index.html`.
  - [x] Run the tests and confirm they pass (Green Phase).

### Task 2: Wiki and Graph Topology Storage API
- [x] **Task: Write failing storage API tests** (bc7073f)
  - [x] Add unit tests in `tests/test_server.py` verifying `GET/POST /api/projects/<project_id>/wiki` and `GET/POST /api/projects/<project_id>/graph` endpoints.
- [x] **Task: Implement custom wiki and graph endpoints** (bc7073f)
  - [x] Implement `GET/POST` REST routes in `src/server.py` to read/write `<project_id>.md` and `<project_id>.dot` files inside the `discover/gcp-project/` cache directory.
  - [x] Verify unit tests pass (Green Phase).

### Task 3: Filtering 'Boring' GKE/Dataproc Node Resources
- [x] **Task: Write VM resource exclusion tests** (bc7073f)
  - [x] Add a unit test in `tests/test_discovery.py` validating that VM instances with `gke-` prefix or Dataproc workers are excluded from discovery/wiki templates.
- [x] **Task: Implement filter logic in discovery crawler** (bc7073f)
  - [x] Modify `src/discovery.py` to identify and ignore GKE system node pool instances (e.g. name starting with `gke-` and belonging to standard GKE pools) and Dataproc instances.
  - [x] Confirm all tests are passing.

- [x] **Task: Conductor - User Manual Verification 'Phase 1: Backend' (Protocol in workflow.md)** (bc7073f)

---

## Phase 2: Cloud Directory Landing Page and Routing Integration

### Task 4: Client-side URL Routing Engine
- [x] **Task: Implement History API Client Router** (5f6300c)
  - [x] Create a client-side navigation handler in `src/static/index.js` using `history.pushState` and intercepting link clicks.
  - [x] Implement a `popstate` window event listener to render views correctly when the user clicks browser Back/Forward buttons.

### Task 5: Clouds Directory landing view
- [x] **Task: Develop Clouds Main Page UI** (5f6300c)
  - [x] Construct a glassmorphic dashboard in `src/static/index.html` and `src/static/index.js` displaying card panels for Google Cloud, AWS, Azure, and Vercel.
  - [x] Generate dynamic lists of discoverable projects dynamically loaded from cache.
  - [x] Make each project fully clickable, routing seamlessly to `/projects/<project_id>` with updated address URLs.

- [x] **Task: Conductor - User Manual Verification 'Phase 2: Clouds Directory' (Protocol in workflow.md)** (5f6300c)

---

## Phase 3: Interactive Wiki and Graphviz DOT Views

### Task 6: Editable Project Wiki Markdown UI
- [x] **Task: Implement Wiki Markdown Tab View** (5f6300c)
  - [x] Add a "Wiki Notes" tab to the project explorer panel in `src/static/index.js`.
  - [x] Load wiki markdown from `/api/projects/<project_id>/wiki`.
  - [x] Integrate a responsive text editor pane with a "Save Wiki" button to persist modifications to the backend cache directory.

### Task 7: Graphviz DOT Render Engine and Network Graph Views
- [x] **Task: Integrate browser Viz.js compiler** (5f6300c)
  - [x] Embed the standard Viz.js CDN library in `src/static/index.html` for interactive on-the-fly compiling of DOT notation into browser SVGs.
- [x] **Task: Build Logical Dependency and VPC Network Views** (5f6300c)
  - [x] Design a "Logical Topology" view providing editing and drawing of dependency links, with interactive SVG node clicks.
  - [x] Design a "VPC Network attachment" view dynamically mapping discovered VMs and SQL instances inside their parent VPC networks as styled DOT subgraph clusters.
  - [x] Add storage syncing to persist operator-modified `.dot` network topologies.

- [x] **Task: Conductor - User Manual Verification 'Phase 3: Interactive Views' (Protocol in workflow.md)** (5f6300c)
