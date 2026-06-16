# Implementation Plan - ADK Observability + Cloud Run (Track: adk_observability_cloud_run_20260603)

## Phase 1: Dockerization and Cloud Run Deploy
- [x] d4d5371 Task: Dockerize Web Server
  - [x] Write a production-ready `Dockerfile` and `.dockerignore`.
  - [x] Add `deploy` target to `justfile` using `gcloud run deploy`.
- [x] d4d5371 Task: Basic / IAP Authentication
  - [x] Add header check middleware in `src/server.py` to validate user identity.

## Phase 2: OpenTelemetry Integration
- [~] Task: Install OTEL Dependencies
  - [ ] Update `requirements.txt` with `opentelemetry-api` and `opentelemetry-sdk`.
- [ ] Task: Instrument ADK Agents
  - [ ] Add tracer instrumentation to core agent execution loops in `src/agents/`.

## Phase 3: Verification
- [ ] Task: End-to-End Verification
  - [ ] Deploy to staging environment.
  - [ ] Verify trace logs export correctly.
