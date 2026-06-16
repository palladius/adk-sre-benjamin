# Specification: Disable Mock Fallback in Development

## Overview
Currently, the Project Benjamin SRE discovery engine automatically falls back to mock resources if live discovery returns nothing (due to gcloud errors, no permission, or no assets). In development mode (where `MOCK_TOOLING=false`), silent fallback to mock data is undesirable, as it masks authentication issues, incorrect project configurations, or missing permissions, confusing developers into thinking they are viewing live data.

This track aims to:
1. Correct the default `PROJECT_ID` configuration in `.env` to `sre-next` (the authorized project under active credentials).
2. Modify the live discovery fallback logic so that in development (with `MOCK_TOOLING=false`), if live discovery fails or returns no resources, the system throws/returns an explicit error rather than silently falling back to mock resources.
3. Update unit and integration tests to ensure correct behavior in test vs. development environments.

## Functional Requirements
1. **Target Project Update**: Update `.env` to set `PROJECT_ID='sre-next'` instead of `sre-next-dev`.
2. **Strict Mode in Development**:
   - In `src/discovery.py`, check the environment setting. If `MOCK_TOOLING` is set to `false`, do NOT fallback to `mock_resources` when `resources` is empty.
   - Raise a clear exception or return an error response that is displayed clearly to the developer/user.
3. **Frontend Warning/Error State**:
   - If live discovery fails, the frontend should display a clear error message indicating that live discovery failed/lacked permissions rather than showing mock/demo data.

## Non-Functional Requirements
- Maintain existing test cases. Ensure unit tests running under `MOCK_TOOLING=true` or in test suites can still mock resources properly.
- Fast and reliable error reporting.

## Acceptance Criteria
- Running `discover_project_resources("sre-next-dev")` with `MOCK_TOOLING=false` in development raises a `RuntimeError` or returns a clear error status instead of silently returning mock data.
- The default `.env` uses `PROJECT_ID='sre-next'`.
- Running the application in development displays the live resources from the `sre-next` project and is not showing mock data.
- If we intentionally target a non-existent project (like `sre-next-dev`) or run without valid credentials in development with `MOCK_TOOLING=false`, the UI shows a clear "Live discovery failed" error page/banner instead of mock data.

## Out of Scope
- Migrating or configuring other GCP projects.
- Changing production fallback behavior (if production fallback is desired for safety, though we target development environment here).
