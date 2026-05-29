# Specification: mock_diagnostics_20260529

## Overview
This specification defines the design and interfaces for a **Mock Diagnostics Subsystem** and an **E2E Incident Simulation Harness**. It allows Project Benjamin to execute lightning-fast, reproducible, and zero-dependency end-to-end incident troubleshooting runs for development, testing, and continuous evaluations (EVALs).

## Requirements & Scope

1. **Environment Config Gates (.env):**
   - Read `SRE_MODE` from the environment.
   - If `SRE_MODE=MOCK` (default), all diagnostic queries return simulated mock strings/data instantly.
   - If `SRE_MODE=LIVE`, queries route to real external providers/APIs.

2. **Mock SRE Diagnostics (`src/diagnostics.py`):**
   - `query_logs(project_id: str, filter_str: str) -> str`: Returns structured mock log dumps (e.g. suspension, memory spikes, or DB timeouts).
   - `query_metrics(project_id: str, metric_name: str) -> list[float]`: Returns mock time-series CPU/memory/latency data lists.

3. **E2E Simulation Runner (`run_simulation.py`):**
   - Executes a full end-to-end latency SLO incident in less than 2 seconds:
     1. Ingest SLO latency violation alert trigger.
     2. Scaffold investigations folder (`investigations/INC-SIM-XXXX/`).
     3. Madhavi broadcasts incident startup.
     4. Ops queries CPU & latency metrics (Metrics Agent). Scribe registers CSV artifact lineage.
     5. Ops queries MySQL query logs (Logs Agent). Scribe registers log artifact lineage.
     6. Ops identifies log-disk saturation and proposes a whitelisted recovery command (e.g., `systemctl restart mysql`).
     7. Logistics Risk Assessor evaluates risk.
     8. Madhavi notifies safety clearance, Mutation Agent executes mutation, diagnostic checks confirm metric recovery, and incident is closed.

## Acceptance Criteria
- Executing `python3 run_simulation.py` runs a complete E2E lifecycle successfully.
- All timeline entries are written, git note attachments are compiled, and CSV logs are cached with accurate CLI/MCP lineage.
