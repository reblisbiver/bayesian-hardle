# ISSUE-011 — Exact planner hotspot research design

## Intent

Continue the exact Bayes-optimal scaling work from ISSUE-010 on the isolated
`codex/issue-011-exact-planner-hotspots` branch. The immediate question is why
the optimized planner still times out on the curated 2,315-support,
12,974-legal horizon-2 root state, and which exact changes move that frontier.

The accepted value remains lexicographic:

1. maximize finite-horizon solve probability;
2. among equal solve probabilities, minimize expected guesses until solve or
   horizon termination.

The scalar `ExactBayesOptimalReferencePlanner` remains the oracle on tractable
states. No approximation, heuristic pruning, or change to public
`BeliefState` semantics is in scope.

## Goals and non-goals

Goals:

- derive and test the exact horizon-2 action value;
- evaluate all horizon-2 legal actions in an exact matrix batch path;
- measure redundant mass/canonicalization and transition work before and after
  each material change;
- add a deterministic benchmark ladder above support 20 and a bounded full
  2,315-support probe;
- preserve auditable JSON, Markdown, profile, test, and journal evidence.

Non-goals:

- no change to the Bayesian objective, feedback rules, or legal/answer
  vocabulary semantics;
- no mutation of the canonical checkout or `project-control/PROJECT_STATE.md`;
- no claim that a bounded timeout is feasibility evidence;
- no internal state rewrite unless profiling demonstrates material benefit and
  the public behavior remains equivalent.

## Approaches considered

### 1. Horizon-2 exact scalar formula, then exact matrix batch (chosen)

For a first guess `g`, let `p(w)` be the normalized state mass and let
`B_o(g)` be the feedback branch. The exact value is

```
success(g) = sum_o max({p(w): w in B_o(g) and w is legal}, default=0)
expected(g) = 1 + (1 - p(g))
```

The winning branch contributes `p(g)` when `g` is a remaining legal answer;
every non-winning branch contributes the mass of its best legal final answer.
The expected value is exact because one second guess is always taken after a
non-winning first guess, regardless of whether that final guess wins.

First implement the scalar form using the existing exact branch semantics and
compare its values and selected actions to the reference planner. Then use the
same formula over matrix feedback-code rows, with exact per-code maxima, to
score all legal first guesses in one batch. This directly attacks the shallow
but very wide 2,315 × 12,974 state.

### 2. Internal immutable exact state rewrite (deferred)

Carry support indices and normalized mass arrays instead of reconstructing
`BeliefState` and observation history for every child. This may reduce Python
allocation and canonicalization, but it has a larger semantic surface and is
not needed to validate the horizon-2 formula. It will only be attempted if
post-A profiling shows posterior construction remains a dominant cost on the
representative horizon-3 ladder.

### 3. Stronger branch-and-bound and new partition machinery (conditional)

Tighter bounds or alternative grouping can help deeper searches, but neither
is assumed safe or faster. They will be implemented only after an adversarial
reference test and a before/after benchmark demonstrate a strict benefit.

## Chosen architecture

- Keep the reference planner unchanged as the scalar oracle.
- Add opt-in `horizon_two_closed_form` and `horizon_two_batch` optimization
  layers; the default optimized planner enables both.
- Expose stable counters for scalar formula hits, batch calls/actions, matrix
  cells, states, actions, branches, cache reuse, and pruning.
- Reuse the current `ExactFeedbackCodeMatrix`; the batch path is valid only
  for the exact `HardleFeedbackEngine` semantics and a matrix containing all
  required legal guesses and support answers.
- Reuse the existing deterministic action tie rank. Batch evaluation changes
  only how values are computed, not action ordering or tie resolution.
- Thread one already-computed normalized mass table and matrix eligibility
  through transition/posterior calls where this is measured to remove the
  ISSUE-010 redundancy.

## Evidence and acceptance boundary

Every optimization gets:

- a failing proof/regression test before production code;
- scalar/reference equivalence on deterministic random weighted states;
- a before/after benchmark row with support, legal count, horizon, runtime,
  states/actions/branches, cache statistics, matrix bytes, and shortcut
  counters;
- fresh full-suite, compile/import, whitespace, branch/worktree, and
  `PROJECT_STATE.md` unchanged checks.

The largest exact support/horizon reported in the handoff is the largest row
whose worker completed within its explicit budget. A timeout is recorded as a
timeout only.
