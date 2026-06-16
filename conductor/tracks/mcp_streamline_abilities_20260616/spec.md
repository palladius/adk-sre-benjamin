# Specification - P1 Add MCP to streamline ahents abilities (Track: mcp_streamline_abilities_20260616)

## 1. Overview
P1 Add MCP to streamline ahents abilities

Issue URL: https://github.com/palladius/adk-sre-benjamin/issues/22

## 2. Description
We should add an MCP with tools like:

1. `safe_gcloud`: to combine ability to execute ANY `gcloud XXX ` command under the safe Service Account use. And also kubectl (TODO find how to, lets start without).
2. `unsafe_gcloud`: to allow use of a powerful ServiceAccount. This tool will be available onlt to the unsafe executor which is vetted by the vetting agent.

## Plan of action

Let's start with just (1).
1. terraform the 2 srervice accounts
2. Create MCP tools for 1.
3. attach this tool to the operator

Testing:

Let's use it for discovery and use the same ops agent for discovery. of cours eprompting might be different so we might considr a Discovery agent, with its own custom prompting, but basically the SAME MCP.

## Open topics

Lets start with a single project id, but we should consider in the MCP that project_id is part of the arguments (so potentially in the future we can relax this).

## 3. Acceptance Criteria
* The feature is fully implemented according to the issue requirements.
* Unit/integration tests are written and passing.
