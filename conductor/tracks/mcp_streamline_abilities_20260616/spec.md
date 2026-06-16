# Specification - P1 Add MCP to streamline agents abilities (Track: mcp_streamline_abilities_20260616)

## 1. Overview
Introduce a secure model for SRE agents using MCP (Model Context Protocol) to execute gcloud commands. It enforces least privilege by separating read-only queries from mutations using two distinct Google Cloud Service Accounts and a Man-in-the-Loop (MITM) vetting layer.

Issue URL: https://github.com/palladius/adk-sre-benjamin/issues/22

## 2. Requirements & Design
*   **Dual Service Account Model**:
    1.  **Safe SRE Service Account (`safe-sre-investigator`)**: Configured with read-only viewer roles (Viewer, Logging Viewer, Monitoring Viewer). Cannot edit or delete any resources. Used by discovery and diagnostic agents.
    2.  **Unsafe Mutator SRE Service Account (`unsafe-sre-mutator`)**: Configured with Editor / mutation-capable roles. Restricted only to execution commands approved by a human.
*   **MCP Safe Executor (`safe_call_gcloud`)**:
    *   Exposes an MCP tool: `safe_call_gcloud(project_id, gcloud_tail)`.
    *   Executes read-only operations using the safe SA credentials.
*   **MITM Vetting Agent Layer**:
    *   Intercepts any proposed mutations.
    *   Integrates with the `pending_approvals.json` queue to request explicit operator confirmation via Telegram/Discord before running mutations under the unsafe SA credentials.

## 3. Acceptance Criteria
*   Agent calls to `safe_call_gcloud` run successfully with read-only access.
*   Attempts to run mutating commands directly are blocked by the safety gate.
*   Mutations are successfully intercepted, queued, and executed only upon human approval.
