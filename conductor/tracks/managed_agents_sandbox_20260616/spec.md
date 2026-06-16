# Specification - Use Managed Agents API to create a solid SRE agent sandbox (Track: managed_agents_sandbox_20260616)

## 1. Overview
Use Managed Agents API to create a solid SRE agent sandbox

Issue URL: https://github.com/palladius/adk-sre-benjamin/issues/23

## 2. Description
OMG I got a vision. Think of this:

Instance an agent with: 

* An `.agents/AGENTS.md` which tells it o use skills from SRE Extension
* a mounted download of SRE Extension
* An MCP for safe executor (depends on https://github.com/palladius/adk-sre-benjamin/issues/22 )
* Super-duper: GCS mount of GCP discovery/playbooks.
* You can just instantiate with "I have a possible outage, PTAL".

## Sources
1. https://www.philschmid.de/gemini-managed-agents-developer-guide
2. https://www.philschmid.de/how-managed-agents-work 


## 3. Acceptance Criteria
* The feature is fully implemented according to the issue requirements.
* Unit/integration tests are written and passing.
