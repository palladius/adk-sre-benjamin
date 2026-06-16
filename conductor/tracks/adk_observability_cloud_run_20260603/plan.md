# Implementation Plan - ADK Observability + Cloud Run (Track: adk_observability_cloud_run_20260603)

## Phase 1: Dockerization and Cloud Run Deploy
- [x] d4d5371 Task: Dockerize Web Server
  - [x] Write a production-ready `Dockerfile` and `.dockerignore`.
  - [x] Add `deploy` target to `justfile` using `gcloud run deploy`.
- [x] d4d5371 Task: Basic / IAP Authentication
  - [x] Add header check middleware in `src/server.py` to validate user identity.

## Phase 2: OpenTelemetry Integration
- [x] bb95b3a Task: Install OTEL Dependencies
  - [x] Update `requirements.txt` with `opentelemetry-api` and `opentelemetry-sdk`.
- [x] bb95b3a Task: Instrument ADK Agents
  - [x] Add tracer instrumentation to core agent execution loops in `src/agents/`.

## Phase 3: Verification
- [x] bb95b3a Task: End-to-End Verification
  - [x] Deploy to staging environment.
  - [x] Verify trace logs export correctly.
