# 🦖 TODO List for Riccardo (Agent Quality Flywheel & EVALs)

Hey RiccardinoCM26 🦖! Here are the action items for you to extend and refine Benjamin's evaluation flywheel:

---

## 📋 1. Review & Expand Evaluation Configurations (`eval/configs/`)
- [ ] Review `eval/configs/commander.eval.json` and add real edge-case prompts (e.g. multi-alert cascades, false alarms).
- [ ] Review `eval/configs/ops.eval.json` to verify high-frequency diagnostic query expectations against production logs.
- [ ] Review `eval/configs/logistics.eval.json` and expand risk assessment classification rules (LOW / MEDIUM / HIGH / CRITICAL).
- [ ] Review `eval/configs/planning.eval.json` and add rollback verification criteria.
- [ ] Review `eval/configs/comms.eval.json` to test multi-channel broadcast formatting (Markdown, HTML, Telegram templates).

---

## 🎭 2. Add Real Investigation Test Scenarios (`eval/scenarios/`)
- [ ] Add real-world GCP incident traces from `sre-next` under `eval/scenarios/` (e.g., GKE OOMKilled pod cascade, Cloud SQL storage exhaustion).
- [ ] Record OTel traces during live simulations (`just simulate`) and save trace fixtures for offline evaluation.

---

## 📊 3. AutoRater Tuning & Production Flywheel Setup
- [ ] Configure Gemini Enterprise Agent Platform GenAI Evaluation Service API keys or GCP credentials for live online AutoRaters.
- [ ] Customize the categorical rubrics (e.g., `sre_root_cause_accuracy`, `tool_call_correctness`) in `eval/runner.py`.
- [ ] Benchmark prompt optimizations using `just eval` and document baseline score improvements in `doc/eval.md`.
