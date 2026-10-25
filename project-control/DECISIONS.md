# Decisions

Important research and architecture decisions are append-only. A superseded
decision remains in this file and is linked to the decision that replaced it.

## 2026-10-25 — Establish the project control plane

Decision:
Use `project-control/` as the formal shared communication, audit, and
handoff surface for OWNER, SUPERVISOR, and EXECUTOR.

Reason:
The project requires direct supervisor/executor collaboration and clear
separation between executor evidence and accepted research state.

Alternatives:
Use chat messages as the handoff channel; keep state only in code comments;
allow executor reports to update accepted project state directly.

Consequences:
Every important task needs an issue, journal entry, Git checkpoint, tests,
and evidence. Research phases cannot advance automatically after executor
completion.

Status:
ACCEPTED — independently verified by SUPERVISOR on 2026-10-25.
