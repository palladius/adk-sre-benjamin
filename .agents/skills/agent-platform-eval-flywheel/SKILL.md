---
name: agent-platform-eval-flywheel
description: Framework-agnostic Python SDK for Gemini Enterprise Agent Platform Evaluation API flywheel loops.
metadata:
  version: "1.0.0"
---

# Agent Platform Eval Flywheel Skill

This skill provides a Python SDK wrapper around the Gemini Enterprise Agent Platform Evaluation API for executing continuous quality flywheel loops across any agent framework (including ADK Python agents).

## Core Capabilities

1. **Dataset & Trace Ingestion**:
   - Parse OpenTelemetry (OTel) traces or local JSON traces into `EvalSet` objects.

2. **AutoRater Grading**:
   - Compute `multi_turn_task_success` and `multi_turn_trajectory_quality` scores.
   - Define custom categorical rubrics (e.g., `sre_root_cause_accuracy`, `tool_call_correctness`, `reconciliation_honored`).

3. **Decoupled Evaluation**:
   - Ensure the optimizer proposed fixes are graded independently by the GenAI Evaluation Service to prevent gaming metrics.

4. **Comparative Analysis**:
   - Compare before/after test runs and calculate metric deltas across prompt/code iterations.
