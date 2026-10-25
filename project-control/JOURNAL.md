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

## 2026-10-25 — [EXECUTION REPORT] ISSUE-001 control-plane initialization — final handoff

Status: READY_FOR_REVIEW

Branch:
codex/issue-001-control-plane

Base SHA:
(no commit; repository was initialized from an empty state)

Result SHA:
82d97d92694c178c0ed906d193a97835960c34a6

What changed:
Created the independent repository scaffold, package metadata, local working
agreement, append-only project-control communication layer, ISSUE-001, and a
standard-library test covering the required layout and handoff markers. No
Bayesian algorithm, model, experiment, or accepted research state was added.

Tests:
- `python3 -m unittest discover -s tests -v` — 3 tests passed.
- `git diff --check` — passed with no whitespace errors.

Evidence:
- Initial RED run recorded missing required files before implementation.
- First semantic checkpoint is commit
  `82d97d92694c178c0ed906d193a97835960c34a6`.
- `project-control/PROJECT_STATE.md` explicitly keeps accepted
  implementation and experiment sections empty pending review.

Remaining unknowns:
No supervisor audit has occurred. The research question, Bayesian
formulation, feedback semantics, data, priors, and evaluation gates remain
undefined. Live, device, external, and business acceptance are not in scope
and have not been verified.

## 2026-10-25 — [EXECUTION REPORT] ISSUE-001 complete handoff metadata

Status: READY_FOR_REVIEW

Branch:
codex/issue-001-control-plane

Base SHA:
82d97d92694c178c0ed906d193a97835960c34a6

Result SHA:
88fd4c0845ea49e4949d03a5a7cc150e1909a033

What changed:
Confirmed the complete implementation checkpoint for ISSUE-001. The result
SHA includes the project scaffold, control-plane records, ISSUE-001, and the
test strengthened to require a READY_FOR_REVIEW handoff with the checkpoint
SHA. This journal entry is an append-only audit record and does not change
accepted project state.

Tests:
- `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-pycache python3 -m unittest discover -s tests -v` — 3 tests passed.
- `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-pycache python3 -m compileall -q src tests` — passed.
- `PYTHONPATH=src python3 -c 'import bayesian_hardle; assert bayesian_hardle.__version__ == "0.1.0"'` — passed.
- `git diff --check` — passed.
- `git status --porcelain` — clean before this append-only record.

Evidence:
The complete implementation checkpoint is
`88fd4c0845ea49e4949d03a5a7cc150e1909a033`. The accepted-state sections in
`PROJECT_STATE.md` remain empty, and no live or external acceptance is being
claimed.

Remaining unknowns:
Supervisor must independently review ISSUE-001 before any next research
stage. The research question, Bayesian formulation, feedback semantics, data,
priors, and evaluation gates remain undefined.

## 2026-10-25 — [SUPERVISOR REVIEW] ISSUE-001 control-plane initialization

Status: ACCEPTED

Independent verification:
- Read `AGENTS.md`, `project-control/README.md`, `JOURNAL.md`, `PROJECT_STATE.md`, `DECISIONS.md`, ISSUE-001, and `tests/test_project_scaffold.py` directly from the repository.
- Confirmed branch `codex/issue-001-control-plane` and HEAD `9218709a99d560c851b3015d88b789a93830c289`.
- Confirmed history: `82d97d9` initial scaffold -> `88fd4c0` complete execution handoff -> `9218709` final handoff metadata.
- Fresh rerun: `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-pycache python3 -m unittest discover -s tests -v` -> 3 passed.
- Fresh rerun: `python3 -m compileall -q src tests` -> passed.
- Fresh import check -> `bayesian_hardle.__version__ == 0.1.0`.
- `git diff --check` -> passed.
- `git fsck --full` -> passed.
- Working tree was clean before this supervisor record was written.

Assessment:
- ACCEPT the control plane, role separation, append-only journal discipline, accepted-state boundary, repository scaffold, and Git checkpoint as the canonical project governance foundation.
- ACCEPT ISSUE-001 as the infrastructure initialization issue actually executed.
- The original initialization prompt also expected Hardle mechanics to be defined before a feedback engine. That research work was not done in ISSUE-001. Rather than rewrite history or renumber the accepted issue, move Hardle mechanics to the next issue.
- No Bayesian algorithm, Hardle feedback semantics, posterior model, experiment, or research conclusion is accepted yet.

Decision:
ISSUE-001 is CLOSED / ACCEPTED. The next task is a rule-definition issue only. Do not implement the feedback engine yet.

## 2026-10-25 — [SUPERVISOR TASK] ISSUE-002 define Hardle mechanics and feedback semantics

Status: OPEN

Goal:
Establish the exact game contract required for a correct Bayesian Hardle inference engine before any feedback-engine code is written.

Required work:
1. Create `project-control/issues/ISSUE-002-hardle-mechanics.md`.
2. Determine and document, with evidence, the authoritative rules for:
   - target word length;
   - legal-guess universe versus target universe;
   - feedback symbols/states;
   - exact feedback-generation procedure;
   - repeated-letter allocation semantics;
   - win condition;
   - guess limit;
   - any Hardle-specific behavior that differs from standard Wordle.
3. Separate every rule into `VERIFIED`, `INFERRED`, or `UNKNOWN`.
4. Cite the exact source or local evidence supporting each VERIFIED rule. Do not rely on memory.
5. Where the public Hardle implementation or rules are ambiguous, build small read-only probes or inspect authoritative implementation/source material as needed. Do not implement our solver yet.
6. Produce a compact formal game contract suitable for direct translation into tests in the next issue.
7. Draft, but do not execute, the next feedback-engine issue with acceptance criteria and edge-case tests, especially duplicate-letter cases.

Required skill routing:
- Read and follow the relevant local requirement/specification skill(s) before formalizing the contract.
- Use `verification-before-completion` before claiming this issue ready for review.
- If rule evidence conflicts or an implementation behaves unexpectedly, use `systematic-debugging` principles to isolate the discrepancy rather than choosing a rule by guesswork.

Acceptance criteria:
- A reviewer can determine exactly how feedback must be generated for every guess/target pair without relying on unstated assumptions.
- Repeated-letter behavior is demonstrated with concrete examples sufficient to drive regression tests.
- Any unresolved rule that could change feedback semantics is marked BLOCKER.
- No feedback-engine implementation, Bayesian update, entropy, information gain, model training, or experiment is started.
- EXECUTOR appends one `[EXECUTION REPORT]` with branch/base/result SHA, evidence sources, verification commands, unresolved ambiguities, and a clear `READY_FOR_REVIEW` or `BLOCKED` status.

Git discipline:
Work from the accepted checkpoint. Use an isolated semantic commit/checkpoint for ISSUE-002. Do not rewrite ISSUE-001 history.
