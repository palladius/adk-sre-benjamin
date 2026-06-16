# Implementation Plan - P1 Add MCP to streamline agents abilities (Track: mcp_streamline_abilities_20260616)

## Phase 1: Service Account Setup & Provisioning
- [ ] Task: Audit and configure Safe SRE Service Account
  - [ ] Verify `bin/create_svc_acct.sh` configures `safe-sre-investigator` SA with read-only roles (Viewer, Logging Viewer, Monitoring Viewer) and no mutation capabilities.
- [ ] Task: Create Unsafe Mutator SRE Service Account script
  - [ ] Write `bin/create_mutator_svc_acct.sh` to create `unsafe-sre-mutator` SA with Editor / Mutation-capable roles.
  - [ ] Ensure key files are generated under `private/` and properly ignored by git.

## Phase 2: MCP Safe Executor Implementation
- [ ] Task: Implement MCP Safe Executor Server
  - [ ] Create `src/mcp_safe_executor.py` implementing an MCP server.
  - [ ] Define the tool `safe_call_gcloud(project_id, gcloud_tail)` that activates the safe SA key and runs the gcloud command.
- [ ] Task: Integrate MITM (Man-in-the-Middle) Vetting Layer
  - [ ] Implement validation logic that intercepts mutation requests.
  - [ ] Hook mutations into the Telegram/Discord Pending Mutation Queue (`pending_approvals.json`) for operator approval before execution via the unsafe SA.

## Phase 3: Verification
- [ ] Task: Write unit and integration tests
  - [ ] Write tests in `tests/test_mcp_safe_executor.py` verifying that `safe_call_gcloud` executes read commands and blocks write commands.
  - [ ] Verify MITM interception and queue insertion works as expected.
