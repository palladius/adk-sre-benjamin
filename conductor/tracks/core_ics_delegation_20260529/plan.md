# Implementation Plan: core_ics_delegation_20260529

## Phase 1: Scaffolding and Trigger Ingestion [checkpoint: 5861e0c]

- [x] Task: Define the SRE incident directory structures and trigger models [f379115]
    - [x] Write unit tests for trigger parsing and directory scaffolding [f379115]
    - [x] Implement the trigger parser and folder generation logic [f379115]
- [x] Task: Conductor - User Manual Verification 'Phase 1: Scaffolding and Trigger Ingestion' (Protocol in workflow.md)

## Phase 2: Core ICS Agents and Delegation

- [~] Task: Set up Jinja2 prompt template loaders and core ADK agents
    - [x] Write unit tests verifying Jinja2 template loading, variable hydration, and ADK configuration [bf748e4]
    - [x] Implement the prompt loader utility and write templated system prompts for all 5 agents [bf748e4]
    - [ ] Implement the Google ADK Agents using LlmAgent and structure the hub-and-spoke tree
- [ ] Task: Implement SRE Mock Incident Harness and piped Agent CLI runner
    - [ ] Write unit tests for mock incident loading and piped agent stdin parsing
    - [ ] Create CLI runner in src/cli.py and mock incident fixtures
- [ ] Task: Implement top-down delegation flows
    - [ ] Write unit tests for alert routing and delegation signal handling
    - [ ] Implement Benjamin's delegation router that activates the 4 leads on alert trigger
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Core ICS Agents and Delegation' (Protocol in workflow.md)

## Phase 3: Logging and Communication Integration

- [ ] Task: Integrate Scribe folder and Madhavi notifications
    - [ ] Write unit tests for initial investigation folder state writing and Madhavi's channel dispatching
    - [ ] Implement Scribe's initial state file creation and Madhavi's mockup notification dispatchers
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Logging and Communication Integration' (Protocol in workflow.md)
