# Plan: GCP Resource Discovery and Asset Audit

## Phase 1: Discovery Core Engine
- [x] Task: Implement core resource crawling logic
    - [x] Create `src/discovery.py` module
    - [x] Write GCE VM, Cloud Run, GKE, and Cloud SQL resource crawlers
    - [x] Implement `MOCK_TOOLING` environment variable branches (live gcloud subprocess vs mock lists)
    - [x] Develop vulnerability check rules (public IP on VM/SQL, run.invoker allUsers, public GKE)
- [x] Task: Write automated unit tests for Discovery Engine
    - [x] Create TDD failing unit tests in `tests/test_discovery.py`
    - [x] Implement and verify all tests pass with >80% coverage
- [x] Task: Conductor - User Manual Verification 'Phase 1: Discovery Core Engine' (Protocol in workflow.md)

## Phase 2: Wiki Compilation & Scribe Integration
- [x] Task: Develop Wiki markdown compilation
    - [x] Build auto-generating folder and index cataloger mapping to `wiki/gcp/<PROJECT_ID>/README.md`
    - [x] Style warnings using bold exposure flags (e.g. `⚠️ EXPOSED`)
- [x] Task: Hook Discovery crawler to Planning Lead SRE workflow
    - [x] Integrate discovery invocation into Scribe timeline logging
    - [x] Save discovery results automatically to investigation registry artifacts
- [x] Task: Implement unit and integration tests for Scribe discovery
    - [x] Write failing test cases in `tests/test_scribe_discovery.py`
    - [x] Complete implementation to make tests pass successfully
- [x] Task: Conductor - User Manual Verification 'Phase 2: Wiki Compilation & Scribe Integration' (Protocol in workflow.md)

## Phase 3: CLI & REST API Interfaces
- [x] Task: Expose CLI discover command
    - [x] Update `src/cli.py` to register `benjamin discover --project-id`
- [x] Task: Expose SRE HTTP server endpoint
    - [x] Add `GET /api/projects/<id>/discover` handler in `src/server.py`
- [x] Task: Implement interface verification integration tests
    - [x] Create test suite in `tests/test_server_discovery.py` and `tests/test_cli_discovery.py`
    - [x] Run automated tests and confirm success
- [x] Task: Conductor - User Manual Verification 'Phase 3: CLI & REST API Interfaces' (Protocol in workflow.md)
