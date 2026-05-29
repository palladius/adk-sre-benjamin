# Implementation Plan: core_ics_delegation_20260529

## Phase 1: Scaffolding and Trigger Ingestion [checkpoint: 5861e0c]

- [x] Task: Define the SRE incident directory structures and trigger models [f379115]
    - [x] Write unit tests for trigger parsing and directory scaffolding [f379115]
    - [x] Implement the trigger parser and folder generation logic [f379115]
- [x] Task: Conductor - User Manual Verification 'Phase 1: Scaffolding and Trigger Ingestion' (Protocol in workflow.md)

## Phase 2: Core ICS Agents and Delegation [checkpoint: e0fa5b9]

- [x] Task: Set up Jinja2 prompt template loaders and core ADK agents [50a1858]
    - [x] Write unit tests verifying Jinja2 template loading, variable hydration, and ADK configuration [bf748e4]
    - [x] Implement the prompt loader utility and write templated system prompts for all 5 agents [bf748e4]
    - [x] Implement the Google ADK Agents using LlmAgent and structure the hub-and-spoke tree [50a1858]
- [x] Task: Implement SRE Mock Incident Harness and piped Agent CLI runner [1144a08]
    - [x] Write unit tests for mock incident loading and piped agent stdin parsing [1144a08]
    - [x] Create CLI runner in src/cli.py and mock incident fixtures [1144a08]
- [x] Task: Implement top-down delegation flows [88c04fd]
    - [x] Write unit tests for alert routing and delegation signal handling [88c04fd]
    - [x] Implement Benjamin's delegation router that activates the 4 leads on alert trigger [88c04fd]
- [x] Task: Conductor - User Manual Verification 'Phase 2: Core ICS Agents and Delegation' (Protocol in workflow.md)

## Phase 3: Logging and Communication Integration

- [x] Task: Integrate Scribe folder and Madhavi notifications [d7a1e09]
    - [x] Write unit tests for initial investigation folder state writing and Madhavi's channel dispatching [d7a1e09]
    - [x] Implement Scribe's initial state file creation and Madhavi's mockup notification dispatchers [d7a1e09]
- [x] Task: Conductor - User Manual Verification 'Phase 3: Logging and Communication Integration' (Protocol in workflow.md)
