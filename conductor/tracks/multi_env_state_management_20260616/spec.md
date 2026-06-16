# Spec: Make sense of state in multiple environments (local vs cloud)

## Overview
This track addresses state management across local and cloud environments, ensuring consistency and seamless transition. It introduces environment-specific folders for local development (dev, test, prod) using SRE_ENV/RAILS_ENV, and defines how state maps to cloud resources when running in a multi-homed cloud setup.

## Functional Requirements
1. **Environment-Specific Folders**:
   - Dynamically resolve the investigations directory using the environment variables `SRE_ENV` or `RAILS_ENV`.
   - Default to `investigations/dev` for development, `investigations/test` for test environments, and `investigations/prod` for production.
2. **Active State Management**:
   - Use `active_state.json` on the filesystem for local development.
   - Design a pluggable state tracker that allows database-backed storage (e.g., Firestore) when running in cloud environments.
3. **Discovery Assets Storage**:
   - Read/write discovery files (markdown, DOT graphs) to local directories under `discover/gcp-project` in development.
   - Support syncing/storing these assets in GCS or Firestore when running in cloud environments.

## Non-Functional Requirements
- Pluggable storage architecture to toggle between Local Filesystem and Cloud Providers.
- Performance: File and database operations must not block critical async execution paths.

## Acceptance Criteria
- Running with `SRE_ENV=production` puts files in `investigations/prod`.
- Running with `SRE_ENV=test` or in pytest puts files in `investigations/test`.
- Pluggable abstraction created or designed for Active State and Discovery Storage.
- Test suite passes with environment-specific directories.

## Out of Scope
- Complete implementation of Firestore sync or full GCS syncing (to be covered in a subsequent cloud integration track, e.g. Issue #9).
