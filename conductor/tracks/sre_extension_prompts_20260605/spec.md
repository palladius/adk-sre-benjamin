# Specification: Use SRE Extension and PoMo Skills with External Prompts

## Overview
This specification details the transition of agent prompts from in-code configurations to external YAML templates stored under a dedicated `etc/prompts/` directory. It also integrates SRE Extension skills (for the Operations Lead agent) and Post-Mortem (PoMo) skills (for the Planning Lead/Scribe and Communications Lead agents) into their system instructions dynamically.

## Functional Requirements

1. **Prompts Relocation**:
   - Create a directory `etc/prompts/` at the repository root.
   - Relocate/copy all YAML prompt templates from `src/prompts/` to `etc/prompts/`.
   - Update `src/prompt_loader.py` to default to `etc/prompts/` as the primary lookup path (relative to the repository root).
   - Retain fallback logic to `src/prompts/` to ensure backwards compatibility and test stability.

2. **Jinja2 Templating with Context variables**:
   - Update agent prompt templates to accept context variables like `incident_id` or `investigation_folder` (e.g. `investigations/{{ incident_id }}/`).
   - Allow agents to pass dynamic keyword arguments to `load_prompt` during construction or execution.

3. **Operations Lead (Ops Agent) Skill Integration**:
   - Automatically search and load the following SRE Extension skills upon `OperationsLead` initialization:
     - `investigation-entrypoint`
     - `cloud-logging`
     - `cloud-monitoring`
     - `safe-sre-investigator`
     - `gcp-setup`
     - `anomaly-detection`
   - Dynamically append these loaded skill instructions to the `OperationsLead` agent's system instructions.

4. **Communications & Planning Lead (Scribe) Skill Integration**:
   - Update `CommunicationsLead` and `PlanningLead` to automatically search and load PoMo (Post-Mortem) skills upon initialization:
     - `postmortem-generator`
     - `postmortem-aggregator`
   - Dynamically append these loaded skill instructions to their system instructions.
   - Update `CommunicationsLead` constructor to support `loaded_skills`.

5. **Skill Directory Portability**:
   - Enhance `SkillAdapter` search paths in `src/skills_adapter.py` to resolve directories relative to the user's home directory (`~/...` via `os.path.expanduser`), supporting different local environments seamlessly.

## Acceptance Criteria
- Prompt templates exist under `etc/prompts/`.
- `prompt_loader.py` loads prompts from `etc/prompts/` by default.
- Ops agent system instructions include instructions from `investigation-entrypoint`, `cloud-logging`, `cloud-monitoring`, `safe-sre-investigator`, etc., if available in the path.
- Planning Lead and Communications Lead system instructions include instructions from `postmortem-generator` and `postmortem-aggregator` if available.
- Unit tests pass successfully.
