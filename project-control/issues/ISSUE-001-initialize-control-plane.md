# ISSUE-001 — Initialize the project control plane

## Research question

Can the Bayesian Hardle project begin with a shared, auditable control plane
that preserves role boundaries and prevents unreviewed work from becoming
accepted research state?

## User-facing meaning

OWNER, SUPERVISOR, and EXECUTOR can continue work through repository files
without requiring OWNER to relay messages. A reviewer can identify what was
requested, what changed, which tests ran, and what remains unverified.

## Engineering goal

Create an independent Git repository with the requested layout, formal
control-plane documents, one initial issue, and a minimal test proving the
scaffold and handoff markers exist.

## Scope

- Initialize `bayesian-hardle/` as a separate Git repository.
- Add `AGENTS.md`, `README.md`, `pyproject.toml`, `.gitignore`, package,
  tests, and the requested research directories.
- Add `project-control/README.md`, `JOURNAL.md`, `PROJECT_STATE.md`,
  `DECISIONS.md`, and this issue.
- Record the initialization directive and executor evidence in the journal.

## Non-goals

- Implementing a feedback engine, posterior update, model, or solver.
- Choosing a Bayesian formulation, prior, dataset, or evaluation metric.
- Claiming device, live, business, or supervisor acceptance.

## Acceptance criteria

- The repository is independent and has a semantic initial checkpoint.
- Required directories and files exist and are tracked.
- The control-plane README contains all formal role and evidence rules.
- `JOURNAL.md` is append-only in usage and contains an executor handoff with
  branch, base SHA, result SHA, tests, evidence, and unknowns.
- `PROJECT_STATE.md` contains no unreviewed accepted implementation or
  experiment.
- The standard-library test suite passes.

## Tests

```bash
python3 -m unittest discover -s tests -v
git status --short --branch
git ls-files
```

## Risks / unknowns

- The research target and Bayesian formulation are not yet specified.
- No supervisor has independently reviewed this initialization.
- The initial package contains no algorithmic behavior.

## Verification evidence

To be appended to `JOURNAL.md` after the first semantic checkpoint and fresh
verification.

## Final status

READY_FOR_REVIEW — executor work only; pending `[SUPERVISOR REVIEW]`.
