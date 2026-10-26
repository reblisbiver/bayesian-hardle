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

## 2026-10-25 — [SUPERVISOR REVIEW] ISSUE-003 component scaffold — accepted

Status: ACCEPTED

SUPERVISOR independently re-read the corrected component interfaces and tests and reran the verification suite. The three previous blockers are resolved:
- `BeliefState` explicitly carries immutable posterior probability mass `b(w)`.
- Information contracts explicitly carry per-feedback outcome probability plus resulting posterior, and entropy is defined over a belief state.
- `BayesOptimalPlanner` explicitly consumes the shared `FeedbackEngine` and `PosteriorUpdater` boundaries for hypothetical lookahead.

Independent verification evidence:
- full unittest suite: 9 tests passed;
- compileall: passed;
- package/import contract check: passed;
- `git diff --check` on the correction and full ISSUE-003 range: passed;
- scope scan found no numeric entropy/IG, Bellman, MCTS, ML, or policy algorithm implementation;
- worktree status was clean at corrected executor checkpoint `60d3c73`.

Acceptance boundary:
This accepts only the architecture/component scaffold and interface handoff. It does not accept or define Hardle feedback semantics, repeated-letter rules, posterior update algorithms, entropy/IG arithmetic, Bellman recursion, policy behavior, or experiment results.

Next milestone:
Return to the deferred Hardle-mechanics specification issue before implementing the Feedback Engine.

## 2026-10-25 — [OWNER DECISION] Enter engineering execution

Status: DIRECTIVE

OWNER confirms that previously settled Bayesian Hardle theory should no longer be reopened as discussion by default. SUPERVISOR should independently execute implementation and experiments, escalating only decisions that change the hypothesis space, objective, experimental comparison, or research conclusion.

## 2026-10-25 — [SUPERVISOR TASK] ISSUE-004 exact Bayesian core and first experiment

Status: OPEN

Executor must implement `project-control/issues/ISSUE-004-exact-bayesian-core-and-first-experiment.md` from the accepted component scaffold.

The settled path is: exact Hardle feedback semantics → exact Bayesian prior/posterior → entropy/information gain → Random/MAP/Max-IG baselines → exact finite-horizon Bayes-optimal planning on a tractable small vocabulary → first controlled experiment.

Do not reopen settled theory unless implementation evidence exposes a contradiction that would change the research definition. Do not use the leaked Hardle scheduled-answer set as solver knowledge. Use TDD, isolated worktree/branch execution, and verification-before-completion. Return READY_FOR_REVIEW with reproducible experiment artifacts and evidence; do not claim supervisor acceptance.

## 2026-10-25 — [EXECUTION REPORT] ISSUE-004 exact Bayesian core and first experiment

Status: READY_FOR_REVIEW (executor evidence only; supervisor acceptance is not claimed)

Branch:
`codex/issue-004-exact-bayesian-core`

Base SHA:
`e9fd532be913d287745c0d80721a0297f226a0a5`

Result SHA:
`14c462d` (`Implement exact Bayesian Hardle core and first experiment`)

What changed:
- Implemented duplicate-aware Hardle feedback as `(exact-position,
  present-but-wrong-position)` using exact-first residual multiplicity
  matching, plus win/guess-limit terminal rules.
- Vendored the supervisor-specified asweigart legal-guess source (12,972
  base words), added exactly `covid` and `padel` to produce 12,974 legal
  guesses, and vendored the specified 2,315-word original answer list.
  Provenance and SHA256 values are in `data/wordlists/provenance.json`.
- Implemented uniform prior, immutable normalized deterministic posterior
  filtering, explicit zero-mass observation rejection, exact outcome
  partitions, Shannon entropy, expected posterior entropy, and information
  gain.
- Implemented seeded Random, MAP, Max-IG, and exact finite-horizon
  Bayes-optimal planning with canonical belief/horizon memoization. The
  planner reuses the shared FeedbackEngine and PosteriorUpdater contracts.
- Implemented leakage-safe episode evaluation and machine-readable results.
  The current Hardle scheduled-answer membership is not vendored and is not
  solver knowledge.

Verification:
- `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-pycache python3 -m unittest discover -s tests -v` — 29 tests passed.
- `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-pycache python3 -m compileall -q src tests experiments scripts` — passed.
- Package wildcard import check — passed.
- `git diff --check` — passed before commit.
- Vendored-input/provenance validation — base 12,972, legal 12,974,
  candidates 2,315, source hashes matched, and `covid`/`padel` absent from
  candidate answers.

Experiment command:
`PYTHONPATH=src PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-pycache python3 experiments/issue_004_first_experiment.py`

Experiment evidence:
- Full scope: 12,974 legal guesses, 2,315 candidate answers, 10 guesses.
  Random completed 2,315/2,315 episodes with solve rate 2/2,315 =
  0.000864 and mean guesses 9.998272. MAP completed 2,315/2,315 with
  solve rate 1.000000 and mean guesses 5.360259.
- Full Max-IG was attempted on the same full legal scope, not a reduced
  vocabulary. With the declared 30-second budget it completed 0/2,315
  episodes, evaluated 6,282 guesses, and stopped at 30.001 seconds. This is
  the measured scaling limit, not a completed full Max-IG comparison.
- Small scope: five candidate answers, ten legal guesses including the two
  Hardle additions, three guesses, five requested episodes. Random solved
  1/5 (0.2) with mean 2.6 guesses; MAP solved 5/5 with mean 2.2; Max-IG
  solved 0/5 with mean 3.0; exact Bayes-optimal solved 5/5 with mean 3.0.
  The planner recorded 192 cache hits and 29 misses.
- Machine-readable output is
  `experiments/results/issue_004_first_experiment.json`; the human summary
  is `experiments/results/issue_004_first_experiment_summary.md`.

Scope and acceptance boundary:
- `PROJECT_STATE.md` was not modified. This report leaves the repository at
  `READY_FOR_REVIEW`; no research milestone or experiment is accepted here.
- Evidence is limited to local behavior tests, compile/import checks, and
  executor-local reproducible experiments. No live, external, or supervisor
  acceptance is claimed.
- Full exact Bayes-optimal planning remains intentionally restricted to the
  declared small vocabulary. Full Max-IG remains incomplete at the measured
  budget and must not be described as a full comparison result.

## 2026-10-25 — [EXECUTION REPORT] ISSUE-004 provenance and shared-updater audit correction

Status: READY_FOR_REVIEW (follow-up executor evidence; supervisor acceptance is not claimed)

Branch:
`codex/issue-004-exact-bayesian-core`

Base SHA:
`14c462d` (prior ISSUE-004 implementation checkpoint)

Result SHA:
`b90f8b8` (follow-up implementation/artifact checkpoint immediately before
this append-only record)

What changed:
- Pinned the legal-guess source to the immutable `asweigart/wordletools`
  revision `b03237c95a2b909226ef4d9ed195d41acf40490f` and the answer source to
  the immutable Gist raw revision `50838083dca5359b3cacf1ab677059b40c0e025e`.
- Added SHA256 checks to `scripts/fetch_wordlists.py` and a regression test for
  immutable provenance URLs. The cached input remains 12,972 base words plus
  the two declared Hardle legal additions (`covid`, `padel`) = 12,974 legal
  guesses, with 2,315 candidate answers.
- Wired the full and small Max-IG experiment runs through one shared
  `ExactOutcomePartitioner(updater)`, making PosteriorUpdater reuse explicit.
- Regenerated the machine-readable and Markdown experiment artifacts after
  this wiring change and added the implementation plan under
  `docs/superpowers/plans/`.

Fresh verification:
- `PYTHONPATH=src PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-pycache python3 -m unittest discover -s tests -v` — 30 tests passed.
- `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-pycache python3 -m compileall -q src tests experiments scripts` — passed.
- Package wildcard import/version check — passed.
- Vendored-input count, subset, SHA256, and pinned-URL audit — passed.
- `git diff --check` — passed.
- Fresh experiment command — completed with full Random/MAP and small Random/MAP/Max-IG/exact-planner results; full Max-IG used the complete legal scope and stopped at the declared 30-second budget after 591 guess evaluations.

Current experiment evidence:
- Full Random: 2/2,315 solved (solve rate 0.000864), mean guesses 9.998272.
- Full MAP: 2,315/2,315 solved (solve rate 1.000000), mean guesses 5.360259.
- Full Max-IG: 0/2,315 completed before the 30-second budget; this is a
  scaling measurement, not a completed full-vocabulary comparison.
- Small scope: Random 1/5, MAP 5/5, Max-IG 0/5, exact Bayes-optimal 5/5;
  the planner recorded 192 cache hits and 29 misses.

Evidence boundary and remaining unknowns:
`PROJECT_STATE.md` was not modified. The implementation, tests, and
experiments remain executor-local evidence pending independent supervisor
review. Full exact Bayes-optimal planning is intentionally limited to the
declared small vocabulary, and full Max-IG remains incomplete at the measured
budget. No scheduled-answer membership was vendored or supplied to the
solver.

## 2026-10-25 — [SUPERVISOR REVIEW] ISSUE-004 exact Bayesian core and first experiment — changes required

Status: CHANGES_REQUIRED

Independent supervisor review did not accept the executor experiment as a valid ISSUE-004 result, despite the full automated suite passing.

Accepted implementation evidence:
- Hardle feedback uses exact-position plus duplicate-aware residual multiplicity matching.
- Uniform prior and deterministic posterior filtering/renormalization are consistent with the settled Bayesian contract.
- Outcome partitions, Shannon entropy, expected posterior entropy, and information gain satisfy the required identities in the reviewed tests.
- Solver candidate-answer vocabulary remains separate from legal guesses, and the leaked Hardle scheduled-answer membership is not solver knowledge.
- Exact finite-horizon planner reuses the shared FeedbackEngine and PosteriorUpdater boundaries.

Blocking findings:
1. Max-IG tie handling is behaviorally incorrect for the baseline experiment. Once the posterior collapses to a single answer, all legal guesses have IG = 0, and the current implementation chooses an arbitrary tied legal guess rather than the known answer. Independent traces reproduce this on all five small-scope targets: after one informative guess the posterior becomes singleton, yet Max-IG repeatedly guesses `adieu` and finishes 0/5. This makes the reported small-scope Max-IG result invalid as a meaningful baseline comparison. Required correction: remain a pure maximum-information-gain policy, but define a solve-aware tie-break among equal-IG actions so a known answer is guessed rather than an arbitrary non-answer.
2. Exact Bayes-optimal action selection optimizes final solve probability only and leaves equal-value actions ordered arbitrarily. Under the settled evaluation contract, solve probability is primary and mean guesses is secondary. Independent traces show the planner deliberately spends an extra guess after the answer is already uniquely identified, then solves on the final allowed move. Its reported 5/5 solve rate is compatible with the primary Bellman objective, but the 3.0 mean-guesses result is an artifact of unresolved tie-breaking rather than a meaningful secondary metric. Required correction: preserve final solve probability as the primary value; among actions with equal final solve probability, prefer the action/policy with lower expected guesses to solution (or an equivalent lexicographic secondary criterion).

Scaling observation, not a correctness blocker:
- Full Max-IG did use the full 12,974-guess / 2,315-answer scope, but the current exact implementation exhausted the declared 30-second budget before completing even the first episode. This is valid evidence of a naive-scaling limit, not a completed baseline result. It must remain labeled incomplete until a computationally practical exact implementation is available or the experimental scope is explicitly revised by the owner.

Fresh supervisor verification evidence:
- `PYTHONPATH=src PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-pycache python3 -m unittest discover -s tests -v` — 30/30 tests passed.
- `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-pycache python3 -m compileall -q src tests experiments scripts` — passed.
- `git diff --check e9fd532..953db2e` — passed.
- Independent small-scope policy traces reproduced Max-IG singleton-belief misbehavior for all five targets and Bayes-optimal extra-step behavior after answer identification.

Acceptance boundary:
- ISSUE-004 is not accepted in its current form.
- The Bayesian inference/information core is not being rejected; required changes are confined to policy tie resolution and regeneration of affected experiment artifacts/tests.
- `PROJECT_STATE.md` remains unchanged.
- No follow-up executor task is dispatched by this review.

## 2026-10-25 — [EXECUTION REPORT] ISSUE-004 policy tie-handling correction round

Status: READY_FOR_REVIEW (executor evidence only; supervisor acceptance is not claimed)

Branch:
`codex/issue-004-exact-bayesian-core`

Base SHA:
`6e9b0624e896d6f74cab0a5de200c8e8264616c4`

Result SHA:
`8c3d83e47f6e8ee09af364537a8e11a8aa187d3c`

What changed:
- Max-IG still maximizes exact information gain first. The documented absolute
  policy tie tolerance is `POLICY_TIE_TOLERANCE = 1e-12`. Within that IG tie,
  it selects the remaining legal candidate answer with greatest posterior
  probability; exact remaining ties preserve the supplied legal-guess order.
- Exact Bayes-optimal planning now evaluates each action with the pair
  `(final solve probability, expected guesses until solve or horizon
  termination)`. The first component is maximized first; the second is used
  only when the first ties within the same tolerance. This is not a MAP
  replacement and does not trade away solve probability.
- Added acceptance/regression coverage for singleton Max-IG, controlled
  equal-IG candidate-vs-non-answer ties, deterministic non-answer fallback,
  equal-success planner ties, planner singleton behavior, and existing
  planner success-probability cases.
- Regenerated the existing machine-readable and human-readable experiment
  artifacts. `PROJECT_STATE.md` was not modified.

Fresh verification:
- TDD red phase: the three new defect tests failed on the untouched base
  (Max-IG candidate tie, Max-IG singleton, planner equal-success tie).
- TDD green phase: targeted decision suite — 10 tests passed.
- `PYTHONPATH=src PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-pycache python3 -m unittest discover -s tests -v` — 35 tests passed.
- `PYTHONPATH=src PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-pycache python3 -m compileall -q src tests experiments scripts` — passed.
- Package import/version and exported tolerance check — passed (`0.1.0`, `1e-12`).
- `git diff --check` — passed; the implementation/artifact checkpoint was clean before this append-only report.

Fresh experiment configuration:
- Seed `20261025`; word length 5; horizon 10; uniform prior; 12,974 legal
  guesses and 2,315 candidate answers; no scheduled Hardle answer membership
  was supplied to the solver.
- Small scope: five candidate answers, ten legal guesses after the declared
  Hardle legal additions, horizon 3, five requested target episodes.
- Full Max-IG retained the existing 30-second bounded scaling attempt; no
  optimization or reduced full scope was introduced.

Fresh experiment results:

| Scope | Policy | Completed / requested | Solve rate | Mean guesses | Runtime (s) | Stop/evidence |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| full | Random | 2315 / 2315 | 0.000864 | 9.998272 | 11.570 | completed |
| full | MAP | 2315 / 2315 | 1.000000 | 5.360259 | 13.974 | completed |
| full | Max-IG | 0 / 2315 | 0.000000 | 0.000000 | 30.039 | bounded after 603 evaluations; scaling measurement only |
| small | Random | 5 / 5 | 0.200000 | 2.600000 | 0.000120 | completed |
| small | MAP | 5 / 5 | 1.000000 | 2.200000 | 0.000093 | completed |
| small | Max-IG | 5 / 5 | 1.000000 | 2.000000 | 0.003161 | completed |
| small | Exact-Bayes-optimal | 5 / 5 | 1.000000 | 2.000000 | 0.003292 | completed |

Plain-language small-scope traces (targets in order `awake`, `cigar`,
`humph`, `rebut`, `sissy`):
- Random: `padel,padel,cigar`; `cigar`; `stare,rebut,arise`;
  `padel,humph,awake`; `awake,adieu,humph`. Only `cigar` solved within the
  three-guess horizon.
- MAP: `awake`; `awake,cigar`; `awake,humph`; `awake,cigar,rebut`;
  `awake,humph,sissy`. All five solved.
- Max-IG: every target first used `arise`, which reduced the posterior from
  five candidates to one, then guessed that sole answer immediately. The
  feedback was `(2,0)`, `(0,3)`, `(0,0)`, `(0,2)`, and `(1,1)` respectively;
  all five solved in two guesses.
- Exact-Bayes-optimal followed the same two-step traces on this controlled
  scope: `arise`, then the now-unique answer for each target. Its equal-value
  alternatives no longer spend the final extra guess.

Artifacts:
- `experiments/results/issue_004_first_experiment.json`
- `experiments/results/issue_004_first_experiment_summary.md`

Evidence boundary and remaining scope:
These are fresh executor-local tests and experiments, not live, physical,
business, or supervisor acceptance. The full Max-IG result remains incomplete
by design and is reported only as a scaling limit. No Bayesian theory,
hypothesis space, objective, vocabulary separation, or scheduled-answer
knowledge boundary was changed.

## 2026-10-25 — [SUPERVISOR REVIEW] ISSUE-004 exact Bayesian core and first experiment — accepted

Status: ACCEPTED

Independent supervisor verification after the correction round confirmed the two previously blocking policy-selection defects are fixed without changing the settled Bayesian research definition.

Accepted evidence:
- Fresh full test suite: 35/35 passed.
- Fresh compile/import and full-range `git diff --check`: passed.
- Worktree clean at executor handoff checkpoint `9568d1b` before supervisor state update.
- Independent supervisor traces reproduced the corrected small-scope behavior for all five targets: Max-IG and exact Bayes-optimal both select `arise` first, reduce the posterior from five candidates to one, then immediately guess the known answer on the second move.
- Max-IG still chooses a non-answer legal guess when its information gain is strictly higher; the correction affects only ties.
- Exact Bayes-optimal still maximizes final solve probability first; expected guesses is used only as a lexicographic secondary criterion among equal-success actions.
- Scheduled Hardle answer membership remains excluded from solver knowledge.

Accepted experiment evidence:
- Full Random: solve rate `0.000864`, mean guesses `9.998272` over 2,315 targets.
- Full MAP: solve rate `1.000000`, mean guesses `5.360259` over 2,315 targets.
- Full Max-IG: incomplete within the declared 30-second budget after 603 candidate-guess evaluations; accepted only as a scaling-limit observation, not as a completed full baseline.
- Small scope: Random `1/5`, MAP `5/5` mean `2.2`, Max-IG `5/5` mean `2.0`, exact Bayes-optimal `5/5` mean `2.0`.

Acceptance boundary:
- ISSUE-004 exact Bayesian core and first controlled experiment are accepted.
- Full-vocabulary Max-IG performance remains unresolved because the current exact implementation is computationally too slow.
- Full-vocabulary exact Bayes-optimal planning remains intentionally unevaluated.
- Next milestone is engineering/scaling of exact Max-IG without changing its mathematical definition.

Infrastructure note:
- The durable bridge successfully produced the user-visible `PM_JOB_STATUS ... completed` callback and Codex exited with code 0, but the durable job JSON was observed afterward with `status: interrupted`. This is a bridge bookkeeping inconsistency, not a research-result failure, and should be corrected separately from the Hardle solver.

## 2026-10-25 — [EXECUTION REPORT] ISSUE-005 exact Max-IG performance engineering

Status: READY_FOR_REVIEW (executor evidence only; supervisor acceptance is not claimed)

Issue: `ISSUE-005`
Branch: `codex/issue-005-maxig-speed`
Base SHA: `70dff41174f2f08169eeeb2b4eccaeab4ea1284b`
Implementation commit: `45d95688ef3c0d877749f16277ac6589951870fd` (short SHA: `45d9568`)

What changed:
- Added `ExactFeedbackCodeMatrix`, a read-only exact `uint8` matrix encoded as `exact * 6 + misplaced`, built with vectorized exact-position and duplicate-aware multiset overlap operations. It uses no Wordle 243-color semantics.
- Added direct weighted outcome-mass entropy scoring for deterministic exact IG, including a vectorized small-belief batch path and an exact singleton zero-IG tie shortcut. Scalar `HardleFeedbackEngine`, `ExactOutcomePartitioner`, and `ExactInformationGainCalculator` remain available as the reference path; `use_acceleration=False` forces it.
- Added deterministic Max-IG decision caching keyed by normalized posterior mass, remaining horizon, and legal-guess order. Posterior filtering still uses the canonical updater and no hidden scheduled-answer membership is supplied.
- Declared NumPy as a project dependency and added ISSUE-005 plan, issue record, benchmark entrypoint/config, machine-readable result, summary, and behavior tests.

Fresh correctness evidence:
- `PYTHONPATH=src python3 -m unittest discover -s tests -v` — 44/44 passed.
- Matrix feedback matched `HardleFeedbackEngine` on adversarial duplicate-letter cases and a deterministic randomized sample of 10,000 full-vocabulary guess-answer pairs.
- Fast weighted IG matched the scalar reference within `1e-12` for uniform, non-uniform, repeated-letter, and random subset beliefs; fast/reference policy choices matched on controlled and random weighted states, including tie/cache checks.
- `python3 -m compileall -q src tests experiments scripts`, package import/export check, JSON artifact assertions, and `git diff --check` — passed.
- `PROJECT_STATE.md` was unchanged.

Fresh performance evidence on this machine:
- Full matrix: 12,974 legal guesses x 2,315 candidate answers; `30,034,810` bytes (`28.643 MiB`).
- Cold first move including matrix construction: `0.610672s`; all `12,974` guesses evaluated; selected opener `stare`.
- Warm first move with the matrix already built: mean `0.118602s` across three full-row scans (minimum `0.117829s`); all `12,974` guesses evaluated; opener `stare` each time. Both gates pass: cold `<=2.0s`, warm `<=0.5s`.
- Full existing-scope Max-IG experiment: `2,315/2,315` episodes, solve rate `1.000000`, mean guesses `4.586177`, runtime `18.410387s`, `8,978,008` evaluated guesses, decision cache `8,112` hits / `2,505` misses, completed without the 30s budget.
- Accepted ISSUE-004 reference: `30.039s`, `603` evaluations, `0` completed episodes. Fresh full-run wall-clock speedup: `1.632x`.

Evidence paths:
- `experiments/results/issue_005_maxig_speed.json`
- `experiments/results/issue_005_maxig_speed_summary.md`
- `docs/superpowers/plans/2026-10-25-issue-005-maxig-speed.md`

Remaining boundary:
- Results are executor-local and machine-specific, pending independent supervisor review. No research definition, objective, hypothesis space, feedback semantics, or live/business acceptance claim was changed.

## 2026-10-25 — [SUPERVISOR REVIEW] ISSUE-005 exact Max-IG performance — accepted

Status: ACCEPTED

Independent post-merge verification passed 44/44 tests. The exact accelerated path preserves the accepted feedback and Max-IG semantics while replacing repeated Python-level guess×answer evaluation with an exact uint8 feedback matrix, vectorized outcome scoring, and deterministic state caching. Fresh evidence: cold full first move ~0.61s, warm full first move ~0.12s, and the 2,315-target exact Max-IG benchmark completed 2,315/2,315 with solve rate 1.0, mean guesses 4.586177, runtime ~18.41s.

## 2026-10-25 — [OWNER DECISION] Fair full-support benchmark and interactive acceptance

Status: DIRECTIVE

The OWNER rejects the curated 2,315-answer subset as the primary fairness assumption for human-comparison claims because a real player is not assumed to know that hidden subset. Primary fair hypothesis support must therefore cover all 12,974 current legal Hardle words. Keep the 2,315 mode only as a diagnostic/answer-list-aware comparison. Build both full-uniform and broad general-English-frequency non-leaking prior modes, with non-zero support for every legal word. Also provide a local interactive acceptance client so the OWNER can enter a target word or manually feed live Hardle feedback and inspect step-by-step guesses, remaining candidates, probabilities/information, and compute time under selectable policies.

## 2026-10-25 — [EXECUTION REPORT] ISSUE-006 fair full-support solver and interactive acceptance client

Status: READY_FOR_REVIEW (executor evidence only; supervisor acceptance is not claimed)

Issue: `ISSUE-006`
Branch: `codex/issue-006-fair-client`
Base SHA: `d5b02dd057739fc54bc4ad31f0f01aff606aff6a`
Implementation commit: `28ae9a86465162352f58fcd7032eb2fe691df088`

What changed:
- Added explicit `full-uniform`, `full-frequency`, and `curated-2315` mode contracts. The first two use only the complete 12,974-word legal vocabulary; the curated mode is visibly diagnostic / answer-list-aware.
- Added `GeneralEnglishFrequencyPrior` using required `wordfreq==3.1.1`, English Zipf frequency, `max(10 ** zipf, 1e-12)`, and normalization. Every legal word retains positive mass; provenance records the source, version, transformation, floor, and `answer_membership_used: false`.
- Extended the exact duplicate-aware Hardle `uint8` feedback matrix to a vocabulary-identity keyed on-disk `.npy` memmap cache. Added exact matrix-backed posterior filtering without changing scalar reference semantics.
- Added installed `bayesian-hardle` and `python -m bayesian_hardle.cli` entrypoints with simulated-target, live-assist, and independent compare modes. Live input rejects malformed and posterior-impossible feedback without mutating the belief state.
- Added TDD coverage, README acceptance commands, sample transcript, benchmark runner/config, machine-readable benchmark JSON, and Markdown summary.

Fresh correctness evidence:
- `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue006-venv-pycache PYTHONPATH=src /tmp/bayesian-hardle-issue006-venv/bin/python -m unittest discover -s tests -v` — 55/55 passed.
- Full-support matrix shape `12,974 x 12,974`, dtype `uint8`; matrix codes matched `HardleFeedbackEngine` on duplicate-letter cases and 10,000 deterministic full-support random pairs.
- Matrix-backed posterior filtering matched the scalar updater on weighted repeated-letter cases and retained legal `aahed` outside curated support under full-support filtering.
- Fast weighted IG matched the scalar exact reference within `1e-12` on uniform/non-uniform controlled beliefs; existing ISSUE-001..005 behavior remained green.
- Fair-mode boundary test proves `full-uniform` and `full-frequency` do not call/read curated answer membership; only `curated-2315` does.
- Actual `wordfreq==3.1.1` venv run solved the legal-but-curated-external `aahed` target in `full-frequency`; installed console-script smoke test and module CLI smoke tests passed.
- `compileall`, package import/export, `git diff --check`, and final worktree status checks passed. `PROJECT_STATE.md` was unchanged.

Fresh performance evidence on this Mac:
- Full-support matrix cold construction: `2.963543s`; warm disk load: `0.007340s`.
- Matrix data memory: `168,324,676` bytes; `.npy` disk footprint: `168,324,804` bytes. Peak RSS delta during the cold build was `408,125,440` bytes.
- Warm first-move exact Max-IG: full-uniform mean `549.221ms`; full-frequency mean `550.246ms`, three repeats each.
- Representative interactive latency covered `aahed`, `padel`, `cigar`, and `civic` under both fair modes; `4/8` rows were outside curated support and all `8/8` solved within the ten-turn default horizon.
- Broad benchmark is explicitly non-exhaustive: deterministic seeded six-target sample, 24 independent mode/policy runs. Primary fair results are in the machine-readable artifact, not substituted with the 2,315-target diagnostic set.

Evidence paths:
- `experiments/results/issue_006_fair_client.json`
- `experiments/results/issue_006_fair_client_summary.md`
- `docs/acceptance/issue_006_sample_transcript.md`
- `docs/superpowers/plans/2026-10-25-issue-006-fair-client.md`

Known boundary:
- The package declares `wordfreq==3.1.1`; OWNER setup should run `python3 -m pip install .` before using `full-frequency`. The old system pip in this Mac rejected editable PEP 517 installation, so evidence used the standard wheel install in a dedicated temporary venv. This is an installation-tool limitation, not a solver fallback.
- Full-support exact Bayes-optimal planning remains out of scope. No scheduled Hardle answer list is supplied to fair-mode inference. Executor evidence remains pending independent SUPERVISOR review.

## 2026-10-25 — [EXECUTION REPORT] ISSUE-007 interactive browser GUI for acceptance

Status: READY_FOR_REVIEW (executor evidence only; supervisor acceptance is not claimed)

Issue: `ISSUE-007`
Branch: `codex/issue-007-interactive-gui`
Base SHA: `41873fb024f1731b791aafc0f3c8d7ee277f1610` (ISSUE-006 executor branch)
Implementation commits:
- `f924750` — design and implementation plan
- `62c2a4c` — reusable solver and battle sessions
- `a8b43f9` — Streamlit acceptance GUI
- `9faef4b` — battle target-support regression test

What changed:
- Added `bayesian_hardle.application` as the shared application/session layer.
  `SolverSession` and `run_simulation` preserve the ISSUE-006 exact solver;
  `BattleSession` advances one human turn plus one hidden solver turn and
  returns a redacted `BattlePublicState` until human solve, horizon, or give-up.
- Refactored the CLI to use the shared application services while preserving
  `simulate`, `live`, and `compare` behavior and adding cumulative per-turn
  timing to the existing transcript shape.
- Added `streamlit_app.py` with Strategy comparison and Human vs Solver tabs,
  support/prior explanations, readable per-turn tables, progress indication,
  explicit diagnostic labeling for curated-2315, and no exact Bayes-optimal
  option outside its tractability scope.
- Added Streamlit to the project dependencies and documented the exact uv
  launch command. The GUI stores the battle service object in Streamlit state
  but renders solver details only from a finished public view.
- Added session-layer, anti-leak, target-validation, support-sampling, and
  Streamlit smoke/AppTest coverage.

Fresh verification evidence:
- `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue007-pycache python3 -m unittest discover -s tests -v` — `66` tests passed, `2` Streamlit-only tests skipped because the default Python lacks the optional GUI dependency.
- `uv run --with . python -m unittest discover -s tests -v` — `66/66` passed, including Streamlit import and initial-page AppTest.
- `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue007-pycache python3 -m compileall -q src tests experiments`, `git diff --check`, and package/module imports — passed.
- Known-target `aahed` under real full-uniform support `12,974`: MAP solved in `1` turn; exact Max-IG solved in `7` turns. See `docs/acceptance/issue_007_gui_sample_transcript.md` for the captured outputs.
- Streamlit AppTest clicked the comparison Run path and observed solved MAP/Max-IG result cards/tables. Battle AppTest observed no solver table before finish, human-only feedback columns after a non-terminal guess, and solver trajectory columns only after Give up.
- The exact launch command `uv run --with . streamlit run src/bayesian_hardle/streamlit_app.py --server.headless true --server.port 8505` reached `http://localhost:8505` on this Mac. A normal browser connector was unavailable in this environment, so browser visual evidence is represented by Streamlit AppTest rather than a screenshot.
- `project-control/PROJECT_STATE.md` had no diff against the ISSUE-006 base.

Evidence paths:
- `docs/superpowers/specs/2026-10-25-interactive-browser-gui-design.md`
- `docs/superpowers/plans/2026-10-25-interactive-browser-gui.md`
- `docs/acceptance/issue_007_gui_sample_transcript.md`
- `src/bayesian_hardle/application.py`
- `src/bayesian_hardle/streamlit_app.py`
- `tests/test_application_sessions.py`
- `tests/test_streamlit_smoke.py`

Known limitations:
- The first full-support Max-IG run may construct the exact `uint8` matrix
  cache under `.cache/bayesian_hardle` (about 160.6 MiB for the 12,974 x 12,974
  support); later runs reuse it.
- Streamlit AppTest and local server startup are local behavioral evidence, not
  physical-browser, remote, or business acceptance.
- ISSUE-006 and ISSUE-007 remain pending independent SUPERVISOR review; this
  report does not modify or advance `PROJECT_STATE.md`.

## 2026-10-25 — [EXECUTION REPORT ADDENDUM] ISSUE-007 final handoff checkpoint

The audited handoff documentation commit is `405bd39ed8e43144af5ff12511d814e66da3f794`.
The worktree is intended to remain clean on branch
`codex/issue-007-interactive-gui`; supervisor review is still required before
any accepted-state advancement.

## 2026-10-25 — [EXECUTION REPORT] ISSUE-008 Chinese GUI localization and complete policy visibility

Status: READY_FOR_REVIEW (executor evidence only; supervisor acceptance is not claimed)

Issue: `ISSUE-008`
Branch: `codex/issue-007-interactive-gui`
Base SHA: `c0661fd8de38df6760b84b6370a18890982b1642`
Implementation commit: `a7cd73f` (`feat: localize GUI and expose policy availability`)

What changed:
- Localized all Streamlit user-facing copy to natural simplified Chinese, including the page title, tabs, headers, labels, buttons, captions, help text, status/outcome labels, table columns, progress/spinner text, and GUI-supplied error wrappers. Technical mode and policy identifiers remain in parentheses where useful.
- Set the runnable policy labels to `随机基线（Random）`, `最大后验（MAP）`, and `最大信息增益（Max-IG）`. Comparison defaults remain MAP plus Max-IG, while Random is directly selectable in both comparison and battle controls.
- Added a visible `精确贝叶斯最优（Exact Bayes-optimal）` availability panel in both tabs. It is not present in either runnable selector, and the Chinese explanation states that accepted exact planning is currently computable and verified only on small vocabularies, so it cannot be accidentally run in 12,974-word full-support modes.
- Preserved the existing application/solver services, the two GUI tabs, and battle secrecy. Added AppTest coverage for Chinese tabs/headings/controls, default policies, Random selection, Exact Bayes-optimal non-runnability and status text, Chinese result columns/statuses, and pre-finish solver-trajectory redaction.
- Updated the GUI launch/usage guidance in `README.md` and the ISSUE-007 acceptance transcript without changing the uv/Streamlit launch command.

Fresh verification evidence:
- `UV_CACHE_DIR=/tmp/bayesian-hardle-uv-cache uv run --with . python -m unittest tests.test_streamlit_smoke -v` — `7/7` passed.
- `UV_CACHE_DIR=/tmp/bayesian-hardle-uv-cache uv run --with . python -m unittest discover -s tests -v` — `70/70` passed.
- `git diff --check` — passed before commit.
- `UV_CACHE_DIR=/tmp/bayesian-hardle-uv-cache uv run --with . streamlit run src/bayesian_hardle/streamlit_app.py --server.headless true --server.port 8505` — fresh server reached `http://localhost:8505`; the temporary process was then stopped cleanly.
- `project-control/PROJECT_STATE.md` was not modified; its pre-task SHA-256 was `16df9822c1b9267ae20d0f93c7aad5ac7b56b5732827b7c88e63230a3efce825`.

Evidence paths:
- `src/bayesian_hardle/streamlit_app.py`
- `tests/test_streamlit_smoke.py`
- `README.md`
- `docs/acceptance/issue_007_gui_sample_transcript.md`

Known boundary:
- No exact Bayes-optimal implementation or approximation was added; the policy remains unavailable for full-support GUI execution.
- AppTest and local Streamlit startup are local behavioral evidence, not physical-browser, remote, business, or supervisor acceptance.
- A pre-existing untracked `uv.lock` was present before ISSUE-008 work began and was intentionally not modified or included in the implementation commit. The tracked source diff is clean at `a7cd73f`, but the worktree still reports that unrelated untracked file.

## 2026-10-25 — [EXECUTION REPORT] ISSUE-009 small-vocabulary Exact GUI experiment

Status: READY_FOR_REVIEW (executor evidence only; supervisor acceptance is not claimed)

Issue: `ISSUE-009`
Branch: `codex/issue-009-small-exact-gui`
Worktree: `.worktrees/issue-009-small-exact-gui`
Base SHA: `03f98c4e3d4e7d59e3691cfac48bb3c1e7feb737` (ISSUE-008 handoff checkpoint)
Implementation commit: `94cae4ee04bb7114c4640f344449301cd4fdcd9d` (`feat: expose exact planner in small GUI scope`)

What changed:
- Added the top-level Chinese `实验范围` selector with `全词表（公平主实验）` and `小词表（Exact 实验）`.
- Preserved all three full-table modes and their Random / MAP / Max-IG runnable policies. Exact is visible in the full comparison page as unavailable with the explanation `仅小词表精确实验可用`; the shared application service rejects a full-scope Exact request before constructing a full-support solver.
- Added the deterministic ISSUE-004 small fixture: five candidate targets (`awake`, `cigar`, `humph`, `rebut`, `sissy`), eight declared legal guesses plus repository Hardle additions (`covid`, `padel`) for ten actual legal guesses, and a three-guess horizon.
- Connected the existing `ExactBayesOptimalPlanner` through the existing `PlannerPolicyAdapter`, `HardleFeedbackEngine`, and exact posterior updater. The small comparison service exposes Random / MAP / Max-IG / Exact together and renders side-by-side per-turn tables with guess, feedback, remaining candidates, decision time, cumulative time, status, and total turns.
- Kept the battle page on scalable policies and explicitly directs Exact comparison to the small-table comparison page. Added Chinese target-support validation and updated README usage instructions.
- Kept `project-control/PROJECT_STATE.md` unchanged; only this append-only journal received a new entry.

Fresh verification evidence:
- `UV_CACHE_DIR=/tmp/bayesian-hardle-uv-cache uv run --with . python -m unittest discover -s tests -v` — `77/77` passed.
- `UV_CACHE_DIR=/tmp/bayesian-hardle-uv-cache uv run --with . python -m unittest tests.test_streamlit_smoke -v` — `10/10` passed, including Chinese scope labels, four-policy small scope, full-scope Exact unavailability, target validation, and battle redaction.
- `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue009-pycache python3 -m compileall -q src tests experiments` — passed.
- uv-environment package and Streamlit imports — `compile_import=ok`.
- `git diff --check` — passed.
- Small application-service verification: actual support count `5`, actual legal-guess count `10`; Exact solved all five accepted targets in two turns, selected `arise` first for each, and MAP / Max-IG / Random ran through the same public service.
- Full-scope application verification: requesting Exact raised `Exact Bayes-optimal is only available in the small vocabulary experiment` before a full-support solver was built.
- Real server smoke: `UV_CACHE_DIR=/tmp/bayesian-hardle-uv-cache uv run --with . streamlit run src/bayesian_hardle/streamlit_app.py --server.headless true --server.port 8505` started on `http://localhost:8505`; authorized HTTP readback returned `<title>Streamlit`; the temporary server was stopped with Ctrl-C.
- `project-control/PROJECT_STATE.md` SHA-256 remained `16df9822c1b9267ae20d0f93c7aad5ac7b56b5732827b7c88e63230a3efce825`.

Known boundary:
- AppTest and local server startup/readback are local behavioral evidence, not physical-browser, remote, business, or supervisor acceptance.
- The worktree does not claim supervisor acceptance; the next state transition requires an independent `[SUPERVISOR REVIEW]`.

## 2026-10-26 — [EXECUTION REPORT] ISSUE-010 exact Bayes-optimal scaling audit

Status: READY_FOR_REVIEW (executor evidence only; supervisor acceptance is not claimed)

Issue: `ISSUE-010`
Branch: `codex/issue-010-exact-scaling`
Worktree: `.worktrees/issue-010-exact-scaling`
Base SHA: `34ec6169ba739547507c71666983f321d1b0ee05` (ISSUE-009 handoff)

Implementation:
- Kept `ExactBayesOptimalReferencePlanner` as the scalar exhaustive oracle.
- Added independently selectable exact layers to `ExactBayesOptimalPlanner`: proved singleton/last-horizon/two-candidate closed forms, explicit exact feedback-matrix transitions, normalized canonical state keys, posterior-mass action ordering, posterior-mass branch ordering, and lexicographic branch-and-bound.
- Branch-and-bound uses a solve-probability upper bound and expected-guess lower bound; incomplete action values are never cached.
- Small Exact GUI solver contexts now reuse the exact small feedback matrix while preserving the ISSUE-009 four-policy behavior and full-support Exact rejection.
- Added proof-oriented closed-form tests, canonical-key tests, 24 deterministic random reference-equivalence states, and an adversarial pruning-equivalence test.

Benchmark and profiling evidence:
- Machine-readable artifact: `experiments/results/issue_010_exact_scaling.json`
- Summary table and exactness justifications: `experiments/results/issue_010_exact_scaling_summary.md`
- cProfile evidence: `experiments/results/issue_010_profiles/`
- The staged driver ran `42` bounded rows; `34` completed and `8` timed out.
- The fully optimized multi-step ladder completed support `20`, horizon `3`, `28` legal actions. On that row it measured `5.40x` cumulative speedup over scalar baseline, `1,710` pruned actions, `3,864` evaluated branches, and `560` matrix bytes.
- The curated `2,315` support with full `12,974` legal actions completed only the horizon-1 closed-form probe. Its full matrix was `30,034,810` bytes. The scalar horizon-1 baseline and every horizon-2 layer timed out at the declared `20s` bound; no full-support exact-feasibility claim is made.

Fresh verification:
- `UV_CACHE_DIR=/tmp/bayesian-hardle-issue010-uv-cache uv run --with . python -m unittest discover -s tests -v` — `81/81` passed.
- Streamlit smoke subset — `10/10` passed.
- `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue010-pycache python3 -m compileall -q src tests experiments` — passed.
- `git diff --check` — passed.
- `project-control/PROJECT_STATE.md` SHA-256 remained `16df9822c1b9267ae20d0f93c7aad5ac7b56b5732827b7c88e63230a3efce825`; the file was not modified.

Known boundary:
- Benchmark timings are local machine evidence; they do not establish remote, device, live, or business acceptance.
- The largest completed exact state is the curated `2,315` support at horizon `1` via a terminal closed form; the largest completed non-terminal multi-step state is deterministic support `20`, horizon `3`, with `28` legal actions.
- This report does not advance `PROJECT_STATE.md`; the next state transition requires an independent `[SUPERVISOR REVIEW]`.

## 2026-10-26 — [EXECUTION REPORT] ISSUE-011 exact planner hotspot research

Status: READY_FOR_REVIEW (executor evidence only; supervisor acceptance is not claimed)

Issue: `ISSUE-011`
Branch: `codex/issue-011-exact-planner-hotspots`
Worktree: `.worktrees/issue-011-exact-planner-hotspots`
Base SHA: `a9f251a321b2fdf2cfd2911a01b1b9b7c23aa17c` (`codex/issue-010-exact-scaling`)
Result checkpoint: `b42f130`

What changed:
- Added an exact scalar horizon-2 evaluator and proof-oriented value formula:
  `success(g) = sum_o max legal candidate mass in branch o` and
  `expected(g) = 2 - p(g)`.
- Added exact `ExactFeedbackCodeMatrix` batch evaluation over feedback-code
  rows, preserving the accepted lexicographic objective and deterministic tie
  order. The scalar reference planner remains the oracle.
- Reused normalized mass and matrix eligibility through transition/posterior
  calls, and added structural counters for states, actions, branches, child
  support sizes, sorting/grouping, cache reuse, and NumPy/matrix cells.
- Added `experiments/issue_011_exact_hotspots.py`, deterministic support
  32/50/100/200/500 horizon-2 rows, support-32 horizon-3, full curated probes,
  machine-readable JSON, Markdown summary, and cProfile evidence.

Main exact result:
- Full curated support `2,315` × full legal `12,974` at horizon 2 completed
  with the batch path in approximately `1.17s` total in the final run,
  including `0.55s` matrix build and `30,034,810` matrix cells/bytes.
- The scalar horizon-2 formula completed the same row in approximately
  `15.09s`; the old ISSUE-010 recursive path timed out at its `30s` bound.
- This is exact horizon-2 completion evidence only. No horizon-3 full-support
  feasibility claim is made.

Evidence:
- `experiments/results/issue_011_exact_hotspots.json`
- `experiments/results/issue_011_exact_hotspots_summary.md`
- `experiments/results/issue_011_profiles/`
- `docs/superpowers/specs/2026-10-26-issue-011-exact-planner-hotspots-design.md`
- `docs/superpowers/plans/2026-10-26-issue-011-exact-planner-hotspots.md`
- `project-control/issues/ISSUE-011-exact-planner-hotspots.md`

Fresh verification:
- `PYTHONPATH=src PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue011-final-pycache python3 -m unittest discover -s tests -v` — `85` passed, `9` skipped.
- `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue011-final-pycache python3 -m compileall -q src tests experiments` — passed.
- Package import/version check — passed.
- JSON/Markdown artifact validation — passed: `51` rows, `50` completed,
  `1` timeout.
- `git diff --check` — passed.

Known boundaries:
- Internal immutable-state rewrite, alternative matrix grouping, and stronger
  branch bounds were deferred; deeper-horizon scaling remains unknown.
- Timings are local execution evidence. No remote, device, live, business, or
  supervisor acceptance is claimed.
- `project-control/PROJECT_STATE.md` was not modified. Its SHA-256 remained
  `16df9822c1b9267ae20d0f93c7aad5ac7b56b5732827b7c88e63230a3efce825`.

## 2026-10-26 — [EXECUTION REPORT] ISSUE-012 horizon-3 root decomposition,
reuse audit, and exact pruning

Status: READY_FOR_REVIEW (executor evidence only; supervisor acceptance is not
claimed)

Issue: `ISSUE-012`
Branch: `codex/issue-012-horizon3-root-audit`
Worktree: `/private/tmp/bayesian-hardle-issue-012`
Base SHA: `36561c1d0d9bfc9d000de3bdd82c13939eb1c9ad`
(`codex/issue-011-exact-planner-hotspots`)
Result checkpoint before this handoff: `7441902`

What changed:
- Added opt-in horizon-3 root auditing in `ExactBayesOptimalPlanner`. Completed
  root runs record every first action, all feedback branches, branch posterior
  mass/support, child-state key digests, exact cache hits, h=2 batch work,
  timing buckets, incumbent timing, and exact prune location.
- Added `root_horizon_two_ordering`, an exact h=2 matrix proxy used only to
  order candidates before probes. It never removes actions or changes the
  exact objective, bound, or tie rule.
- Added reference-equivalence regression tests and a standalone bounded
  ladder/full-support benchmark with JSON, Markdown, and cProfile artifacts.

Main diagnosis:
- The completed h=3 ladder reached support `500` × legal `508`. On the
  pre-ISSUE-012 ordering control, mean Hardle branches/action increased from
  `8.32` at support 32 to `12.80` at support 500, while mean child
  support/branch increased from `3.84` to `39.06`.
- At support 500, exact child h=2 batch work was `116,515,388` matrix cells
  and about `4.77s` aggregate timing; root partitioning was about `0.054s`,
  cache/key handling `0.195s`, and pruning checks `0.001s`. This identifies
  repeated h=2 work as the dominant term.
- Child-state reuse was low at scale: `2,811` requests, `2,792` distinct
  canonical keys, `0.7%` repeated requests. The existing exact memoization was
  retained; no speculative second cache was added.
- The exact proxy reduced h=2 cells on all five paired rows. At support 500
  it reduced cells to `116,431,060` and raised root pruning from `98.4%` to
  `99.0%`. Paired selected guesses and values were equal within `1e-12`.
- No stronger certified root bound or full root-partition batch was added:
  profiling showed the h=2 child work dominated, and no cheaper exact bound
  with measured net benefit was established.

Evidence:
- `experiments/results/issue_012_horizon3_root_audit.json`
- `experiments/results/issue_012_horizon3_root_audit_summary.md`
- `experiments/results/issue_012_profiles/`
- `project-control/issues/ISSUE-012-horizon3-root-audit.md`

Scaling boundary:
- Largest completed exact h=3 row: support `500` × legal `508`, matrix
  memory `254,000` bytes.
- Curated `2,315` support × `12,974` legal h=3 probes used a declared `45s`
  budget in both ordering variants and timed out. No full 2,315/horizon-3
  feasibility claim is made. The matrix dimension is `30,034,810` uint8
  cells, but h=3 root completion was not observed.

Fresh verification:
- `PYTHONPATH=src PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue012-final-pycache python3 -m unittest discover -s tests -v` — `87` passed, `9` skipped.
- `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue012-final-pycache python3 -m compileall -q src tests experiments` — passed.
- Package import/version check — passed.
- JSON artifact validator — passed: `12` runs, `10` completed paired ladder
  rows, `2` explicit full-support timeouts; every completed root trace covers
  all legal first actions and satisfies requests = distinct + repeated.
- `git diff --check` — passed.
- `project-control/PROJECT_STATE.md` was not modified. Its SHA-256 remained
  `16df9822c1b9267ae20d0f93c7aad5ac7b56b5732827b7c88e63230a3efce825`.

Known boundaries:
- Timings are local machine evidence; no remote, device, live, business, or
  supervisor acceptance is claimed.
- The final handoff commit adds this append-only record; `PROJECT_STATE.md`
  remains unchanged and requires independent `[SUPERVISOR REVIEW]` before any
  accepted-state advancement.

## 2026-10-26 — [EXECUTION REPORT] ISSUE-013 horizon-2 child bounds and exact batch fusion

Status: READY_FOR_REVIEW (executor evidence only; supervisor acceptance is not claimed)

Issue: `ISSUE-013`
Branch: `codex/issue-013-horizon2-bounds-batch`
Worktree: `/private/tmp/bayesian-hardle-issue-013`
Base SHA: `34d4e58fdf940c40ca8a6a1f134e8a1125c573ae`
Implementation checkpoint before this handoff: `aa59c10`

What changed:
- Proved and tested a finite-36-code H2 capacity upper bound. It is exact-safe
  but too loose on the support=500 replay: strict child-action skips=0 and
  strict root-action skips=0. The bound is analysis-only and avoided work=0.
- Added an exact ragged H2 child block evaluator and explicit opt-in planner
  layer. Scalar/reference values and deterministic selections match within
  `1e-12`; default planner use is disabled after net-negative measurement.
- Added child H2 exact-solve, block, logical-cell, temporary-memory, and
  bound-only-skip instrumentation plus a fresh ladder/full-probe driver.

Fresh measurement:
- Completed exact h=3 ladder supports: `32, 50, 100, 200, 500, 750, 1000`
  with legal counts `support+8`; all 7 control/fused pairs were equivalent.
- At support=500: control select `6.007s`, `116,431,060` H2 cells;
  fused select `7.163s`, `119,111,268` H2 cells, peak temporary `256,484`
  bytes. The delayed branch-and-bound flush makes fusion slower.
- Largest completed exact row: support `1000` × legal `1008` × h=3.
- Curated `2315 × 12974 × h=3`: both control and fused probes timed out at
  the declared `45s` budget. No feasibility claim is made.

Evidence:
- `docs/superpowers/specs/2026-10-26-issue-013-horizon2-bounds-batch-design.md`
- `docs/superpowers/plans/2026-10-26-issue-013-horizon2-bounds-batch.md`
- `experiments/results/issue_013_horizon2_bounds_batch.json`
- `experiments/results/issue_013_horizon2_bounds_batch_summary.md`
- `experiments/results/issue_013_profiles/`
- `project-control/issues/ISSUE-013-horizon2-bounds-batch.md`

Verification observed before final handoff rerun:
- Full suite `92` passed, `9` skipped.
- `compileall`, artifact validation, paired exact-equivalence validation,
  and `git diff --check` passed.
- `PROJECT_STATE.md` SHA-256 remains
  `16df9822c1b9267ae20d0f93c7aad5ac7b56b5732827b7c88e63230a3efce825`.

Known boundaries:
- Timings are local execution evidence; no remote, device, live, business, or
  supervisor acceptance is claimed.
- `PROJECT_STATE.md` remains unchanged and requires independent
  `[SUPERVISOR REVIEW]` before any accepted-state advancement.

## 2026-10-26 — [EXECUTION REPORT] ISSUE-013 final self-review verification

Status: READY_FOR_REVIEW (executor evidence only; supervisor acceptance is not claimed)

The final self-review added deterministic random-weight capacity-bound coverage,
fixed root snapshot indentation, and fixed exact-child solve accounting on a
cache-hit/value-miss path. Fresh verification after checkpoint `7fab431`:

- Full suite: `93` passed, `9` skipped.
- `compileall` and package import/version (`0.1.0`) passed.
- Artifact validator passed for `14` completed rows and `2` bounded timeouts.
- `git diff --check` passed.
- `PROJECT_STATE.md` remains unchanged at SHA-256
  `16df9822c1b9267ae20d0f93c7aad5ac7b56b5732827b7c88e63230a3efce825`.

## 2026-10-26 — [EXECUTION REPORT] ISSUE-014 H2 action-space structure and similarity bounds

Status: `READY_FOR_REVIEW` (executor evidence only; supervisor acceptance is not
claimed)

Issue: `ISSUE-014`
Branch: `codex/issue-014-h2-action-similarity`
Worktree: `/private/tmp/bayesian-hardle-issue-014`
Base SHA: `b50f3ba541327264e86b63137c3f37896b576dc8`

What was measured:

- Reconstructed ISSUE-013 H3 child supports for completed ladder cases at
  support 100, 200, 500, 750, and 1000, plus a bounded curated-2315 frontier
  from eight deterministic root guesses.
- Canonicalized all legal-guess feedback rows into unlabeled candidate
  partitions and separated partition equivalence from exact lexicographic
  action equivalence.
- Proved and tested the exact safe collapse key `(partition, immediate-hit
  posterior mass)`. Partition-only grouping is unsound for expected guesses.
- Proved and adversarially tested the sufficient dominance condition: a finer
  partition plus no smaller immediate-hit mass cannot be worse under H2.
- Derived total-variation fixed-action and optimal-value bounds, then replayed
  nearest solved-state neighbors with exact target values and incumbent skip
  simulation.

Decision:

- No planner optimization was integrated. Safe partition collapse reduced the
  sampled H2 logical cells by `5.9446%`, while a standalone representative
  collapse evaluator was `6.2x` to `35.7x` slower than the existing matrix
  evaluator.
- Dominance had zero examined-pair violations but only `0.1184%` sampled
  strict-dominance cell reduction after closed-form states were excluded.
- Similarity bounds preserved the exact best value in every replay, but
  completed support 500/750/1000 ladder samples had high-support strict skip
  ratio `0.2715%` and nearest-neighbor distance means `0.8567`, `0.8903`, and
  `0.9181`. The curated bounded frontier is not a full H3 feasibility claim.

Evidence:

- `docs/research/issue_014_h2_action_similarity.md`
- `experiments/results/issue_014_h2_action_similarity.json`
- `experiments/results/issue_014_h2_action_similarity_summary.md`
- `experiments/issue_014_h2_action_similarity.py`
- `tests/test_issue_014_action_similarity.py`

Known boundaries:

- The curated 2315 x 12974 H3 run was not completed; only a bounded child
  frontier was audited.
- Timings and skip counts are local research evidence. No remote, device,
  live, business, or supervisor acceptance is claimed.
- `project-control/PROJECT_STATE.md` was not modified.
