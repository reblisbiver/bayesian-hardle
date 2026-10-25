# Project control

`project-control/` is the shared supervision and handoff layer for Bayesian
Hardle. It is the formal communication channel between the OWNER,
SUPERVISOR, and EXECUTOR; the OWNER must not be used as a message relay.

## Role boundaries

1. OWNER is responsible for research and product decisions.
2. EXECUTOR is responsible for implementation, investigation, experiments,
   and evidence collection.
3. SUPERVISOR is responsible for independent audit, acceptance or rejection,
   and dispatching the next task.
4. An OWNER message is not execution evidence.
5. An EXECUTOR report is evidence awaiting audit, not acceptance.
6. SUPERVISOR must independently verify important conclusions.
7. SUPERVISOR and EXECUTOR read and write this directory directly; neither
   should require OWNER message forwarding.
8. `JOURNAL.md` is append-only. Do not rewrite or delete history.
9. Every important task records its Git branch, base SHA, result SHA, tests,
   and evidence.
10. Work must not automatically enter the next research stage before a
    `[SUPERVISOR REVIEW]` accepts it.

## Formal record types

Use these exact headings in the journal:

- `[SUPERVISOR TASK]` — scope and acceptance criteria assigned for execution.
- `[EXECUTION REPORT]` — executor changes, tests, evidence, and unknowns;
  always marked as awaiting review until accepted.
- `[SUPERVISOR REVIEW]` — independent audit, decision, and next task.
- `[OWNER DECISION]` — research/product direction supplied by OWNER.

## State files

- `JOURNAL.md` is the append-only event bus.
- `PROJECT_STATE.md` contains only the current accepted state. Executor work
  must not be written into accepted sections before supervisor review.
- `DECISIONS.md` records important research and architecture decisions. Old
  decisions remain and are marked superseded rather than deleted.
- `issues/` contains one independently verifiable issue per research or
  engineering problem.

## Handoff minimum

An executor handoff must identify the issue, branch, base SHA, result SHA,
changed files, test commands and outcomes, evidence paths, remaining
unknowns, and whether any external/live acceptance remains unverified.
