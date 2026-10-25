# Journal

Append-only shared event bus. Historical entries must not be rewritten or
deleted. New records are appended below the existing records.

## 2026-10-25 — [OWNER DECISION] INITIALIZE-001

Status: DIRECTIVE

Decision:
Create an independent `bayesian-hardle/` project with a formal shared
control plane before beginning algorithm or experiment work.

Scope:
Establish the repository structure, Git checkpoint discipline, issue format,
append-only journal, accepted-state boundary, and role separation between
OWNER, SUPERVISOR, and EXECUTOR.

Constraint:
This decision authorizes project initialization only. It does not accept any
implementation, Bayesian formulation, experiment, or research conclusion.

## 2026-10-25 — [EXECUTION REPORT] ISSUE-001 control-plane initialization

Status: IN_PROGRESS

Branch:
codex/issue-001-control-plane

Base SHA:
(no commit; repository was initialized from an empty state)

Result SHA:
pending first checkpoint

What changed:
The project scaffold and control-plane documents are being created from the
OWNER initialization directive. This record remains a provisional handoff;
the final executor report will be appended after the first checkpoint.

Tests:
The scaffold test was written first and run in the expected RED state because
the required files did not yet exist.

Evidence:
See the failing `python3 -m unittest discover -s tests -v` output in the
executor session; it reported missing required files and control-plane
documents.

Remaining unknowns:
No supervisor audit has occurred. No implementation or experiment is
accepted. The first checkpoint SHA is pending.
