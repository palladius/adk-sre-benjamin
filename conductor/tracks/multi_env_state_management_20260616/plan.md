# Implementation Plan: Make sense of state in multiple environments (local vs cloud)

## Phase 1: Environment-Specific Directory Routing
- [ ] Task: Implement dynamically-routed investigations directories
    - [ ] Create `get_investigations_dir()` in `src/incident.py` supporting `SRE_ENV`/`RAILS_ENV`
    - [ ] Update server logic to use resolved investigations directory instead of hardcoded `investigations`
- [ ] Task: Adapt test suite to environment routing
    - [ ] Update `tests/test_incident_archival.py` to use `get_investigations_dir()`
    - [ ] Verify test suite runs successfully in `test` environment
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Environment-Specific Directory Routing' (Protocol in workflow.md)

## Phase 2: Pluggable Abstractions for Active State & Discovery Storage
- [ ] Task: Design pluggable abstraction interface for Active State and Discovery Storage
    - [ ] Create interface/abstract classes or config toggles for StateManager and DiscoveryStorage
    - [ ] Implement local filesystem backend for StateManager and DiscoveryStorage
- [ ] Task: Write tests for pluggable state and discovery storage backends
    - [ ] Create `tests/test_state_abstractions.py` to test local filesystem backend
    - [ ] Confirm tests fail before implementation (Red Phase)
- [ ] Task: Implement abstraction changes in orchestrator and server
    - [ ] Refactor server and orchestrator to load active state and discovery via pluggable storage manager
    - [ ] Run test suite and confirm all tests pass (Green Phase)
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Pluggable Abstractions for Active State & Discovery Storage' (Protocol in workflow.md)
