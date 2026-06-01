# Plan: live_gcp_connectors_20260601

## Phase 1: Real-Time SRE Diagnostics (R/O)
- [ ] Task: Integrate live GCP Cloud Logging subprocess query routing in `src/diagnostics.py`
- [ ] Task: Integrate live GCP Cloud Monitoring metric timeseries retrieval in `src/diagnostics.py`
- [ ] Task: Write unit tests verifying dynamic `SRE_MODE=LIVE` environment switching for diagnostics
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Whitelisted Mutations via Compute SSH (R/W)
- [ ] Task: Configure the SRE Mutation Agent to execute whitelisted Compute commands via `gcloud compute ssh`
- [ ] Task: Implement human-in-the-loop manual override buttons on the visual dashboard panel
- [ ] Task: Write security validation tests ensuring commands are limited strictly to whitelisted VM operations
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: End-to-End Live Simulation & Integration
- [ ] Task: Coordinate complete end-to-end incident flow simulation under `SRE_MODE=LIVE`
- [ ] Task: Verify that results and metric trend charts render perfectly on the SRE dashboard
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)
