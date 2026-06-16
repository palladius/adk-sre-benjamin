# Implementation Plan - migrate the TF/CB logic from Pvt Codelab to here (Track: migrate_tf_cb_logic_20260616)

## Phase 1: Define Validation Commands
- [ ] Task: Add standalone validation target to justfile
  - [ ] Add `tf-validate` target to run `terraform fmt -check` and `terraform validate` inside the `terraform/` directory.

## Phase 2: Environment Diagnostic Check
- [ ] Task: Integrate Terraform checks into check_env.py
  - [ ] Update `bin/check_env.py` to look for `terraform` binary on PATH.
  - [ ] Run `terraform validate` inside the `bin/check_env.py` logic and report status.

## Phase 3: Verification
- [ ] Task: Run and verify validation checks
  - [ ] Run `just tf-validate` locally and verify output.
  - [ ] Run `just check` and confirm Terraform validation results are printed correctly.
