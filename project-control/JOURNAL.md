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

## 2026-10-25 — [OWNER DECISION] Reprioritize execution to component initialization

OWNER directs the project to enter execution by initializing the accepted component architecture first. The previously dispatched Hardle-mechanics task remains historically valid but is deferred until after the component scaffold is established. No Hardle rule semantics are authorized by this reprioritization.

## 2026-10-25 — [SUPERVISOR TASK] ISSUE-003 initialize Bayesian Hardle component scaffold

Status: OPEN

Executor must implement `project-control/issues/ISSUE-003-component-scaffold.md` using `docs/superpowers/plans/2026-10-25-component-scaffold.md` as the implementation plan.

Scope is architecture initialization only: create typed module boundaries, value objects, Protocol contracts, one integration-level scaffold test using test doubles, compact architecture documentation, and an execution handoff. Do not implement real Hardle feedback semantics, Bayesian calculations, information-gain calculations, Bellman recursion, ML, RL, or MCTS.

Required execution discipline:
- Work from the accepted repository checkpoint using an isolated semantic branch/worktree.
- Read and follow relevant Superpowers skills, including `using-git-worktrees`, `test-driven-development`, `executing-plans`, and `verification-before-completion`.
- Do not modify or delete the OWNER's untracked figure artifacts or unrelated files.
- Append one `[EXECUTION REPORT]` to `project-control/JOURNAL.md` and leave the result `READY_FOR_REVIEW`.

## 2026-10-25 — [EXECUTION REPORT] ISSUE-003 component scaffold

Status: READY_FOR_REVIEW (awaiting supervisor review; no supervisor
acceptance is claimed)

Branch:
codex/issue-003-component-scaffold

Base SHA:
37d48455b778d0189a0856ccdbd10099d0be3d1a

Result SHA:
9a5c0586088ccac5d37663c228b6fd4f4c06cde3 (implementation and documentation
checkpoint immediately before this append-only handoff record)

Changed files:
- `src/bayesian_hardle/__init__.py`
- `src/bayesian_hardle/game.py`
- `src/bayesian_hardle/belief.py`
- `src/bayesian_hardle/information.py`
- `src/bayesian_hardle/decision.py`
- `src/bayesian_hardle/evaluation.py`
- `tests/test_component_contracts.py`
- `README.md`
- `project-control/JOURNAL.md` (this append-only record)

Result:
Initialized the five focused component modules with typed Protocol contracts,
validated immutable value objects, placeholder policy classes, and one
integration-level scaffold test using test doubles. Documented the component
map and seven-step information flow. No real game, Bayesian, information,
planning, ML, RL, or MCTS behavior was added.

Tests and evidence:
- TDD RED: the new contract test failed on the missing `ArtifactSink` import.
- TDD RED: the handoff test failed because the Protocols lacked
  `@runtime_checkable`.
- TDD GREEN: focused component tests — 3 passed.
- `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-pycache python3 -m unittest discover -s tests -v` — 6 tests passed.
- `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-pycache python3 -m compileall -q src tests` — passed.
- `git diff --check` — passed.
- Work was isolated from the main checkout; its untracked `docs/figures/` and
  `uv.lock` were not touched.

Unresolved semantics:
Hardle word/feedback rules, repeated-letter allocation, terminal conditions,
prior and likelihood representation, posterior numeric update, entropy and
information-gain formulas, planner recursion/cache semantics, policy behavior,
benchmark protocol, and experiment acceptance gates remain unspecified or
unimplemented. These are intentionally deferred to later reviewed issues.

Evidence boundary:
This is a local scaffold and test-double verification only. No algorithm,
live, external, behavioral game, or supervisor acceptance is established.

## 2026-10-25 — [SUPERVISOR REVIEW] ISSUE-003 component scaffold — changes required

Status: CHANGES_REQUIRED

Independent architecture audit found three interface-level blockers despite green tests:

1. `BeliefState` does not explicitly represent posterior probability mass `b(w)`. Candidate membership alone cannot support non-uniform priors/posteriors, MAP, entropy, or finite-horizon value calculations. The scaffold must carry an immutable probability-mass representation without implementing normalization/update algorithms.
2. The Information Engine contracts do not explicitly represent the pair `P(o | g,b)` + posterior `b^{g,o}` for each possible feedback outcome. `EntropyCalculator` is also shaped around a partition instead of `H(b)`. Add a typed outcome value object / distribution boundary sufficient for exact expected posterior entropy and information gain, without implementing the calculations.
3. `BayesOptimalPlanner` can currently be implemented using only `(DecisionState, candidate_guesses)`, which does not enforce reuse of shared feedback/posterior semantics during hypothetical lookahead. Its contract must explicitly depend on the shared `FeedbackEngine` and `PosteriorUpdater` (and terminal rules if needed by the chosen interface), so planner implementations cannot silently duplicate those semantics.

Required correction scope:
- Interface/value-object changes and tests only.
- Preserve the five top-level architecture groups.
- No Hardle feedback semantics, posterior numeric update, entropy/IG arithmetic, Bellman recursion, policy algorithms, ML/RL/MCTS.
- Use TDD for each correction and rerun the complete verification suite.
- Append a new `[EXECUTION REPORT]` for the corrected checkpoint. Do not rewrite the previous executor report.

## 2026-10-25 — [EXECUTION REPORT] ISSUE-003 interface corrections

Status: READY_FOR_REVIEW (awaiting supervisor review; no supervisor
acceptance is claimed)

Branch:
codex/issue-003-component-scaffold

Base SHA:
257129f (supervisor changes-required review checkpoint)

Result SHA:
d81c42d (verified implementation checkpoint immediately before this
append-only report)

What changed:
- `src/bayesian_hardle/belief.py`: `BeliefState` now carries an immutable
  tuple-based `probability_mass` representation for posterior mass `b(w)`;
  no normalization or posterior update is implemented.
- `src/bayesian_hardle/information.py` and `__init__.py`: added immutable
  `OutcomeBranch` and `OutcomeDistribution` boundaries carrying an opaque
  outcome, `P(o | g,b)`, and posterior `b^{g,o}`; changed entropy to receive
  `BeliefState`, and expected-entropy/IG contracts to receive the typed
  distribution boundary.
- `src/bayesian_hardle/decision.py`: `BayesOptimalPlanner.select_guess`
  now explicitly requires the shared `FeedbackEngine` and `PosteriorUpdater`
  contracts.
- `tests/test_component_contracts.py`: added one regression test per
  supervisor correction, including RED-to-GREEN interface checks.

Tests and evidence:
- TDD RED 1: probability-mass test failed because `BeliefState` lacked the
  `probability_mass` constructor field; GREEN passed.
- TDD RED 2: outcome-distribution test failed because `OutcomeBranch` and
  `OutcomeDistribution` were not importable; GREEN passed.
- TDD RED 3: planner-signature test failed because the planner accepted only
  `state` and `candidate_guesses`; GREEN passed after adding both shared
  semantics dependencies.
- `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-pycache python3 -m unittest discover -s tests -v` — 9 tests passed.
- `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-pycache python3 -m compileall -q src tests` — passed.
- `PYTHONPATH=src PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-pycache python3 -c 'import bayesian_hardle; assert bayesian_hardle.__version__ == "0.1.0"; from bayesian_hardle import OutcomeBranch, OutcomeDistribution; print("import-check: ok")'` — passed.
- `git diff --check` — passed before the implementation checkpoint.

Scope boundary:
The five top-level architecture groups are preserved. No Hardle semantics,
numeric posterior update, normalization, entropy/IG arithmetic, Bellman
recursion, policy algorithm, ML, RL, or MCTS was added. Evidence is limited
to local interface tests and static checks; no live, external, behavioral
game, or supervisor acceptance is established.

Remaining unknowns:
Hardle word/feedback rules, repeated-letter allocation, terminal conditions,
posterior update and normalization algorithms, entropy and information-gain
formulas, planner recursion/cache semantics, policy behavior, benchmark
protocol, and experiment acceptance gates remain unspecified or
unimplemented for later reviewed issues.
