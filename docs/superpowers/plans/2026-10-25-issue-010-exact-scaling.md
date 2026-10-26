# ISSUE-010 — Exact Bayes-optimal scaling audit and staged optimization

## Scope and invariant

Work only in the ISSUE-010 worktree, based on the ISSUE-009 handoff at
`34ec616`. The canonical checkout and `project-control/PROJECT_STATE.md` stay
unchanged. The planner remains exact and keeps the accepted lexicographic
objective:

1. maximize finite-horizon solve probability;
2. among actions tied on that probability, minimize expected guesses until
   solve or horizon termination.

The existing scalar implementation remains available as a reference path.
Every optimization layer is independently selectable and benchmarked against
that path on deterministic small states.

## Stages

1. **Baseline/profile.** Add a bounded benchmark ladder and cProfile evidence
   for the scalar reference on increasing supports, legal-action counts, and
   horizons. Record function calls, runtime, node/action/branch counts, and
   the first practical limit.
2. **Closed forms.** Add only proved shortcuts: one-candidate states, one-step
   horizons, and two-candidate states when the candidate answer action is
   legal. Add proof-oriented tests for values and tie behavior.
3. **Exact transitions.** Permit an explicit `ExactFeedbackCodeMatrix` to
   replace repeated feedback evaluation and partition construction. Fall back
   to the scalar path when the matrix cannot represent the supplied semantics.
4. **Canonical memoization.** Normalize probability mass in cache keys, sort
   support entries, and canonicalize the legal action set for equivalent
   state identity. Keep observations out of the key because they do not affect
   future exact values.
5. **Action ordering.** Visit remaining answer candidates first, ordered by
   descending posterior mass and then word, followed by non-answer legal
   probes in deterministic lexical order. Final tie resolution remains
   deterministic and independent of evaluation order.
6. **Branch ordering.** Visit feedback branches by descending posterior mass,
   then deterministic outcome code. This affects only search order.
7. **Exact branch-and-bound.** For an action prefix, use solve-probability
   upper bound `solved_mass + unexplored_mass`. When that cannot beat the
   incumbent, or ties its primary value while the expected-guess lower bound
   cannot improve the incumbent, stop the action. Never cache an incomplete
   action value.
8. **Frontier and GUI.** Run the same ladder after each layer, include
   deterministic subsets of the 2,315 curated answers and bounded full-size
   probes, and retain the ISSUE-009 small Exact GUI behavior. Expose a larger
   exact demo only if measurements show it remains responsive.

## Verification gates

- Scalar/reference and fully optimized planners return equal lexicographic
  values on many deterministic random states; selected guesses are compared
  where the deterministic tie order is shared.
- Matrix transitions agree with scalar Hardle feedback and posterior updates,
  including duplicate-letter cases.
- Adversarial branch-and-bound cases match exhaustive reference values and
  demonstrate pruning without pruning the optimum.
- The same benchmark ladder reports incremental and cumulative speedups,
  actions/branches/nodes, cache hits, and matrix memory.
- Full test suite, `compileall`, `git diff --check`, and an ISSUE-009 GUI
  smoke/regression check pass before the worktree is marked
  `READY_FOR_REVIEW`.
- `project-control/JOURNAL.md` receives one append-only executor handoff;
  `PROJECT_STATE.md` receives no edit.
