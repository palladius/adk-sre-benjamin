# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-06-01
### Added
- **Dynamic GCP Project ID Input**: Introduced a glassmorphic Project ID input in the SRE dashboard sidebar allowing custom override values.
- **Project ID Trigger Payload**: Configured `/api/simulate` payload submission to use the custom Project ID specified in the UI.
- **GCP Project ID Fallback**: Added fallback checking inside the `parse_trigger` parsing utility to load project ID from `.env` (using `GCP_PROJECT_ID` or `PROJECT_ID`) when blank/absent.
- **Human-In-The-Loop (HITL) Safety Clearance**: Developed approval/rejection button panel controls directly linked to REST APIs `/api/incidents/<id>/approve` and `/api/incidents/<id>/reject`.
- **Safety Gate States Rendering**: Styled risk assessment highlights in neon colors based on state ("AWAITING CLEARANCE", "REJECTED", "EXECUTED").
- **Interactive Contextual Chat Agent**: Designed and styled an interactive SRE Co-Pilot chat panel in Outfit/Mono font colors.
- **Tactical SRE Commander Agent Backend**: Exposed GET/POST REST APIs `/api/incidents/<id>/chat` to load/save chat history logs and simulate an SRE Incident Commander Agent that responds contextually to operator queries.
- **Service Account Setup script (`bin/create_svc_acct.sh`)**: Engineered an SRE service account creation and configuration bash script that binds least-privilege R/O viewer/logging roles and exports keys directly to `private/`.
- **Extended Test Suite**: Added a fallback environment variable unit test under `tests/test_trigger.py` and integration tests for the SRE chat endpoints inside `tests/test_server.py`.
