# Specification: sre_dashboard_20260601

## Overview
This specification defines the design, interfaces, and architecture for the **SRE Incident Command System Web Dashboard**. It provides site reliability engineers and coordinators with a high-fidelity, real-time visualization of the active Incident Command System (ICS), operational timelines, diagnostics, safety gate approval decisions, and communications updates.

## Requirements & Scope

1. **Zero-Dependency Python Web Server (`server.py`):**
   - Provide a lightweight server using Python's standard `http.server` library to maintain zero dependencies.
   - Serve frontend static assets from a static directory (e.g. `src/static/`).
   - Expose the following REST API endpoints returning clean JSON data:
     - `GET /api/incidents`: Lists all incident directories under `investigations/` along with their status and trigger type.
     - `GET /api/incidents/<incident_id>`: Returns the complete parsed incident state, timeline entries, registered artifacts, and audit logs.
     - `POST /api/simulate`: Invokes the `run_simulation()` flow to generate a brand new live SRE incident and returns the results.

2. **Premium Glassmorphism Frontend Dashboard:**
   - **Visual Identity:** Sleek Dark Mode using a curated color palette (deep slate `#0d1117`, midnight indigo `#161b22`, neon green `#39ff14` for healthy, neon red `#ff3131` for SLO breach, neon cyan `#00ffff` for safety approvals). Include a stylized header referencing Benjamin's Ferrari cap and Schloss castle base.
   - **Interactive Sidebar:** Select past or currently running SRE incidents.
   - **Real-Time Simulation Trigger:** Clicking "Trigger Live Simulation" initiates an API call that runs the simulation and renders the step-by-step progress using CSS animations.
   - **Dynamic SRE Timeline:** A vertical chronological path displaying formatted steps (Benjamin's declaration, Logistics audits, Ops metrics collection, Madhavi notifications).
   - **Rich Diagnostic Visualization:**
     - A custom SVG-based line chart displaying metrics (Latency and CPU utilization) with threshold guidelines.
     - An interactive MySQL query log terminal panel with query-highlighting.
   - **Logistics Safety Gate Card:** Highlights risk evaluation analysis (risk coefficients, blocked status, command decomposition).
   - **Communications Center:** Shows Slack/Telegram dispatch cards.

## Acceptance Criteria
- Running `python3 server.py` starts the server on port `8080` successfully.
- Triggering a simulation from the UI initiates a live run, saving files under `investigations/` and immediately rendering the complete timeline and assets.
- SVG metrics are generated dynamically and MySQL logs are readable inside the UI.
