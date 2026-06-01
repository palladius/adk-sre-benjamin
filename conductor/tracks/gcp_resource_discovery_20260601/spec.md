# Specification: GCP Resource Discovery and Asset Audit

## 1. Overview
This feature introduces automated GCP resource crawling and discovery for Project Benjamin. Given a GCP Project ID, the Planning Lead coordinates with the discovery module to crawl and catalog key cloud resources:
- Compute Engine (GCE) VMs
- Cloud Run Services
- Google Kubernetes Engine (GKE) Clusters
- Cloud SQL Database Instances

The discovery results are logged, audited for exposure vulnerabilities (triggering bold red warning flags for open resources), and persisted under a permanent, structured self-indexing workspace layout matching `wiki/gcp/<PROJECT_ID>/README.md`.

---

## 2. Functional Requirements

### 2.1 Interface & Access
- **CLI Utility**: Exposed via `benjamin discover --project-id <PROJECT_ID>`.
- **API Endpoint**: Served via `GET /api/projects/<PROJECT_ID>/discover` returning a structured JSON list of resources, status warnings, and the output path.

### 2.2 GCP Resource Crawling & Auditing
The discovery module crawls and audits the following assets:
1. **Compute Engine (GCE) VMs**:
   - Discovers active VM instances.
   - **Vulnerability flag**: Raises a warning if the VM has any external/public IP bound to it.
2. **Cloud Run Services**:
   - Discovers deployed services.
   - **Vulnerability flag**: Raises a warning if the IAM policy binds `allUsers` to `roles/run.invoker` (unauthenticated public access).
3. **GKE Clusters**:
   - Discovers container clusters.
   - **Vulnerability flag**: Raises a warning if public endpoint access is enabled or if private cluster options are disabled.
4. **Cloud SQL Instances**:
   - Discovers database instances.
   - **Vulnerability flag**: Raises a warning if public IP is enabled and no authorized networks restriction is specified.

### 2.3 Mock & Live Modes (`MOCK_TOOLING`)
- **Live Mode (`MOCK_TOOLING=false`)**: Automatically triggers real-time `gcloud` subprocess commands securely utilizing the active service account credentials context.
- **Mock Mode (`MOCK_TOOLING=true`)**: Emulates realistic structured GCP resources and vulnerabilities, enabling rapid frontend development and local testing.

### 2.4 Scribe & Wiki Compilation
- Saves the audited topology under a clean, markdown-formatted wiki structure: `wiki/gcp/<PROJECT_ID>/README.md`.
- Exposed/vulnerable assets are highlighted with distinct bold warning marks (e.g. `⚠️ EXPOSED`).

---

## 3. Acceptance Criteria
- Running `benjamin discover` creates the correct project directory and populates `wiki/gcp/<PROJECT_ID>/README.md` with properly structured and flagged resources.
- `GET /api/projects/<id>/discover` returns valid JSON with all discovered resources and vulnerability flags.
- Comprehensive unit tests cover `MOCK_TOOLING` mock/live toggle routes, parsing logic, and vulnerability rules.
