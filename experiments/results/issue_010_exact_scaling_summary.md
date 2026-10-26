# ISSUE-010 exact planner scaling audit

All rows are root-state selections on deterministic supports. A timeout is an observed bounded limit, not an exact-feasibility claim.

| Case | Layer | Status | Support | Legal | H | Total s | Incremental vs prior | Cumulative vs baseline | Actions | Branches | Cache hit/miss | Pruned | Matrix bytes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fixture5_h3_legal10 | baseline_scalar | completed | 5 | 10 | 3 | 0.012 | - | 1.00x | 290 | 503 | 178/29 | 0 | 0 |
| fixture5_h3_legal10 | closed_forms | completed | 5 | 10 | 3 | 0.002 | 6.45x | 6.45x | 50 | 132 | 88/28 | 0 | 0 |
| fixture5_h3_legal10 | matrix_transitions | completed | 5 | 10 | 3 | 0.001 | 1.27x | 8.20x | 50 | 132 | 88/28 | 0 | 50 |
| fixture5_h3_legal10 | canonical_memoization | completed | 5 | 10 | 3 | 0.002 | 0.92x | 7.51x | 50 | 132 | 88/28 | 0 | 50 |
| fixture5_h3_legal10 | action_ordering | completed | 5 | 10 | 3 | 0.002 | 0.95x | 7.16x | 50 | 132 | 88/28 | 0 | 50 |
| fixture5_h3_legal10 | branch_ordering | completed | 5 | 10 | 3 | 0.002 | 1.00x | 7.19x | 50 | 132 | 88/28 | 0 | 50 |
| fixture5_h3_legal10 | branch_and_bound | completed | 5 | 10 | 3 | 0.007 | 0.23x | 1.67x | 50 | 113 | 75/28 | 37 | 50 |
| sample8_h3_legal16 | baseline_scalar | completed | 8 | 16 | 3 | 0.017 | - | 1.00x | 1168 | 2252 | 954/73 | 0 | 0 |
| sample8_h3_legal16 | closed_forms | completed | 8 | 16 | 3 | 0.008 | 2.19x | 2.19x | 192 | 547 | 433/71 | 0 | 0 |
| sample8_h3_legal16 | matrix_transitions | completed | 8 | 16 | 3 | 0.005 | 1.57x | 3.44x | 192 | 547 | 433/71 | 0 | 128 |
| sample8_h3_legal16 | canonical_memoization | completed | 8 | 16 | 3 | 0.006 | 0.88x | 3.02x | 192 | 547 | 433/71 | 0 | 128 |
| sample8_h3_legal16 | action_ordering | completed | 8 | 16 | 3 | 0.006 | 1.01x | 3.04x | 192 | 547 | 433/71 | 0 | 128 |
| sample8_h3_legal16 | branch_ordering | completed | 8 | 16 | 3 | 0.006 | 0.96x | 2.91x | 192 | 547 | 433/71 | 0 | 128 |
| sample8_h3_legal16 | branch_and_bound | completed | 8 | 16 | 3 | 0.005 | 1.22x | 3.55x | 176 | 405 | 304/69 | 143 | 128 |
| sample12_h3_legal20 | baseline_scalar | completed | 12 | 20 | 3 | 0.139 | - | 1.00x | 3940 | 8467 | 2790/197 | 0 | 0 |
| sample12_h3_legal20 | closed_forms | completed | 12 | 20 | 3 | 0.032 | 4.36x | 4.36x | 720 | 2066 | 1727/195 | 0 | 0 |
| sample12_h3_legal20 | matrix_transitions | completed | 12 | 20 | 3 | 0.018 | 1.79x | 7.78x | 720 | 2066 | 1733/189 | 0 | 240 |
| sample12_h3_legal20 | canonical_memoization | completed | 12 | 20 | 3 | 0.021 | 0.86x | 6.72x | 720 | 2066 | 1733/189 | 0 | 240 |
| sample12_h3_legal20 | action_ordering | completed | 12 | 20 | 3 | 0.021 | 0.97x | 6.54x | 720 | 2066 | 1733/189 | 0 | 240 |
| sample12_h3_legal20 | branch_ordering | completed | 12 | 20 | 3 | 0.021 | 1.01x | 6.59x | 720 | 2066 | 1733/189 | 0 | 240 |
| sample12_h3_legal20 | branch_and_bound | completed | 12 | 20 | 3 | 0.033 | 0.64x | 4.23x | 700 | 1395 | 1111/181 | 588 | 240 |
| sample20_h3_legal28 | baseline_scalar | completed | 20 | 28 | 3 | 0.273 | - | 1.00x | 18256 | 45083 | 9086/652 | 0 | 0 |
| sample20_h3_legal28 | closed_forms | completed | 20 | 28 | 3 | 0.129 | 2.12x | 2.12x | 2380 | 7976 | 6911/652 | 0 | 0 |
| sample20_h3_legal28 | matrix_transitions | completed | 20 | 28 | 3 | 0.066 | 1.95x | 4.12x | 2380 | 7976 | 6991/572 | 0 | 560 |
| sample20_h3_legal28 | canonical_memoization | completed | 20 | 28 | 3 | 0.092 | 0.72x | 2.96x | 2380 | 7976 | 6991/572 | 0 | 560 |
| sample20_h3_legal28 | action_ordering | completed | 20 | 28 | 3 | 0.081 | 1.13x | 3.35x | 2380 | 7976 | 6991/572 | 0 | 560 |
| sample20_h3_legal28 | branch_ordering | completed | 20 | 28 | 3 | 0.081 | 1.01x | 3.37x | 2380 | 7976 | 6991/572 | 0 | 560 |
| sample20_h3_legal28 | branch_and_bound | completed | 20 | 28 | 3 | 0.048 | 1.69x | 5.69x | 1932 | 3864 | 3157/500 | 1710 | 560 |
| curated2315_h1_fulllegal | baseline_scalar | timed_out | 2315 | 12974 | 1 | 20.013 | - | - | - | - | - | - | - |
| curated2315_h1_fulllegal | closed_forms | completed | 2315 | 12974 | 1 | 0.002 | - | - | 0 | 0 | 0/1 | 0 | 0 |
| curated2315_h1_fulllegal | matrix_transitions | completed | 2315 | 12974 | 1 | 0.524 | 0.00x | - | 0 | 0 | 0/1 | 0 | 30034810 |
| curated2315_h1_fulllegal | canonical_memoization | completed | 2315 | 12974 | 1 | 0.542 | 0.97x | - | 0 | 0 | 0/1 | 0 | 30034810 |
| curated2315_h1_fulllegal | action_ordering | completed | 2315 | 12974 | 1 | 0.531 | 1.02x | - | 0 | 0 | 0/1 | 0 | 30034810 |
| curated2315_h1_fulllegal | branch_ordering | completed | 2315 | 12974 | 1 | 0.541 | 0.98x | - | 0 | 0 | 0/1 | 0 | 30034810 |
| curated2315_h1_fulllegal | branch_and_bound | completed | 2315 | 12974 | 1 | 0.532 | 1.02x | - | 0 | 0 | 0/1 | 0 | 30034810 |
| curated2315_h2_fulllegal | baseline_scalar | timed_out | 2315 | 12974 | 2 | 20.018 | - | - | - | - | - | - | - |
| curated2315_h2_fulllegal | closed_forms | timed_out | 2315 | 12974 | 2 | 20.009 | - | - | - | - | - | - | - |
| curated2315_h2_fulllegal | matrix_transitions | timed_out | 2315 | 12974 | 2 | 20.022 | - | - | - | - | - | - | - |
| curated2315_h2_fulllegal | canonical_memoization | timed_out | 2315 | 12974 | 2 | 20.103 | - | - | - | - | - | - | - |
| curated2315_h2_fulllegal | action_ordering | timed_out | 2315 | 12974 | 2 | 20.099 | - | - | - | - | - | - | - |
| curated2315_h2_fulllegal | branch_ordering | timed_out | 2315 | 12974 | 2 | 20.155 | - | - | - | - | - | - | - |
| curated2315_h2_fulllegal | branch_and_bound | timed_out | 2315 | 12974 | 2 | 20.126 | - | - | - | - | - | - | - |

## Layer exactness justifications

| Layer | Why it preserves the objective |
|---|---|
| closed_forms | Singleton, last-horizon, and legal two-candidate formulas enumerate the same terminal outcomes and Bellman value under the accepted lexicographic objective. |
| matrix_transitions | The existing uint8 matrix encodes the same duplicate-aware `(exact, misplaced)` Hardle feedback; grouping and normalized member masses are algebraically identical to scalar evaluation. |
| canonical_memoization | Keys normalize mass, sort support, and exclude only history that cannot affect future transitions; equivalent belief/support states therefore share values. |
| action_ordering | All legal actions are still evaluated unless branch-and-bound proves them unable to improve the incumbent; only visit order changes. |
| branch_ordering | All feedback branches remain in the Bellman sum; posterior probability descending changes only evaluation order. |
| branch_and_bound | Uses solve-probability upper bound `solved_mass + unexplored_mass` and expected-guess lower bound; pruning occurs only when the action cannot improve the incumbent within the documented tie tolerance. |


## Profiling

The profile text files under `experiments/results/issue_010_profiles/` list cumulative-time hotspots for the scalar baseline and the fully optimized ladder case.

| Profile | Dominant cumulative-time calls (ncalls from cProfile) |
|---|---|
| scalar fixture5 | `_guess_value` 497/11; `HardleFeedbackEngine.evaluate` 1,132; `ExactPosteriorUpdater.update` 206; `_transition_branches` 290 |
| optimized sample12 | `_guess_value` 1,992/21; `_mass_table` 7,162; `_transition_branches` 700; `_can_use_matrix` 1,991; `_posterior_for_branch` 1,291 |

The optimized profile shifts the hot path away from repeated scalar feedback and posterior filtering; remaining cost is exact state-key/mass handling and matrix transition bookkeeping.

## Interpretation boundary

The curated 2,315 / full-legal rows are bounded probes. Completion at horizon 1 only measures the terminal closed form; it does not prove a multi-step exact solve over the full support. Any timeout remains the practical frontier evidence.
