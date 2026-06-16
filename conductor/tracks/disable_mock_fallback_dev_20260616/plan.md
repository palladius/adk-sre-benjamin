# Implementation Plan - Disable Mock Fallback in Development

## Phase 1: Environment and Configuration Update
- [ ] Task: Correct default Project ID in `.env`
    - [ ] Update `PROJECT_ID` in `.env` to `sre-next`
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Environment and Configuration Update' (Protocol in workflow.md)

## Phase 2: Implement Strict Live Discovery
- [ ] Task: Write Failing Tests for Strict Live Discovery (Red Phase)
    - [ ] Write a test in `tests/test_discovery.py` that verifies `discover_project_resources` raises `RuntimeError` when `MOCK_TOOLING=false` and no live resources can be fetched (due to gcloud failure, missing project, or lack of permission)
- [ ] Task: Implement Strict Live Discovery Behavior (Green Phase)
    - [ ] Modify `src/discovery.py` to check if `MOCK_TOOLING` is set to `"false"`. If so, raise an exception or fail if `resources` is empty, rather than silently falling back to `mock_resources`
    - [ ] Run the tests and verify that the newly written test passes while existing tests (such as mock-tooling = true) still pass
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Implement Strict Live Discovery' (Protocol in workflow.md)

## Phase 3: Frontend Error Reporting
- [ ] Task: Write Tests for Frontend Error Banner (Red Phase)
    - [ ] Add unit/integration tests in `tests/test_server.py` verifying that `/api/discover` returns a proper error response (HTTP 500) if discovery fails
- [ ] Task: Handle Server Error Response in Frontend (Green Phase)
    - [ ] Modify `src/server.py` to return an HTTP error code (e.g. 500) with details when `discover_project_resources` raises an error
    - [ ] Modify `src/static/index.js` to catch discovery errors and display a clear error banner/state in the UI (e.g., indicating connection/authentication failure)
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Frontend Error Reporting' (Protocol in workflow.md)
