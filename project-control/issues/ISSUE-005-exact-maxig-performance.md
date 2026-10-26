# ISSUE-005 — Exact Max-IG performance engineering

## Goal

Reduce the Python overhead of exact full-vocabulary Max-IG while preserving
the accepted Bayesian Hardle definition and the scalar implementation as the
correctness reference. This issue is engineering-only; it does not reopen the
prior, hypothesis space, feedback semantics, objective, or scheduled-answer
boundary.

## Accepted contract

- Legal guesses remain the complete 12,974-word legal vocabulary.
- Candidate answers remain the complete 2,315-word answer vocabulary.
- Feedback remains the duplicate-aware pair `(exact_count, misplaced_count)`.
- Max-IG remains exact information gain with the existing `1e-12` tie rule:
  greatest posterior mass among remaining candidate answers, then stable legal
  order.
- The scalar `HardleFeedbackEngine`, `ExactOutcomePartitioner`, and
  `ExactInformationGainCalculator` remain available as the correctness
  reference path.
- The solver receives no scheduled-answer membership or other evaluation-only
  information.

## Required implementation

1. Add a deterministic compact `uint8` feedback-code matrix for the fixed
   legal-guess by candidate-answer vocabulary. Build it with exact NumPy
   vectorization using exact-position matches and multiplicity-limited letter
   overlap; do not use Wordle color-pattern semantics or reduce the search
   space.
2. Add a fast Max-IG path that computes weighted feedback-outcome masses from a
   matrix row and the current posterior weights. It must not construct a full
   posterior object for every hypothetical branch.
3. Add deterministic decision caching keyed by normalized belief/state and the
   legal-guess universe. Caching may reuse decisions but must not alter policy
   semantics.
4. Keep all scalar reference interfaces and make the accelerated path
   selectable/observable in tests and benchmarks.
5. Declare NumPy as a package dependency if the accelerated path requires it.

## Acceptance gates

- Matrix codes match the canonical feedback engine on duplicate-letter cases
  and at least 10,000 deterministic randomized full-vocabulary pairs.
- Fast IG matches scalar exact IG within `1e-12` for uniform and non-uniform
  beliefs, repeated-letter cases, and random belief subsets.
- Fast and scalar Max-IG select the same action, including tie behavior.
- Candidate filtering remains canonical and no scheduled answer membership is
  introduced.
- All existing tests pass.
- Fresh machine measurements report cold matrix build/footprint, warm full
  first-move selection, and the existing full Max-IG experiment. Targets are
  cold first move `<= 2.0s` and warm first move `<= 0.5s`; any miss must retain
  a profile-backed hotspot report.

## Handoff boundary

Work in `codex/issue-005-maxig-speed` in the isolated repository worktree.
Append one `[EXECUTION REPORT]` to `project-control/JOURNAL.md`, leave
`PROJECT_STATE.md` unchanged, and hand off as `READY_FOR_REVIEW` with exact
commit SHA(s), commands, evidence paths, and remaining unknowns. Executor
evidence is not supervisor acceptance.
