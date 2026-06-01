# Specification: sre_skills_integration_20260601

## Overview
This specification defines the architecture, data structures, and integration boundaries for a **Modular SRE Skill Adapter** in Project Benjamin. It enables the Python ADK SRE agents to dynamically discover, parse, and leverage the pre-authored incident-response and diagnostics skills from the **Gemini CLI SRE Extension** repository.

## Requirements & Scope

1. **Dynamic Skill Loader (`src/skills_adapter.py`):**
   - Provide a `SkillAdapter` class to manage skill directory resolution.
   - Implement `load_sre_skill(skill_name: str) -> dict`:
     - Resolve the target skill folder path inside configured extension locations (e.g. `/home/riccardo/.gemini/config/plugins/palladius-common-commands/skills/` or a custom mock path for test validation).
     - Load and parse the `SKILL.md` file, separating the YAML frontmatter (e.g., `name`, `description`) from the markdown execution payload.
     - Return a dictionary containing the parsed frontmatter metadata and the instruction block.

2. **ADK Agent Integration (`src/agents/`):**
   - Allow SRE agents (like the Operations Lead or Planning Lead) to be initialized with active SRE extension skills.
   - Provide a pattern where the loaded skill's markdown instruction block is cleanly appended to the agent's system instructions, extending its capabilities dynamically.
   - Expose skill helper scripts or subprocess execution handles as callable Python ADK `tools` (e.g., executing the skill's diagnostics workflows).

3. **Validation & Test Suite:**
   - Create unit tests under `tests/test_skills.py` validating:
     - Frontmatter YAML parsing accuracy.
     - Skill discovery and loading under custom mock paths.
     - Integration of the loaded prompt directives into an ADK `LlmAgent`.

## Acceptance Criteria
- Running `pytest tests/test_skills.py` passes cleanly with >80% code coverage.
- SRE agents can import and run with both real and mocked SRE extension skills successfully.
