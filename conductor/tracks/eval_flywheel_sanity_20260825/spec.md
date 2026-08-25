# Specification: Agent Quality Flywheel & ADK EVAL Sanity Integration

## Track ID
`eval_flywheel_sanity_20260825`

## Overview
Integrate the Agent Quality Flywheel skills (`google-agents-cli-eval` and `agent-platform-eval-flywheel`) as described in the Google Developers Blog post ("Driving the Agent Quality Flywheel from Your Coding Agent"). This track establishes robust, repeatable, automated evaluations for all Benjamin ADK agents (both in isolation and end-to-end integration scenarios), callable via `just eval`.

## Functional Requirements
1. **Flywheel Skills Installation**:
   - Install `.agents/skills/google-agents-cli-eval` and `.agents/skills/agent-platform-eval-flywheel` locally.
   - Configure local evaluation toolchain settings.
2. **ADK Agent Isolation & E2E Evals**:
   - Implement single-agent isolation evaluations for IC, Operations, Logistics, Planning, and Comms leads.
   - Implement end-to-end incident investigation integration scenarios.
   - Connect evaluation commands to `just eval` in the `Justfile`.
3. **Documentation**:
   - Create `doc/eval.md` detailing the 5-stage Flywheel loop (Prepare Data, Run Inference, Grade, Analyze Failures, Optimize & Iterate).
   - Link `doc/eval.md` in `README.md`.
4. **Actionable User TODO**:
   - Create `TODO_RICC.md` with explicit action items for Riccardo (e.g., reviewing `.eval.json` datasets, adding real-world incident traces, tuning AutoRaters/rubrics).

## Non-Functional Requirements
- Maintain fast execution options for local development while allowing deep LLM-as-judge grading via `just eval`.
- Ensure zero breaking changes to existing web server or agent execution pipelines.

## Acceptance Criteria
- Both flywheel skills are installed under `.agents/skills/`.
- `just eval` runs both agent-isolation and integration evaluation suites cleanly.
- `doc/eval.md` exists and is referenced in `README.md`.
- `TODO_RICC.md` exists with clear instructions for Riccardo.
- Full test suite (`just test`) passes without regressions.
