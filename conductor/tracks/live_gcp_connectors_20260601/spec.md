# Specification: live_gcp_connectors_20260601

## Overview
This track integrates real Google Cloud Platform (GCP) connectors into Project Benjamin. It enables the SRE agents to execute authentic read-only diagnostics queries (Cloud Logging and Cloud Monitoring metrics) and safe whitelisted mutation recovery actions (Compute Engine SSH commands) on target GCP resources when `SRE_MODE=LIVE`.

## Requirements & Scope

1. **Read-Only Diagnostics (R/O):**
   - When `SRE_MODE=LIVE` is active, queries to logs and metrics must read directly from the target GCP project configured by `GCP_PROJECT_ID` using the authenticated local `gcloud` SDK context.
   - Parse live metric values (such as CPU utilization and system latency) and log entries.

2. **Read-Write Mutations (R/W):**
   - Mutation commands (e.g. service restarts) proposed by the Operations Lead and approved by Logistics must execute using secure `gcloud compute ssh` commands on target VM instances.
   - Ensure the operations remain strictly restricted to whitelisted commands.

3. **Interactive Logistics Override:**
   - Expose Human-in-the-loop (HITL) approval gates. If a proposed mutation is blocked due to HIGH risk, provide a manual approval override capability.

4. **Robust Mock Fallbacks:**
   - If `SRE_MODE=MOCK` is active (default), standard mock generators must supply simulated telemetry data instantly without invoking GCP commands.

## Acceptance Criteria
- Seamless env toggle between `SRE_MODE=LIVE` and `SRE_MODE=MOCK`.
- Unit tests verifying live vs mock command routing with 100% success rate.
