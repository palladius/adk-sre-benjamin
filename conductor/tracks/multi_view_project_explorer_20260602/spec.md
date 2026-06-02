# Specification: Multi-View Project Explorer (multi_view_project_explorer_20260602)

## 1. Overview
Revive project asset discovery and introduce an interactive, multi-view SRE project explorer dashboard. This feature adds a cloud-directory landing page, multiple interactive views per project (Wiki Markdown, VPC Network Topology Graph, and Logic dependency Graph), and modern Rails-like URL routing structure using HTML5 History API.

---

## 2. Functional Requirements

### 2.1 Backend-like Clean Routing
- **Routing Structure**: Transition UI navigation from hashed paths to beautiful, shareable URLs:
  - `/` or `/clouds`: The Clouds Directory main page.
  - `/projects/<project_id>`: The Project Home Dashboard page.
  - `/projects/<project_id>/wiki`: The editable Markdown wiki page.
  - `/projects/<project_id>/graph`: Interactive resource dependency/logical topology graph.
  - `/projects/<project_id>/network`: VPC network topology graph mapping resource attachments.
- **Python Route Rewriting**: Update `src/server.py` to intercept deep-linked paths (e.g., `/projects/*`, `/clouds`) and rewrite/serve the main `index.html` file, letting the client-side router render the correct view.

### 2.2 Clouds Directory (Main Page)
- **Multi-Cloud Dashboard**: Renders a landing dashboard representing cloud systems: Google Cloud, AWS, Azure, and Vercel.
- **Project Indexing**: Clicking on a cloud system displays a dynamic clickable list of associated project IDs (loaded from discovery history).
- **Navigation**: Selecting a project routes the browser smoothly to `/projects/<project_id>`.

### 2.3 Interactive Project Views
- **1. Ugly but Functional Tab (Current View)**: Retain the existing raw asset audit list view as a dedicated dashboard tab.
- **2. Editable Project Wiki (Markdown)**:
  - Serves an editable, self-persisted markdown wiki page for each project.
  - **Auto-Sweep Bootstrapping**: If no wiki exists, automatically bootstrap a template from discovery:
    - `## ☸️ GKE Clusters` listing active clusters and GKE services.
    - `## 🖥️ Compute VM Instances` listing VMs.
  - **Boring VM Filtering**: Filter out and hide GKE node pools/helper VMs (e.g., `gke-*` prefix) and Dataproc worker/master nodes by default from the listing, keeping focus on core workload VMs.
  - **Notes Persistence**: Allow custom inline markdown edits to persist directly in the backend at `discover/gcp-project/<project_id>.md`.
- **3. Graph & VPC Network Views (Graphviz DOT)**:
  - **Logical Graph**: Render an interactive logical topology map showing dependencies and documented breakages between services and VMs.
  - **Network Graph**: Render a physical VPC topology mapping how resources (VMs, SQL instances) attach to distinct VPC networks.
  - **Graphviz DOT Rendering**: Integrate Viz.js from CDN to dynamically compile Graphviz DOT syntax into clean, interactive SVGs in the frontend. Preservation of textual links within nodes/labels is fully enabled.
  - **Topology Customization**: Provide an editable DOT text panel to allow operators to document custom links, connections, or simulated network breakages, saved in the backend directory.

---

## 3. Non-Functional Requirements
- **No Extra Dependencies**: Standard library Python, standard JS, and standard CSS (Zero-dependency rule). External libraries (Viz.js / Graphviz) loaded strictly from reliable CDNs.
- **Storage**: Persist customized wiki Markdown and DOT files inside `discover/gcp-project/`.
- **TDD Compliant**: All backend routing logic and file persistence integrations must have corresponding unit tests.

---

## 4. Acceptance Criteria
1. Navigating to `http://localhost:8080/projects/sre-next-prod` directly serves the SRE dashboard and initializes the `sre-next-prod` project view.
2. Clicking sidebar tabs updates the URL path dynamically (using `history.pushState`) without reloading the entire window.
3. Live GKE node pools (`gke-*`) and Dataproc master/worker nodes are automatically hidden from the default Wiki discovery list.
4. Interactive DOT network diagrams compile cleanly from string templates and display resource nodes correctly linked to their VPC parent boxes.
