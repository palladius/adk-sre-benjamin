# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.6] - 2026-06-05
### Fixed
- **Collapsed Chat Widget Sizing**: Fixed CSS layout where `.chat-column.collapsed` was overridden by `min-width` and `min-height` settings, resolving the issue where it rendered as a large blank box.
- **Pulsing Golden Pill UI**: Redesigned the collapsed chat state into an animated golden pulsing pill widget with custom text shadows, glow effects, hover transitions, and a central label "⚡ SRE Co-Pilot (Click to Expand)".

## [1.2.5] - 2026-06-04
### Added
- **Maximize Chat Widget Sizing**: Added size toggle button (🗖 / 🗗) to expand the chat panel height to 90vh and width to 480px.
- **Maximized State Persistence**: Persists maximized state dynamically across user sessions in localStorage.
- **Collapsible Post-it Preview**: Redesigned collapsed chat widget as a golden bordered post-it preview box displaying the latest message snippet.
- **Vulnerability Diagnostics & Audit Tracking**: Checkpoint resolution states and diagnostic logs automatically recorded for incident `INC-20260604-e0dc`.
- **Bolding Version Tag**: Configured JavaScript to dynamically bold the application version tag in the footer.

## [1.2.4] - 2026-06-04
### Added
- **Floating Collapse-ready Widget**: Transformed the SRE chat panel from a static column layout to a floating glassmorphic collapsible chat widget.
- **Compact Footer Layout**: Consolidated the footer to a single line display version and source repository link.
- **Adaptive Screen Grids**: Dynamically adjustments of the main dashboard grid-template-columns to span full available width when the chat is minimized.

## [1.2.3] - 2026-06-02
### Changed
- **Project Folder Grouping**: Transitioned the flat cache file storage inside `discover/gcp-project/` to clean project-specific subdirectories (`discover/gcp-project/<project_id>/`), structuring resource discoveries in `discover.json`, Markdown indices in `wiki.md`, and dependency diagrams in `graph.dot`.
- **API & UI Telemetry Updates**: Updated GET/POST discover, wiki, and graph server handlers, test assertions, and UI labels to search and print the new directory-grouped paths.
- **Automatic Migration**: Executed a safe file migration script moving all existing SRE wikis, resources, and DOT graphs cleanly to their corresponding project subdirectories with zero data loss.

## [1.2.2] - 2026-06-02
### Added
- **Markdown Wiki Editor & Live Preview**: Wired up the `.project-tab-btn` buttons to display the split markdown editor/preview layout, dynamically loading existing project wiki notes via `GET /api/projects/<id>/wiki`, compiled in real-time in the browser, and persisted via `POST /api/projects/<id>/wiki`.
- **SPA Routing Router & History sync**: Integrated client-side `navigateTo(url)` and `handleRouting()` popstate router, capturing `/clouds` and `/projects/<id>` deep-links cleanly with zero page reloads.
- **Dynamic Physical Network Topology Graphs**: Programmed dynamic physical VPC attachment map auto-generation client-side, representing VMs, private databases, GCS buckets, GKE controls, and subnets inside beautifully styled Graphviz cluster subgraphs compiled to SVGs asynchronously via Viz.js.
- **Custom Logical Graphs Integration**: Wired Graphviz dependency graphs editing and compiling asynchronously using Viz.js CDN rendering, with dynamic saving back to `discover/gcp-project/<id>.dot`.

## [1.2.1] - 2026-06-02
### Fixed
- **Live Discovery Impersonation Override**: Added logic to automatically override/bypass active Google Cloud service account impersonation settings when performing a live resource discovery scan on non-default GCP projects (such as `sre-next-prod`), allowing authentications to naturally fall back to the active authorized gcloud credentials configuration. This eliminates the fake/mock fallback notice caused by default service account access boundaries.

## [1.2.0] - 2026-06-02
### Added
- **Interactive Safety Gate Buttons**: Implemented SRE approval validation buttons (`✅ Yes, I am sure` and `❌ No, abort mutation`) presented directly to the operator in Telegram during a safety gate hold.
- **Two-Way Web & Telegram Sync**: Connected REST endpoints `/approve` and `/reject` to dynamically reset Telegram keyboards back to standard when choices are confirmed from either interface.
- **Operator Chat Logging**: Automatically recorded safety gate confirmation responses and Benjamin IC status alerts directly within the incident's `chat.json` log for live synchronization.
- **Resource Usage Capping**: Integrated systemd scopes and cgroup memory limits inside the SRE CLI and test runners (`justfile`) to enforce resource caps on host systems.
- **Safety Gate Test Suite**: Authored `tests/test_telegram_safety_gate.py` to verify dispatches of keyboard markup payloads.

## [1.1.0] - 2026-06-01
### Added
- **Dynamic GCP Project ID Input**: Introduced a glassmorphic Project ID input in the SRE dashboard sidebar allowing custom override values.
- **Project ID Trigger Payload**: Configured `/api/simulate` payload submission to use the custom Project ID specified in the UI.
- **GCP Project ID Fallback**: Added fallback checking inside the `parse_trigger` parsing utility to load project ID from `.env` (using `GCP_PROJECT_ID` or `PROJECT_ID`) when blank/absent.
- **Human-In-The-Loop (HITL) Safety Clearance**: Developed approval/rejection button panel controls directly linked to REST APIs `/api/incidents/<id>/approve` and `/api/incidents/<id>/reject`.
- **Safety Gate States Rendering**: Styled risk assessment highlights in neon colors based on state ("AWAITING CLEARANCE", "REJECTED", "EXECUTED").
- **Interactive Contextual Chat Agent**: Designed and styled an interactive SRE Co-Pilot chat panel in Outfit/Mono font colors.
- **Tactical SRE Commander Agent Backend**: Exposed GET/POST REST APIs `/api/incidents/<id>/chat` to load/save chat history logs and simulate an SRE Incident Commander Agent that responds contextually to operator queries.
- **Service Account Setup script (`bin/create_svc_acct.sh`)**: Engineered an SRE service account creation and configuration bash script that binds least-privilege R/O viewer/logging roles and exports keys directly to `private/`.
- **Extended Test Suite**: Added a fallback environment variable unit test under `tests/test_trigger.py` and integration tests for the SRE chat endpoints inside `tests/test_server.py`.
