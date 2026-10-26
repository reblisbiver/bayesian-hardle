# ISSUE-014 H2 action-space structure and similarity-bound audit

This is a research-first audit. It measures exact unlabeled partition equivalence, tests the immediate-hit caveat, checks a refinement-plus-immediate-mass dominance condition, and measures total-variation bounds from previously solved H2 child states. No planner optimization is enabled by this artifact.

## Decision

- Partition collapse useful: `False`.
- Dominance rule useful: `False`; proof/test status: `safe_on_examined_pairs`.
- Similarity bounds useful: `False`.
- Integration status: `no planner integration; research audit only`.

## Per-case measurements

| Case | Frontier | Support | Legal | Child requests | Unique children | Audit states | Raw rows range | Unlabeled classes range | Safe collapse range | Similarity NN mean d | Similarity strict skips |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| sample100_h3_legal108 | recorded_completed_h3_run | 100 | 108 | 981 | 884 | 6 | 10-108 | 1-108 | 0.000-0.981 | 0.7823 | 1 |
| sample200_h3_legal208 | recorded_completed_h3_run | 200 | 208 | 2187 | 2010 | 6 | 101-208 | 5-208 | 0.000-0.966 | 0.8077 | 160 |
| sample500_h3_legal508 | recorded_completed_h3_run | 500 | 508 | 6002 | 5577 | 6 | 12-508 | 1-508 | 0.000-0.996 | 0.8567 | 1 |
| sample750_h3_legal758 | recorded_completed_h3_run | 750 | 758 | 9470 | 8814 | 6 | 11-758 | 1-758 | 0.000-0.997 | 0.8903 | 140 |
| sample1000_h3_legal1008 | recorded_completed_h3_run | 1000 | 1008 | 12902 | 12135 | 6 | 15-1008 | 1-1008 | 0.000-0.998 | 0.9181 | 1 |
| curated2315_h3_fulllegal | curated_bounded_frontier_only | 2315 | 12974 | 102 | 98 | 6 | 15-12974 | 1-12974 | 0.000-1.000 | 0.8486 | 11311 |

## Interpretation

A partition class is not automatically an action-equivalence class: if one member is a remaining answer candidate and another is probe-only, their expected-guesses components differ by the candidate's posterior mass even when their future partition is identical. The safe collapse key therefore includes both the unlabeled partition and immediate-hit mass.

The dominance condition tested here is exact but only sufficient: if action A's partition refines action B's partition and A's immediate-hit mass is at least B's, then the sum of per-block maxima cannot decrease and the expected-guesses component cannot increase. A zero violation count on the audited pairs is evidence for the implementation of this rule, while the mathematical argument is recorded in the research note.

The similarity bound uses total variation `d = 1/2 ||p-q||_1`. Every fixed H2 action's success probability and expected-guesses component move by at most `d`; the optimal success lies in `[F*(p)-d, F*(p)+d]`. The expected component is bounded using actions within `2d` of the solved state's best success. The artifact reports bound gaps and strict skip counts separately, because a valid but loose bound is not a useful planner optimization.

Timeouts and bounded curated-frontier extraction are coverage boundaries, not feasibility or acceptance claims.
