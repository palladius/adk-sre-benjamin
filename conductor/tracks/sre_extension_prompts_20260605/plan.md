# Implementation Plan: Use SRE Extension and PoMo Skills with External Prompts

## Phase 1: Prompts Relocation and Templating Support
- [ ] Task: Create `etc/prompts/` directory and copy files
    - [ ] Create `etc/prompts/` directory at repository root
    - [ ] Copy prompt templates `benjamin.yaml`, `logistics_agent.yaml`, `madhavi.yaml`, `ops_agent.yaml`, `planning_agent.yaml` to `etc/prompts/`
- [ ] Task: Write tests for prompt loader lookup logic
    - [ ] Write test in `tests/test_prompts.py` asserting prompt files are loaded from `etc/prompts/` by default
- [ ] Task: Update `src/prompt_loader.py` to default to `etc/prompts/`
    - [ ] Modify `prompt_loader.py` to resolve `etc/prompts/` relative to repository root and load prompts from there with fallback to `src/prompts/`
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Prompts Relocation and Templating Support' (Protocol in workflow.md)

## Phase 2: Portability & SRE Extensions Skill Loading
- [ ] Task: Write tests for `SkillAdapter` path expansion
    - [ ] Write test in `tests/test_skills.py` verifying `SkillAdapter` search paths expand `~` correctly
- [ ] Task: Update `SkillAdapter` search paths with path expansion
    - [ ] Modify `src/skills_adapter.py` to resolve `~` directories using `os.path.expanduser`
- [ ] Task: Write tests for automatic skill discovery in agent initialization
    - [ ] Write tests in `tests/test_skills.py` asserting Ops, Planning, and Comms agents automatically load SRE Extension and PoMo skills when initialized
- [ ] Task: Implement automatic skill loading in agents
    - [ ] Modify `src/agents/ops_lead.py` to automatically load SRE Extension skills
    - [ ] Modify `src/agents/planning_lead.py` and `src/agents/comms.py` to automatically load PoMo skills
    - [ ] Modify `src/agents/comms.py` to support `loaded_skills` parameter and inject them into `system_instruction`
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Portability & SRE Extensions Skill Loading' (Protocol in workflow.md)
