# Specification - migrate the TF/CB logic from Pvt Codelab to here (Track: migrate_tf_cb_logic_20260616)

## 1. Overview
Migrate and validate the TF/CB logic from the private codelab.

Issue URL: https://github.com/palladius/adk-sre-benjamin/issues/15

## 2. Requirements & Selected Design
*   **Terraform Static Analysis**: Add a static check suite for the migrated Terraform files in the `terraform/` directory.
*   **Decoupled & Integrated Check Runner**:
    *   Expose a `just tf-validate` command that checks formatting (`terraform fmt -check`) and validates configuration (`terraform validate`).
    *   Integrate these checks into `bin/check_env.py` (which runs on `just check`) to verify both Terraform tool presence and configuration health.

## 3. Acceptance Criteria
*   Running `just tf-validate` runs validation checks successfully.
*   Running `just check` executes the Terraform configuration validation and outputs the diagnostics.
