# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.14] - 2026-06-16
### Added
- **OpenTelemetry SRE Agent Instrumentation**: Added dynamic monkeypatching wrapper in `src/observability.py` to instrument agent `run()` method executions with OpenTelemetry spans tracking `agent.class`, `agent.name`, `agent.prompt`, and response status.
- **Observability Testing**: Added unit test `test_agent_otel_instrumentation` verifying that execution spans and attributes are correctly collected using an InMemorySpanExporter.

## [1.2.13] - 2026-06-16
### Added
- **Production-Ready Dockerfile & .dockerignore**: Dockerized the web server using `python:3.12-slim` base image, added a non-root `appuser`, configured necessary env vars, and updated `.dockerignore` to exclude development directories like `conductor/` and `terraform/`.
- **Cloud Run Deployment**: Configured deploy script and added deploy/docker-build targets to `justfile` using `gcloud run deploy`.
- **Pluggable Abstractions for Active State & Discovery Storage**: Implemented `BaseStateManager` and `BaseDiscoveryStorage` abstract base classes in `src/storage.py` alongside local filesystem backends `FileStateManager` and `FileDiscoveryStorage` to support dynamically toggleable local/cloud state tracking.

### Fixed
- **State Abstraction Test Environment Dependency**: Updated `test_file_state_manager` in `tests/test_state_abstractions.py` to use `monkeypatch` to delete `PROJECT_ID` and `GCP_PROJECT_ID` environment variable overrides, ensuring predictable default project resolution during pytest runs.

## [1.2.12] - 2026-06-16
### Added
- **Telegram Bot /pending Command & Callbacks (Phase 2)**: Added Telegram bot listener for `/pending` command to show pending mutation queue formatted with risk indicator emojis (🟢, 🟡, 🟠, 🔴). Added inline keyboards with Approve and Reject callback buttons. Implemented callback listeners with reply-to-comment prompts to capture operator comment inputs for approvals and rejections.
- **Web UI Mutation Queue Widget (Phase 3)**: Added a "Pending SRE Mutation Actions Queue" dashboard panel. Styled list items with glassmorphic cards showing details in Outfit font. Added non-mandatory comment input and Approve (💥) / Reject buttons.
- **Dynamic Bot Navigation Key**: Updated `send_telegram_menu` to dynamically show the `📥 Pending Approvals` reply button when the active incident is in a non-closed status.
- **Telegram Co-pilot Comments Context**: Injected operator comments context into direct Telegram SRE agent chat dispatch.

## [1.2.11] - 2026-06-16
### Added
- **Multi-Environment State Separation (Rails-style)**: Divided active incident investigations into environment-specific folders (`investigations/prod`, `investigations/dev`, `investigations/test`) matching `RAILS_ENV` / `SRE_ENV`.
- **Pytest Auto-detection & Path Mocking**: Configured `get_investigations_dir()` to auto-detect pytest environments and isolate test operations under `investigations/test`, resolving dotenv overrides while allowing explicit test overrides.

## [1.2.10] - 2026-06-16
### Added
- **Whitelisted Mutations via Compute SSH**: Configured SRE Mutation Agent to execute whitelisted Compute commands via `gcloud compute ssh` under `SRE_MODE=LIVE`, using secure subprocess execution.
- **Human-in-the-Loop Override Panel**: Implemented manual override force-approval button on the visual dashboard panel to override safety gates for high-risk commands.
- **Security Validation Tests**: Added pytest test suite validating whitelisted VM commands and MutationAgent execution logic.
- **Pending Mutations Queue (Phase 1)**: Added shared JSON persistence for pending mutations queue inside `<incident_folder>/pending_approvals.json` and compiled Markdown tables inside `state.md`. Exposed GET/POST `/api/incidents/<id>/pending` and approve/reject POST endpoints. Integrated operator comment piggybacking to the LLM agent prompt.

### Changed
- **Remove test-project-123 & Disable Mocking**: Removed all occurrences and environment configuration traces of `test-project-123` across dev, prod, and mocking, replaced them with `sre-next` and `sre-next-dev` respectively. Set default configurations for `MOCK_TOOLING` and `SRE_MODE` to `false` and `LIVE` respectively to disable mocking.

## [1.2.9] - 2026-06-16
### Added
- **Incident Archival & Deletion**: Added a status metadata attribute `Archived` to SRE incident states. Active incidents are filtered out by default in UI/API list views. Added Archive and Delete action buttons to incident list item panels. Added Telegram bot `/archive` command. Added background scheduler to auto-archive CLOSED incidents older than 3 days.

### Changed
- **Web Port Configuration**: Configured the `just web` and `restart-services` commands to run on port `10042` instead of port `8080`.

## [1.2.8] - 2026-06-16
### Added
- **Telegram Send CLI Shortcut**: Added `bin/telegram-send` command line tool to easily dispatch Telegram messages and Hello World notifications with custom formatting.

## [1.2.7] - 2026-06-08
### Added
- **GCS Discovery Cache Sync**: Automatic background bidirectional directory sync between local discovery cache and GCS using `gsutil rsync`. Pulse sync dot status indicators displayed on coordinates bar.
- **Wiki Cross-Linking & Tab State Preservation**: Support for `/projects/` prefix inside double brackets (e.g. `[[/projects/sre-next]]`) and programmatic tab preservation when switching project context.

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
