# Plan: GCP Resource Discovery and Asset Audit

## Phase 1: Discovery Core Engine
- [ ] Task: Implement core resource crawling logic
    - [ ] Create `src/discovery.py` module
    - [ ] Write GCE VM, Cloud Run, GKE, and Cloud SQL resource crawlers
    - [ ] Implement `MOCK_TOOLING` environment variable branches (live gcloud subprocess vs mock lists)
    - [ ] Develop vulnerability check rules (public IP on VM/SQL, run.invoker allUsers, public GKE)
- [ ] Task: Write automated unit tests for Discovery Engine
    - [ ] Create TDD failing unit tests in `tests/test_discovery.py`
    - [ ] Implement and verify all tests pass with >80% coverage
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Discovery Core Engine' (Protocol in workflow.md)

## Phase 2: Wiki Compilation & Scribe Integration
- [ ] Task: Develop Wiki markdown compilation
    - [ ] Build auto-generating folder and index cataloger mapping to `wiki/gcp/<PROJECT_ID>/README.md`
    - [ ] Style warnings using bold exposure flags (e.g. `⚠️ EXPOSED`)
- [ ] Task: Hook Discovery crawler to Planning Lead SRE workflow
    - [ ] Integrate discovery invocation into Scribe timeline logging
    - [ ] Save discovery results automatically to investigation registry artifacts
- [ ] Task: Implement unit and integration tests for Scribe discovery
    - [ ] Write failing test cases in `tests/test_scribe_discovery.py`
    - [ ] Complete implementation to make tests pass successfully
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Wiki Compilation & Scribe Integration' (Protocol in workflow.md)

## Phase 3: CLI & REST API Interfaces
- [ ] Task: Expose CLI discover command
    - [ ] Update `src/cli.py` to register `benjamin discover --project-id`
- [ ] Task: Expose SRE HTTP server endpoint
    - [ ] Add `GET /api/projects/<id>/discover` handler in `src/server.py`
- [ ] Task: Implement interface verification integration tests
    - [ ] Create test suite in `tests/test_server_discovery.py` and `tests/test_cli_discovery.py`
    - [ ] Run automated tests and confirm success
- [ ] Task: Conductor - User Manual Verification 'Phase 3: CLI & REST API Interfaces' (Protocol in workflow.md)
