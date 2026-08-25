# Implementation Plan: Agent Quality Flywheel & ADK EVAL Sanity Integration

## Track ID
`eval_flywheel_sanity_20260825`

## Workflow Methodology
Strict adherence to `conductor/workflow.md` (TDD, red-green-refactor, phase verification checkpoints, coverage gates, version bumping).

---

## Phase 1: Local Flywheel Skills Installation & Setup

- [x] Task: Install `google-agents-cli-eval` and `agent-platform-eval-flywheel` skills locally into `.agents/skills/`
- [x] Task: Verify skill file structures and catalog registration
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md)

---

## Phase 2: ADK Agent Isolation & E2E Integration Evals Implementation

- [ ] Task: Create red unit tests for evaluation runners (`tests/test_eval_flywheel.py`)
- [ ] Task: Implement agent isolation evaluation configs and scripts (`eval/configs/`)
- [ ] Task: Implement end-to-end incident investigation scenario evaluation scripts (`eval/scenarios/`)
- [ ] Task: Integrate `just eval` command in `Justfile` to run both isolation & E2E evals
- [ ] Task: Verify green pass of evaluation runner test suite
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

---

## Phase 3: Documentation & User Action Items (TODO_RICC.md)

- [ ] Task: Create `doc/eval.md` detailing the 5-stage Quality Flywheel loop
- [ ] Task: Update `README.md` to link `doc/eval.md`
- [ ] Task: Create `TODO_RICC.md` with explicit action items for Riccardo (dataset review, real incident traces, AutoRater tuning)
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
