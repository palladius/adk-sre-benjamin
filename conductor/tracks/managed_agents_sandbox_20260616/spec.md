# Specification - Use Managed Agents API to create a solid SRE agent sandbox (Track: managed_agents_sandbox_20260616)

## 1. Overview
This specification defines the requirements and architecture for creating a secure, isolated SRE Agent Sandbox using the Vertex AI / Gemini Managed Agents API (via `google-genai` SDK). The sandbox enables instantiating agents with specific context, playbooks, SRE Extension skills, and safe execution tools to troubleshoot outages.

## 2. Goals & Scope
- **Provisioning:** Ability to dynamically create, configure, and invoke Gemini Managed Agents.
- **SRE Extension Mount:** Expose SRE Extension skills to the agent via workspace mounting or file-based prompt loading.
- **AGENTS.md Context:** Utilize `.agents/AGENTS.md` (stored under `sandbox/`) to define agent personas, instructions, and rules.
- **Safe Tool Execution:** Bind the Safe Executor MCP server (Issue #22) to the agent's tool config to limit high-risk mutations.
- **GCS Playbook Integration:** Mount or synchronize GCP discovery files and playbooks from GCS.
- **Outage Triggering:** Allow starting a troubleshooting run with a query like "I have a possible outage, PTAL".

## 3. Tech Stack & Architecture
- **SDK:** `google-genai` SDK (Gemini Managed Agents / Vertex AI Agentic API).
- **Configuration Path:** `sandbox/.agents/AGENTS.md` for instructions, and `sandbox/skills/` for SRE Extension skills.
- **Tooling Interface:** Vertex AI Agent tool bindings mapped to the Safe Executor MCP server.
- **Authentication:** Application Default Credentials (ADC) with permissions to Vertex AI and GCS.

## 4. Acceptance Criteria
- Sandbox folder `sandbox/` created with standard `.agents/AGENTS.md` template.
- Implementation of `src/agents/managed_sandbox.py` or similar class/cli module to provision, deploy, and run the agent.
- Integration with GCP GCS bucket or local directory representing playbooks / discovery data.
- Safe Executor MCP tool bindings set up correctly.
- Unit and integration tests written and passing for managed agent creation and interaction.
