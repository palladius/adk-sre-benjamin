# ADK Agent Isolation & Integration Evaluation Harness Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a robust ADK native evaluation harness with isolated agent evalsets, integration scenario evals, and ROUGE scoring, executable via `just eval`.

**Architecture:** Refactor agent wrappers to use ADK `InMemoryRunner` and bind native tools to `google.adk.agents.Agent` instances. Create ADK native evalsets for each of the 5 SRE leads (Commander, Comms, Ops, Planning, Logistics) and an E2E integration scenario, configured via `eval_config.json`. Create a unified python eval runner `tests/eval/eval_runner.py` computing ROUGE metrics and calling `adk eval`, exposed via `just eval`.

**Tech Stack:** Python 3.13, Google ADK (2.7.1), google-genai, ROUGE Score (`rouge-score`), Pytest, Justfile.

---

### Task 1: Update Dependencies in `requirements.txt`

**Files:**
- Modify: `requirements.txt`
- Test: Run `uv pip list`

**Step 1: Write the updated requirements.txt**

Add `google-adk>=2.7.0`, `google-genai>=2.12.0`, `rouge-score>=0.1.2` to `requirements.txt`.

**Step 2: Run pip install**

Run: `UV_INDEX_URL="https://pypi.org/simple" uv pip install -r requirements.txt`
Expected: Successfully installed google-adk, google-genai, and rouge-score.

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "build: add google-adk, google-genai, and rouge-score to requirements.txt"
```

---

### Task 2: Refactor Agent Classes to use ADK `InMemoryRunner` & Native Tools

**Files:**
- Modify: `src/agents/commander.py`
- Modify: `src/agents/comms.py`
- Modify: `src/agents/ops_lead.py`
- Modify: `src/agents/planning_lead.py`
- Modify: `src/agents/logistics_lead.py`
- Test: `tests/test_agents.py`

**Step 1: Write failing test in `tests/test_agents.py`**

Test that `.run(prompt)` uses `InMemoryRunner` or returns valid agent execution outputs rather than static mock strings when an ADK agent is queried.

**Step 2: Run test to verify failure**

Run: `uv run pytest tests/test_agents.py -k test_agent_run_methods`

**Step 3: Implement ADK `InMemoryRunner` execution in agent classes**

Update `src/agents/*.py` so `run(prompt)` uses `google.adk.runners.InMemoryRunner` with `google.adk.agents.Agent` and fallback if API key is not present. Ensure tools are properly attached to the `Agent` objects.

**Step 4: Run test to verify pass**

Run: `uv run pytest tests/test_agents.py`
Expected: PASS

**Step 5: Commit**

```bash
git add src/agents/ tests/test_agents.py
git commit -m "refactor(agents): integrate ADK InMemoryRunner and tool bindings"
```

---

### Task 3: Create ADK Eval Configuration & Isolated Agent Evalsets

**Files:**
- Create: `tests/eval/eval_config.json`
- Create: `tests/eval/evalsets/commander_evalset.json`
- Create: `tests/eval/evalsets/comms_evalset.json`
- Create: `tests/eval/evalsets/ops_evalset.json`
- Create: `tests/eval/evalsets/planning_evalset.json`
- Create: `tests/eval/evalsets/logistics_evalset.json`

**Step 1: Create `tests/eval/eval_config.json`**

Define criteria for `tool_trajectory_avg_score`, `response_match_score`, `final_response_match_v2`, and `rubric_based_final_response_quality_v1`.

**Step 2: Create isolated agent evalsets in `tests/eval/evalsets/`**

Create evalsets for each of the 5 agents:
- `commander_evalset.json`: Tests incident declaration and role coordination.
- `comms_evalset.json`: Tests broadcasting updates and HITL authorization requests.
- `ops_evalset.json`: Tests metric triage, log checks, and mutation proposals.
- `planning_evalset.json`: Tests timeline scribing, commit annotation, and discovery summary.
- `logistics_evalset.json`: Tests command safety evaluation, risk calculation, and quota checks.

**Step 3: Verify JSON formatting**

Run: `uv run python3 -c "import json, glob; [json.load(open(f)) for f in glob.glob('tests/eval/**/*.json', recursive=True)]; print('JSON Valid!')"`
Expected: Output "JSON Valid!"

**Step 4: Commit**

```bash
git add tests/eval/
git commit -m "feat(eval): add ADK eval_config.json and 5 isolated agent evalsets"
```

---

### Task 4: Create Multi-Turn Integration Scenario Evalset

**Files:**
- Create: `tests/eval/evalsets/integration_evalset.json`

**Step 1: Create `integration_evalset.json`**

Define an end-to-end incident response trajectory:
Turn 1: Alert trigger -> Commander declaration
Turn 2: Comms broadcast & Logistics quota check
Turn 3: Ops triage & log/metric query
Turn 4: Logistics risk assessment & safety hold
Turn 5: HITL safety clearance & mutation execution -> Planning scribe resolution.

**Step 2: Verify JSON syntax**

Run: `uv run python3 -c "import json; json.load(open('tests/eval/evalsets/integration_evalset.json')); print('Integration Evalset Valid!')"`
Expected: Output "Integration Evalset Valid!"

**Step 3: Commit**

```bash
git add tests/eval/evalsets/integration_evalset.json
git commit -m "feat(eval): add multi-turn integration scenario evalset"
```

---

### Task 5: Create Python ROUGE & Native ADK Eval Runner

**Files:**
- Create: `tests/eval/eval_runner.py`
- Create: `tests/test_eval_harness.py`

**Step 1: Write `tests/eval/eval_runner.py`**

Implement:
1. `calculate_rouge_scores(reference, candidate)`: Computes ROUGE-1, ROUGE-2, and ROUGE-L precision/recall/f1-scores using `rouge_score.rouge_scorer`.
2. `run_isolated_agent_evals()`: Runs evaluation for each agent, comparing outputs against expected responses with ROUGE metrics.
3. `run_adk_native_evals()`: Executes `adk eval` CLI programmatically or via sub-process for all evalsets in `tests/eval/evalsets/`.
4. `run_integration_eval()`: Evaluates full integration flow against `integration_evalset.json`.

**Step 2: Write pytest wrapper `tests/test_eval_harness.py`**

Create pytest unit test that invokes `tests/eval/eval_runner.py` to ensure high test coverage and automatic execution during pytest runs.

**Step 3: Run the eval runner**

Run: `uv run python3 tests/eval/eval_runner.py`
Expected: Output showing isolated agent eval results, ROUGE scores, and integration scenario scores.

**Step 4: Commit**

```bash
git add tests/eval/eval_runner.py tests/test_eval_harness.py
git commit -m "feat(eval): add unified ROUGE and ADK native eval runner"
```

---

### Task 6: Add `just eval` Recipe to `justfile` & Verify Full Suite

**Files:**
- Modify: `justfile`
- Test: Run `just eval`

**Step 1: Update `justfile`**

Add `eval:` target to `justfile`:

```justfile
# Run ADK agent evals (isolation + integration + ROUGE metrics)
eval:
    @uv run python3 tests/eval/eval_runner.py
```

**Step 2: Test `just eval`**

Run: `just eval`
Expected: Successful execution of all isolated agent evaluations, ROUGE scoring, and integration scenario evaluation.

**Step 3: Run `just test` to verify no regressions**

Run: `just test` or `uv run pytest`
Expected: All tests passing cleanly.

**Step 4: Commit**

```bash
git add justfile
git commit -m "feat(justfile): add just eval target for ADK agent evaluations"
```
