# Implementation Plan - migrate the TF/CB logic from Pvt Codelab to here (Track: migrate_tf_cb_logic_20260616)

## Phase 1: Define Validation Commands
- [x] Task: Add standalone validation target to justfile
  - [x] Add `tf-validate` target to run `terraform fmt -check` and `terraform validate` inside the `terraform/` directory.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Define Validation Commands' (Protocol in workflow.md)

## Phase 2: Environment Diagnostic Check
- [x] Task: Integrate Terraform checks into check_env.py
  - [x] Update `bin/check_env.py` to look for `terraform` binary on PATH.
  - [x] Run `terraform validate` inside the `bin/check_env.py` logic and report status.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Environment Diagnostic Check' (Protocol in workflow.md)

## Phase 3: Verification
- [x] Task: Run and verify validation checks
  - [x] Run `just tf-validate` locally and verify output.
  - [x] Run `just check` and confirm Terraform validation results are printed correctly.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Verification' (Protocol in workflow.md)
