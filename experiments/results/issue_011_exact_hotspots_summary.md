# ISSUE-011 exact planner hotspot audit

The objective and feedback semantics are unchanged. A bounded timeout is an observed limit, not an exact-feasibility claim.

| Case | Variant | Status | Support | Legal | H | Total s | Selected | Value | States | Actions | Branches | Pruned | Cache H/M | Batch calls/actions | Matrix bytes |
|---|---|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| fixture5_h3_legal10 | baseline_reference | completed | 5 | 10 | 3 | 0.010 | arise | [1.0, 1.9999999999999998] | 29 | 290 | 503 | 0 | 178/29 | 0/0 | 0 |
| fixture5_h3_legal10 | closed_forms | completed | 5 | 10 | 3 | 0.002 | arise | [1.0, 1.9999999999999998] | 28 | 50 | 132 | 0 | 88/28 | 0/0 | 0 |
| fixture5_h3_legal10 | matrix_transitions | completed | 5 | 10 | 3 | 0.001 | arise | [1.0, 1.9999999999999998] | 28 | 50 | 132 | 0 | 88/28 | 0/0 | 50 |
| fixture5_h3_legal10 | canonical_memoization | completed | 5 | 10 | 3 | 0.001 | arise | [1.0, 1.9999999999999998] | 28 | 50 | 132 | 0 | 88/28 | 0/0 | 50 |
| fixture5_h3_legal10 | action_ordering | completed | 5 | 10 | 3 | 0.001 | arise | [1.0, 1.9999999999999998] | 28 | 50 | 132 | 0 | 88/28 | 0/0 | 50 |
| fixture5_h3_legal10 | branch_ordering | completed | 5 | 10 | 3 | 0.001 | arise | [1.0, 1.9999999999999998] | 28 | 50 | 132 | 0 | 88/28 | 0/0 | 50 |
| fixture5_h3_legal10 | issue010_full | completed | 5 | 10 | 3 | 0.003 | arise | [1.0, 1.9999999999999998] | 28 | 50 | 113 | 37 | 75/28 | 0/0 | 50 |
| fixture5_h3_legal10 | horizon_two_scalar | completed | 5 | 10 | 3 | 0.001 | arise | [1.0, 1.9999999999999998] | 13 | 50 | 29 | 6 | 15/13 | 0/0 | 50 |
| fixture5_h3_legal10 | horizon_two_batch | completed | 5 | 10 | 3 | 0.001 | arise | [1.0, 1.9999999999999998] | 13 | 50 | 29 | 6 | 15/13 | 4/40 | 50 |
| sample8_h3_legal16 | baseline_reference | completed | 8 | 16 | 3 | 0.018 | beget | [1.0, 2.0] | 73 | 1168 | 2252 | 0 | 954/73 | 0/0 | 0 |
| sample8_h3_legal16 | closed_forms | completed | 8 | 16 | 3 | 0.008 | beget | [1.0, 2.0] | 71 | 192 | 547 | 0 | 433/71 | 0/0 | 0 |
| sample8_h3_legal16 | matrix_transitions | completed | 8 | 16 | 3 | 0.004 | beget | [1.0, 2.0] | 71 | 192 | 547 | 0 | 433/71 | 0/0 | 128 |
| sample8_h3_legal16 | canonical_memoization | completed | 8 | 16 | 3 | 0.005 | beget | [1.0, 2.0] | 71 | 192 | 547 | 0 | 433/71 | 0/0 | 128 |
| sample8_h3_legal16 | action_ordering | completed | 8 | 16 | 3 | 0.005 | beget | [1.0, 2.0] | 71 | 192 | 547 | 0 | 433/71 | 0/0 | 128 |
| sample8_h3_legal16 | branch_ordering | completed | 8 | 16 | 3 | 0.005 | beget | [1.0, 2.0] | 71 | 192 | 547 | 0 | 433/71 | 0/0 | 128 |
| sample8_h3_legal16 | issue010_full | completed | 8 | 16 | 3 | 0.004 | beget | [1.0, 2.0] | 69 | 176 | 405 | 143 | 304/69 | 0/0 | 128 |
| sample8_h3_legal16 | horizon_two_scalar | completed | 8 | 16 | 3 | 0.002 | beget | [1.0, 2.0] | 34 | 176 | 61 | 14 | 26/34 | 0/0 | 128 |
| sample8_h3_legal16 | horizon_two_batch | completed | 8 | 16 | 3 | 0.001 | beget | [1.0, 2.0] | 34 | 176 | 61 | 14 | 26/34 | 10/160 | 128 |
| sample12_h3_legal20 | baseline_reference | completed | 12 | 20 | 3 | 0.063 | gruel | [1.0, 2.3333333333333335] | 197 | 3940 | 8467 | 0 | 2790/197 | 0/0 | 0 |
| sample12_h3_legal20 | closed_forms | completed | 12 | 20 | 3 | 0.031 | gruel | [1.0, 2.3333333333333335] | 195 | 720 | 2066 | 0 | 1727/195 | 0/0 | 0 |
| sample12_h3_legal20 | matrix_transitions | completed | 12 | 20 | 3 | 0.015 | gruel | [1.0, 2.3333333333333335] | 189 | 720 | 2066 | 0 | 1733/189 | 0/0 | 240 |
| sample12_h3_legal20 | canonical_memoization | completed | 12 | 20 | 3 | 0.018 | gruel | [1.0, 2.3333333333333335] | 189 | 720 | 2066 | 0 | 1733/189 | 0/0 | 240 |
| sample12_h3_legal20 | action_ordering | completed | 12 | 20 | 3 | 0.019 | gruel | [1.0, 2.3333333333333335] | 189 | 720 | 2066 | 0 | 1733/189 | 0/0 | 240 |
| sample12_h3_legal20 | branch_ordering | completed | 12 | 20 | 3 | 0.019 | gruel | [1.0, 2.3333333333333335] | 189 | 720 | 2066 | 0 | 1733/189 | 0/0 | 240 |
| sample12_h3_legal20 | issue010_full | completed | 12 | 20 | 3 | 0.016 | gruel | [1.0, 2.3333333333333335] | 181 | 700 | 1395 | 588 | 1111/181 | 0/0 | 240 |
| sample12_h3_legal20 | horizon_two_scalar | completed | 12 | 20 | 3 | 0.007 | gruel | [1.0, 2.3333333333333335] | 67 | 700 | 77 | 18 | 9/67 | 0/0 | 240 |
| sample12_h3_legal20 | horizon_two_batch | completed | 12 | 20 | 3 | 0.003 | gruel | [1.0, 2.3333333333333335] | 67 | 700 | 77 | 18 | 9/67 | 34/680 | 240 |
| sample20_h3_legal28 | baseline_reference | completed | 20 | 28 | 3 | 0.711 | amble | [1.0, 2.45] | 652 | 18256 | 45083 | 0 | 9086/652 | 0/0 | 0 |
| sample20_h3_legal28 | closed_forms | completed | 20 | 28 | 3 | 0.133 | amble | [1.0, 2.45] | 652 | 2380 | 7976 | 0 | 6911/652 | 0/0 | 0 |
| sample20_h3_legal28 | matrix_transitions | completed | 20 | 28 | 3 | 0.057 | amble | [1.0, 2.45] | 572 | 2380 | 7976 | 0 | 6991/572 | 0/0 | 560 |
| sample20_h3_legal28 | canonical_memoization | completed | 20 | 28 | 3 | 0.069 | amble | [1.0, 2.45] | 572 | 2380 | 7976 | 0 | 6991/572 | 0/0 | 560 |
| sample20_h3_legal28 | action_ordering | completed | 20 | 28 | 3 | 0.069 | amble | [1.0, 2.45] | 572 | 2380 | 7976 | 0 | 6991/572 | 0/0 | 560 |
| sample20_h3_legal28 | branch_ordering | completed | 20 | 28 | 3 | 0.107 | amble | [1.0000000000000002, 2.4499999999999993] | 572 | 2380 | 7976 | 0 | 6991/572 | 0/0 | 560 |
| sample20_h3_legal28 | issue010_full | completed | 20 | 28 | 3 | 0.084 | amble | [1.0000000000000002, 2.4499999999999993] | 500 | 1932 | 3864 | 1710 | 3157/500 | 0/0 | 560 |
| sample20_h3_legal28 | horizon_two_scalar | completed | 20 | 28 | 3 | 0.018 | amble | [1.0000000000000002, 2.4499999999999993] | 108 | 1932 | 134 | 26 | 25/108 | 0/0 | 560 |
| sample20_h3_legal28 | horizon_two_batch | completed | 20 | 28 | 3 | 0.010 | amble | [1.0000000000000002, 2.4499999999999993] | 108 | 1932 | 134 | 26 | 25/108 | 68/1904 | 560 |
| curated2315_h1_fulllegal | issue010_full | completed | 2315 | 12974 | 1 | 0.512 | aback | [0.00043196544276457883, 1.0] | 1 | 0 | 0 | 0 | 0/1 | 0/0 | 30034810 |
| curated2315_h1_fulllegal | horizon_two_batch | completed | 2315 | 12974 | 1 | 0.534 | aback | [0.00043196544276457883, 1.0] | 1 | 0 | 0 | 0 | 0/1 | 0/0 | 30034810 |
| curated2315_h2_fulllegal | issue010_full | timed_out | 2315 | 12974 | 2 | 30.166 | - | - | - | - | - | - | - | - | - |
| curated2315_h2_fulllegal | horizon_two_scalar | completed | 2315 | 12974 | 2 | 15.086 | ester | [0.008207343412526998, 1.9995680345572355] | 1 | 12974 | 0 | 0 | 0/1 | 0/0 | 30034810 |
| curated2315_h2_fulllegal | horizon_two_batch | completed | 2315 | 12974 | 2 | 1.171 | ester | [0.008207343412526998, 1.9995680345572355] | 1 | 12974 | 0 | 0 | 0/1 | 1/12974 | 30034810 |
| sample32_h2_legal40 | horizon_two_scalar | completed | 32 | 40 | 2 | 0.001 | curse | [0.34375, 1.96875] | 1 | 40 | 0 | 0 | 0/1 | 0/0 | 1280 |
| sample32_h2_legal40 | horizon_two_batch | completed | 32 | 40 | 2 | 0.001 | curse | [0.34375, 1.96875] | 1 | 40 | 0 | 0 | 0/1 | 1/40 | 1280 |
| sample50_h2_legal58 | horizon_two_scalar | completed | 50 | 58 | 2 | 0.002 | taper | [0.24, 1.98] | 1 | 58 | 0 | 0 | 0/1 | 0/0 | 2900 |
| sample50_h2_legal58 | horizon_two_batch | completed | 50 | 58 | 2 | 0.001 | taper | [0.24, 1.98] | 1 | 58 | 0 | 0 | 0/1 | 1/58 | 2900 |
| sample100_h2_legal108 | horizon_two_scalar | completed | 100 | 108 | 2 | 0.006 | delay | [0.13, 1.99] | 1 | 108 | 0 | 0 | 0/1 | 0/0 | 10800 |
| sample100_h2_legal108 | horizon_two_batch | completed | 100 | 108 | 2 | 0.001 | delay | [0.13, 1.99] | 1 | 108 | 0 | 0 | 0/1 | 1/108 | 10800 |
| sample200_h2_legal208 | horizon_two_batch | completed | 200 | 208 | 2 | 0.003 | caper | [0.07500000000000001, 1.995] | 1 | 208 | 0 | 0 | 0/1 | 1/208 | 41600 |
| sample500_h2_legal508 | horizon_two_batch | completed | 500 | 508 | 2 | 0.010 | relay | [0.034, 1.998] | 1 | 508 | 0 | 0 | 0/1 | 1/508 | 254000 |
| sample32_h3_legal40 | issue010_full | completed | 32 | 40 | 3 | 0.075 | stage | [0.9999999999999999, 2.625] | 1545 | 2600 | 5480 | 2342 | 3694/1545 | 0/0 | 1280 |
| sample32_h3_legal40 | horizon_two_batch | completed | 32 | 40 | 3 | 0.012 | stage | [1.0, 2.625] | 83 | 2600 | 89 | 35 | 2/83 | 64/2560 | 1280 |

## Exactness and time movement

- `horizon_two_closed_form` uses the scalar identity `success(g) = sum_o max(p(w) for legal w in branch o)` and `expected(g) = 2 - p(g)`; the reference-equivalence tests cover deterministic random weighted states.
- `horizon_two_batch` applies the same identity to matrix rows with exact per-code maxima; it is enabled only for the exact Hardle engine and a compatible matrix.
- The current benchmark reports matrix build time separately from planner selection time. Matrix bytes are uint8 feedback-code storage.

## Per-optimization timing

| Case | Variant | Status | Total s | Selection s | Matrix build s |
|---|---|---:|---:|---:|---:|
| sample20_h3_legal28 | baseline_reference | completed | 0.711 | 0.711106208 | 1.669999999953653e-07 |
| sample20_h3_legal28 | issue010_full | completed | 0.084 | 0.08387449999999999 | 0.0003046250000000028 |
| sample20_h3_legal28 | horizon_two_scalar | completed | 0.018 | 0.018032959 | 0.0003164579999999917 |
| sample20_h3_legal28 | horizon_two_batch | completed | 0.010 | 0.009869124999999992 | 0.00031774999999999165 |
| curated2315_h2_fulllegal | issue010_full | timed_out | 30.166 | - | - |
| curated2315_h2_fulllegal | horizon_two_scalar | completed | 15.086 | 14.577172832999999 | 0.508736334 |
| curated2315_h2_fulllegal | horizon_two_batch | completed | 1.171 | 0.617200959 | 0.553958708 |

The support-20 horizon-3 comparison isolates the movement from the ISSUE-010 ladder to the scalar horizon-2 formula and then to the matrix batch path. The curated 2,315 horizon-2 rows are the direct practical-frontier comparison; the old recursive path is retained as a bounded timeout.

## Deferred hypotheses

- No internal immutable-state rewrite was made: after the horizon-2 shortcut, representative horizon-3 profile time is dominated by exact recursive state expansion and batch calls, while posterior construction is a small fraction of the run.
- No alternative matrix partition was made: the finite-code `np.maximum.at` batch is already the measured dominant NumPy work and completes the full horizon-2 root; Python transition grouping remains only on deeper horizon-3 roots.
- No stronger branch-and-bound bound was made: horizon-2 does not recurse or prune, and the support-32 horizon-3 row already shows exact pruning with reference-equivalent values; a new bound would need a separate adversarial proof and measured gain.

## Profile breakdown

| Profile | Bucket | Calls | Primitive calls | Internal s | Cumulative s |
|---|---|---:|---:|---:|---:|
| baseline_reference / fixture5_h3_legal10 | cache_handling | 236 | 236 | 0.000029 | 0.000051 |
| baseline_reference / fixture5_h3_legal10 | canonical_key | 704 | 704 | 0.000197 | 0.000468 |
| baseline_reference / fixture5_h3_legal10 | mass_table | 496 | 496 | 0.000163 | 0.000487 |
| baseline_reference / fixture5_h3_legal10 | matrix_eligibility | 290 | 290 | 0.000047 | 0.000059 |
| baseline_reference / fixture5_h3_legal10 | posterior_construction | 618 | 618 | 0.000362 | 0.003863 |
| baseline_reference / fixture5_h3_legal10 | recursion_state_expansion | 621 | 1313 | 0.001129 | 0.018079 |
| baseline_reference / fixture5_h3_legal10 | sorting | 733 | 733 | 0.000159 | 0.000278 |
| baseline_reference / fixture5_h3_legal10 | transition_grouping | 290 | 290 | 0.000578 | 0.003326 |
| issue010_full / fixture5_h3_legal10 | cache_handling | 131 | 131 | 0.000018 | 0.000030 |
| issue010_full / fixture5_h3_legal10 | canonical_key | 256 | 256 | 0.000108 | 0.000516 |
| issue010_full / fixture5_h3_legal10 | mass_table | 425 | 425 | 0.000170 | 0.000465 |
| issue010_full / fixture5_h3_legal10 | matrix_eligibility | 50 | 50 | 0.000043 | 0.000096 |
| issue010_full / fixture5_h3_legal10 | posterior_construction | 306 | 306 | 0.000253 | 0.000675 |
| issue010_full / fixture5_h3_legal10 | recursion_state_expansion | 163 | 407 | 0.000455 | 0.004825 |
| issue010_full / fixture5_h3_legal10 | sorting | 532 | 532 | 0.000101 | 0.000174 |
| issue010_full / fixture5_h3_legal10 | transition_grouping | 50 | 50 | 0.000173 | 0.000420 |
| baseline_reference / sample20_h3_legal28 | cache_handling | 10390 | 10390 | 0.001354 | 0.003341 |
| baseline_reference / sample20_h3_legal28 | canonical_key | 37732 | 37732 | 0.010448 | 0.028350 |
| baseline_reference / sample20_h3_legal28 | mass_table | 27993 | 27993 | 0.010538 | 0.036103 |
| baseline_reference / sample20_h3_legal28 | matrix_eligibility | 18256 | 18256 | 0.003089 | 0.003981 |
| baseline_reference / sample20_h3_legal28 | posterior_construction | 29211 | 29211 | 0.017483 | 0.269860 |
| baseline_reference / sample20_h3_legal28 | recursion_state_expansion | 37194 | 74896 | 0.072210 | 1.425244 |
| baseline_reference / sample20_h3_legal28 | sorting | 38384 | 38384 | 0.010125 | 0.018051 |
| baseline_reference / sample20_h3_legal28 | transition_grouping | 18256 | 18256 | 0.047860 | 0.316286 |
| issue010_full / sample20_h3_legal28 | cache_handling | 4157 | 4157 | 0.000517 | 0.001155 |
| issue010_full / sample20_h3_legal28 | canonical_key | 9246 | 9246 | 0.003608 | 0.018739 |
| issue010_full / sample20_h3_legal28 | mass_table | 14506 | 14506 | 0.005773 | 0.015960 |
| issue010_full / sample20_h3_legal28 | matrix_eligibility | 1932 | 1932 | 0.001580 | 0.003739 |
| issue010_full / sample20_h3_legal28 | posterior_construction | 10968 | 10968 | 0.008543 | 0.023855 |
| issue010_full / sample20_h3_legal28 | recursion_state_expansion | 4825 | 14041 | 0.014961 | 0.173148 |
| issue010_full / sample20_h3_legal28 | sorting | 18768 | 18768 | 0.004093 | 0.006446 |
| issue010_full / sample20_h3_legal28 | transition_grouping | 1932 | 1932 | 0.007230 | 0.017834 |
| horizon_two_batch / sample20_h3_legal28 | cache_handling | 241 | 241 | 0.000045 | 0.000069 |
| horizon_two_batch / sample20_h3_legal28 | canonical_key | 362 | 362 | 0.000169 | 0.001053 |
| horizon_two_batch / sample20_h3_legal28 | mass_table | 658 | 658 | 0.000326 | 0.001002 |
| horizon_two_batch / sample20_h3_legal28 | matrix_eligibility | 28 | 28 | 0.000046 | 0.000135 |
| horizon_two_batch / sample20_h3_legal28 | numpy_matrix | 2788 | 2788 | 0.002168 | 0.004821 |
| horizon_two_batch / sample20_h3_legal28 | posterior_construction | 396 | 396 | 0.000408 | 0.001265 |
| horizon_two_batch / sample20_h3_legal28 | recursion_state_expansion | 301 | 565 | 0.001442 | 0.023528 |
| horizon_two_batch / sample20_h3_legal28 | sorting | 796 | 796 | 0.000222 | 0.000379 |
| horizon_two_batch / sample20_h3_legal28 | transition_grouping | 28 | 28 | 0.000237 | 0.000610 |
| horizon_two_batch / curated2315_h2_fulllegal | cache_handling | 2 | 2 | 0.000064 | 0.000159 |
| horizon_two_batch / curated2315_h2_fulllegal | canonical_key | 3 | 3 | 0.000106 | 0.007428 |
| horizon_two_batch / curated2315_h2_fulllegal | mass_table | 5 | 5 | 0.000382 | 0.001546 |
| horizon_two_batch / curated2315_h2_fulllegal | numpy_matrix | 12987 | 12987 | 0.132902 | 0.247661 |
| horizon_two_batch / curated2315_h2_fulllegal | recursion_state_expansion | 4 | 4 | 0.465805 | 1.224447 |
| horizon_two_batch / curated2315_h2_fulllegal | sorting | 7 | 7 | 0.001071 | 0.006359 |
| horizon_two_batch / sample32_h3_legal40 | cache_handling | 168 | 168 | 0.000030 | 0.000045 |
| horizon_two_batch / sample32_h3_legal40 | canonical_key | 274 | 274 | 0.000145 | 0.001176 |
| horizon_two_batch / sample32_h3_legal40 | mass_table | 528 | 528 | 0.000358 | 0.001201 |
| horizon_two_batch / sample32_h3_legal40 | matrix_eligibility | 40 | 40 | 0.000069 | 0.000232 |
| horizon_two_batch / sample32_h3_legal40 | numpy_matrix | 3392 | 3392 | 0.002552 | 0.005724 |
| horizon_two_batch / sample32_h3_legal40 | posterior_construction | 252 | 252 | 0.000296 | 0.001021 |
| horizon_two_batch / sample32_h3_legal40 | recursion_state_expansion | 287 | 455 | 0.001780 | 0.027842 |
| horizon_two_batch / sample32_h3_legal40 | sorting | 616 | 616 | 0.000252 | 0.000468 |
| horizon_two_batch / sample32_h3_legal40 | transition_grouping | 40 | 40 | 0.000444 | 0.001065 |

## Structural diagnostics

Planner instrumentation contains state-support, feedback-branch, child-support, sorting/grouping, cache, matrix eligibility, and batch-cell counters for every completed row. The Hardle-vs-position-level pattern comparison is diagnostic only and does not define planner semantics.

### sample32_h3_legal40 (horizon_two_batch)

```json
{
  "diagnostic_hardle_child_support_ratio": 2.096096096096096,
  "hardle": {
    "actions": 40,
    "branch_count_histogram": {
      "10": 4,
      "11": 4,
      "5": 2,
      "6": 3,
      "7": 6,
      "8": 10,
      "9": 11
    },
    "branch_size_histogram": {
      "1": 120,
      "10": 8,
      "11": 3,
      "12": 5,
      "13": 4,
      "14": 4,
      "2": 43,
      "3": 32,
      "4": 20,
      "5": 27,
      "6": 24,
      "7": 17,
      "8": 15,
      "9": 11
    },
    "mean_branches_per_action": 8.325,
    "mean_child_support_per_branch": 3.843843843843844,
    "support": 32
  },
  "wordle_pattern_diagnostic": {
    "actions": 40,
    "branch_count_histogram": {
      "10": 1,
      "12": 2,
      "13": 4,
      "14": 3,
      "15": 4,
      "16": 2,
      "17": 4,
      "18": 5,
      "19": 3,
      "20": 2,
      "21": 4,
      "22": 1,
      "23": 3,
      "24": 2
    },
    "branch_size_histogram": {
      "1": 445,
      "10": 2,
      "13": 2,
      "14": 1,
      "2": 131,
      "3": 48,
      "4": 26,
      "5": 16,
      "6": 14,
      "7": 7,
      "8": 2,
      "9": 4
    },
    "mean_branches_per_action": 17.45,
    "mean_child_support_per_branch": 1.833810888252149,
    "support": 32
  }
}
```

## Boundary

Largest completed row: `curated2315_h2_fulllegal` / `horizon_two_scalar` / support=2315 / horizon=2`
