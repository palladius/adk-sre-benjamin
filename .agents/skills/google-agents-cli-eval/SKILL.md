---
name: google-agents-cli-eval
description: 5-stage Agent Quality Flywheel evaluation skill for ADK agents using the agents-cli toolchain.
metadata:
  version: "1.0.0"
---

# Google Agents CLI Eval Skill

This skill encodes the 5-stage Agent Quality Flywheel for ADK agents built with the `agents-cli` toolchain, as detailed in the Google Developers Blog ("Driving the Agent Quality Flywheel from Your Coding Agent").

## The 5 Flywheel Stages

1. **Prepare Data**:
   - Synthesize synthetic scenarios via `agents-cli eval dataset synthesize` or compile traces from OTel logs / hand-crafted test cases.
   - Example:
     ```bash
     agents-cli eval dataset synthesize -n 5 --max-turns 8 --model gemini-2.5-flash \
       --instruction "$(cat eval_instruction.txt)" \
       -o traces_dataset.json
     ```

2. **Run Inference**:
   - Execute agent models over the evaluation dataset to produce conversation traces (skip if traces already exist).

3. **Grade**:
   - Score traces using adaptive AutoRaters (`multi_turn_task_success`, `multi_turn_trajectory_quality`) or custom categorical rubrics.
   - Example:
     ```bash
     agents-cli eval grade --traces traces_merged.json --config eval_config.yaml
     ```

4. **Analyze Failures**:
   - Read rubric verdicts to determine root causes. For $\ge 10$ failures, trigger Automatic Loss Analysis.

5. **Optimize & Iterate**:
   - Propose targeted prompt or tool routing fixes, re-run grading, and compare against baseline metrics.
