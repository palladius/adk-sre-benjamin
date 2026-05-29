# Specification: core_ics_delegation_20260529

## Overview
This specification defines the core Incident Command System (ICS) architecture and lead delegation logic for **Project Benjamin**, implementing the first Behavior-Driven Development (BDD) feature scenario in [doc/bdd.md](file:///home/riccardo/git/adk-sre-benjamin/doc/bdd.md).

## Requirements & Scope

1. **Incident Trigger Ingestion:**
   - Implement an entrypoint that accepts incident triggers/payloads (e.g., JSON representing alert events like `"frontend_latency_slo_violated"`).

2. **Incident Commander (Benjamin):**
   - Implemented as an ADK-based `LlmAgent` or custom ADK Agent.
   - Outputs consistent visual branding/avatars (Bald man, Ferrari cap, castle) in its initial run logs or description.
   - On alert ingestion, Benjamin declares the incident active and assigns a unique Incident ID: `INC-YYYYMMDD-<random_hex>`.
   - Creates the active **Investigation Folder**: `investigations/INC-YYYYMMDD-<random_hex>/`.

3. **Multi-Agent Coordination & Delegation:**
   - Define a pure ADK agent hierarchy structure.
   - Instantiates four child Leads reporting directly to Benjamin:
     - **Ops Agent** (Operations Lead)
     - **Planning Agent** (Planning Lead)
     - **Logistics Agent** (Logistics Lead)
     - **Madhavi** (Communications Lead)
   - Benjamin delegates specific responsibilities to each lead based on the alert type, producing clean structured event signals.

4. **Communication Notification (Mocked / Basic CLI):**
   - Madhavi handles initial notification logic, simulating Telegram channel messages and ServiceNow ticket logs.

## Acceptance Criteria
- Given an alert event payload of `"frontend_latency_slo_violated"`.
- When the execution script runs.
- Then Benjamin parses the alert, creates the unique investigation directory, and instantiates the 4 ICS Leads.
- Then Benjamin successfully delegates the operational workflows to the respective leads.
- Then Madhavi logs the final dispatch notice summarizing the incident setup.
