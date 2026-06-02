# Initial Concept

Create "Project Benjamin", a production-grade, secure, agentic SRE multi-agent framework built with Python ADK and aligned with Google's Incident Management At Google (IMAG) Incident Command System (ICS) structure. The core system architecture, agent roles, and Behavior-Driven Development (BDD) specifications are defined in [doc/bdd.md](file:///home/riccardo/git/adk-sre-benjamin/doc/bdd.md).

---

# Product Vision

Project Benjamin aims to revolutionize Incident Response and Site Reliability Engineering (SRE) operations. Instead of relying on ad-hoc script execution or unstructured chat-based agent swarms, Project Benjamin brings order and safety to automated incident remediation. By fully aligning with the battle-tested Google IMAG ICS model, the framework enforces a strict top-down operational command chain where organizational, communicative, planning, and tactical duties are strictly segregated.

The framework functions as the intelligent agentic brain wrapper for existing SRE extensions and tools, executing diagnostics, maintaining a secure state timeline, assessing risk, and executing mutations safely under continuous, rule-based verification.

---

# User Personas & Roles

The system is composed of five specialized agent personas operating under a strict hierarchy:

1. **Incident Commander (Benjamin):** The central leader of the incident lifecycle. Ingests alerts/triggers (e.g. from GCP Monitoring or ServiceNow), initializes the incident context, declares it active, and delegates tasks to the leads. Visually represented as a bald man with a red Ferrari cap inside a castle (visually named **Ben Treno** - a pun on the Italian word for train and Ben Treynor Sloss/Schloss).
2. **Operations Lead (Ops Agent):** Tactical driver of diagnostics and remediation. Strictly read-only by default. Must delegate mutations to the Mutation Agent and request safety clearance from the Logistics Lead.
3. **Planning Lead (Planning Agent):** Supports the incident context by retrieving historical runbooks (Memini), scanning active GCP project structures (Discovery Agent), and maintaining a highly detailed git-versioned timeline and status log (Scribe Agent).
4. **Logistics Lead (Logistics Agent):** Gatekeeper of resources, credentials, API quotas, and system safety. Evaluates commands for their Risk Coefficient (via Risk Assessment Agent) and blocks high-risk operations without explicit approval.
5. **Communications Lead (Madhavi):** The sole public voice of the incident. Manages Telegram notifications, ServiceNow/GitHub ticket updates, and human-in-the-loop escalation flows.

---

# Core Features & Scope

1. **Top-Down IMAG ICS Delegation:** Automated triggering and coordination of multiple leads on incoming incident payloads.
2. **Investigation Folder & Scribe Logging:** Autonomous directory creation (`investigations/INC-YYYYMMDD-ID/`) containing a living state document (`state.md`) and running chronological command log (`timeline.md`), backed by automated Git commits.
3. **Runbook Retrieval & Resource Discovery:** Memory retrieval for matching incident signatures, and automated GCP resource crawling with bold red warning flags for exposed assets.
4. **Logistics Risk Gate:** Strict command parsing (handling pipes, redirects, and dangerous patterns) to assign a Risk Coefficient (LOW, MEDIUM, HIGH) and conditionally allow or block execution.
5. **Mutation Execution:** Controlled environment for execution of recovery actions (log rotation, service restarts) once safe credentials are secure and risk assessment clears.
6. **Multi-View Project Explorer:** Dynamic SPA dashboard rendering multi-cloud structures (Google Cloud, AWS, Azure, Vercel) and providing deep-linked interactive project views including a self-persisted Markdown Wiki notes editor (filtering boring GKE/Dataproc VMs by default), editable Logical dependency Graphviz DOT topologies, and auto-generated VPC physical network topology graphs compiled client-side asynchronously.
