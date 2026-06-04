# Specification: ADK Observability + Cloud Run (Track: adk_observability_cloud_run_20260603)

## 1. Overview
This track delivers deployment capability for the Project Benjamin SRE framework to Google Cloud Run, secured via IAP or simple basic authentication, and embeds full OpenTelemetry (OTEL) logging/tracing inside the ADK agent communication loops.

---

## 2. Functional Requirements
* **Docker & Deployment**: Build a Dockerfile for the web server and add a `just deploy` pipeline target.
* **Access Control**: Secure the Cloud Run web application using Google Cloud Identity-Aware Proxy (IAP) or L7 basic authentication.
* **Observability (OTEL)**: Configure OpenTelemetry tracing in Python for all inter-agent messages and tool execution paths.

---

## 3. Acceptance Criteria
* The app compiles, builds, and deploys to Cloud Run with `just deploy`.
* Access to the dashboard is blocked unless authenticated.
* Inter-agent conversation execution logs export clean OTEL traces.
