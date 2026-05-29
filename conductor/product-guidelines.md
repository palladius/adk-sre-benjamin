# Product Guidelines & Operational System Standards

This document establishes the user-experience, branding, writing style, and safety-critical guidelines for **Project Benjamin**. All agent modules, communication handlers, and automated outputs must strictly comply with these principles.

---

## 🎨 1. Tone, Prose, & Branding

1. **The Core Persona (Benjamin):**
   - Benjamin represents authority, expertise, and operational calm.
   - When Benjamin communicates (e.g., initializing an incident), he is respectful, brief, and structured. 
   - Emojis should be used strategically to highlight operational status (e.g., 🚨 for critical alerts, 🔧 for operations, 📢 for communications, 🛡️ for safety, 🏰 for system initialization).

2. **Incident Communication Tone (Madhavi):**
   - The Communications Lead must remain professional, factual, and strictly objective.
   - Avoid alarmist language (e.g., "The system is crashing!" or "Disaster!"). Instead, use structured states: "SLO latency violation detected", "Mitigation plan formulated", "Incident status: Active".
   - Messages to Telegram/Slack must follow a standard structure:
     - **Incident ID:** `INC-YYYYMMDD-ID`
     - **Status:** Active / Investigating / Mitigated / Resolved
     - **Current Impact:** (e.g., Latency at 450ms)
     - **Next Action:** Ops Agent is executing log queries.

3. **Documentation Style (Scribe):**
   - All written docs (`state.md`, `timeline.md`, `running_doc.md`) must be in clean, GitHub-style Markdown.
   - Every entry in `timeline.md` must be timestamped with UTC ISO 8601 format: `[YYYY-MM-DDTHH:MM:SSZ]`.
   - References to terminal commands and outputs should be neatly styled. Large log payloads must be stored in standalone text files inside the investigation folder, and linked in the timeline (e.g., `[Full logs here](logs/cmd-04-output.txt)`), rather than pasted inline to prevent token bloating.

---

## 🔒 2. Safety & Security Principles

1. **Read-Only by Default:**
   - The primary Ops Agent possesses no write/modify credentials directly. It can query APIs, list resources, read logs, and check metrics.
   - State-altering changes must be isolated to a dedicated **Mutation Agent** which is initialized with a minimal-privilege execution environment.

2. **The Logistics Gate:**
   - No command proposed by the Ops Agent can be routed to the Mutation Agent without first passing the **Logistics Lead's Risk Assessment Gate**.
   - Commands containing shell pipes (`|`), execution chains (`&&`, `;`), or redirection (`>`, `>>`) must be decomposed and analyzed for dangerous patterns (e.g., `rm -rf`, `DROP DATABASE`, credential exfiltration).

3. **Risk Coefficients:**
   - Every operational proposal must be assigned a risk category:
     - **LOW:** Safe queries, text tailing, diagnostic metrics, status checks.
     - **MEDIUM:** Rebuilding configuration, log rotations, package updates.
     - **HIGH:** Database schema updates, service restarts, destructive commands.
   - **All HIGH risk proposals require explicit human-in-the-loop approval via Madhavi's Telegram channel.**

---

## 📋 3. Human-In-The-Loop (HITL) Protocol

1. **Escalation Trigger:**
   - A HITL escalation is triggered automatically when:
     - A HIGH-risk command is proposed.
     - An automatic remediation fails to resolve the issue after two attempts.
     - Logistics Agent detects quota exhaustion or credentials mismatch.
2. **User Input Handling:**
   - When awaiting human input, the system pauses the Operations queue.
   - The Scribe Agent records: `[WAITING FOR HUMAN APPROVAL]`.
   - Madhavi presents the user with the proposed command, the risk assessment breakdown, and two clear buttons/options: "Approve" or "Reject".
