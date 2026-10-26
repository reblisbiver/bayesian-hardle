# ISSUE-012 horizon-3 root decomposition and exact pruning

All planner values use the accepted exact Hardle semantics and lexicographic objective. `issue011_order` is the pre-ISSUE-012 ordering control; `issue012_proxy_order` adds one exact h=2 matrix proxy for order only. A timeout is a bounded observation, not a feasibility claim.

| Case | Variant | Status | Support | Legal | Total s | Matrix s | Select s | States | Actions | Branches | Root branches/action | Child requests | Distinct | Reuse ratio | h2 cells | Root prune ratio | Matrix bytes | Selected |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| sample32_h3_legal40 | issue011_order | completed | 32 | 40 | 0.012 | 0.004 | 0.008 | 83 | 2600 | 89 | 8.32 | 84 | 82 | 0.024 | 20680 | 0.875 | 1280 | stage |
| sample32_h3_legal40 | issue012_proxy_order | completed | 32 | 40 | 0.008 | 0.000 | 0.008 | 80 | 2440 | 84 | 8.32 | 81 | 79 | 0.025 | 19600 | 0.925 | 1280 | stage |
| sample50_h3_legal58 | issue011_order | completed | 50 | 58 | 0.017 | 0.000 | 0.016 | 116 | 5858 | 123 | 9.40 | 117 | 115 | 0.017 | 72384 | 0.897 | 2900 | crone |
| sample50_h3_legal58 | issue012_proxy_order | completed | 50 | 58 | 0.017 | 0.001 | 0.016 | 115 | 5800 | 121 | 9.40 | 117 | 114 | 0.026 | 71978 | 0.931 | 2900 | crone |
| sample100_h3_legal108 | issue011_order | completed | 100 | 108 | 0.129 | 0.001 | 0.128 | 358 | 37584 | 361 | 10.01 | 357 | 357 | 0.000 | 813564 | 0.963 | 10800 | forte |
| sample100_h3_legal108 | issue012_proxy_order | completed | 100 | 108 | 0.126 | 0.001 | 0.126 | 359 | 37476 | 361 | 10.01 | 358 | 358 | 0.000 | 806112 | 0.972 | 10800 | forte |
| sample200_h3_legal208 | issue011_order | completed | 200 | 208 | 0.514 | 0.002 | 0.512 | 939 | 190944 | 952 | 11.48 | 942 | 938 | 0.004 | 7119840 | 0.952 | 41600 | tower |
| sample200_h3_legal208 | issue012_proxy_order | completed | 200 | 208 | 0.579 | 0.002 | 0.577 | 862 | 176592 | 867 | 11.48 | 864 | 861 | 0.003 | 6938256 | 0.986 | 41600 | tower |
| sample500_h3_legal508 | issue011_order | completed | 500 | 508 | 5.258 | 0.019 | 5.239 | 2793 | 1412240 | 2819 | 12.80 | 2811 | 2792 | 0.007 | 116515388 | 0.984 | 254000 | baler |
| sample500_h3_legal508 | issue012_proxy_order | completed | 500 | 508 | 5.067 | 0.007 | 5.060 | 2776 | 1403096 | 2800 | 12.80 | 2795 | 2775 | 0.007 | 116431060 | 0.990 | 254000 | baler |
| curated2315_h3_fulllegal | issue011_order | timed_out | 2315 | 12974 | 45.014 | - | - | - | - | - | - | - | - | - | - | - | - | - |
| curated2315_h3_fulllegal | issue012_proxy_order | timed_out | 2315 | 12974 | 45.013 | - | - | - | - | - | - | - | - | - | - | - | - | - |

## Interpretation

- `horizon_two_batch_matrix_cells` is child h=2 work; root ordering proxy cells are reported separately in planner instrumentation and are not counted as child solves.
- `root_child_reuse_ratio` counts repeated exact canonical child-state keys across feedback branches and root guesses. The planner already has exact canonical memoization; a new cache is not added merely because a duplicate exists.
- Root pruning is exact branch-and-bound only. Ordering changes visit order and incumbent timing; it does not remove candidates or change the result.
- Root partition, child h=2, cache/key, pruning, and proxy timings are in each completed row's `root_summary.timing_seconds`.

## Hardle structural diagnostic

### issue011_order / sample32_h3_legal40

```json
{
  "hardle": {
    "actions": 40,
    "mean_branches_per_action": 8.325,
    "mean_child_support_per_branch": 3.843843843843844,
    "support": 32
  },
  "hardle_to_position_child_support_ratio": 2.096096096096096,
  "position_pattern_diagnostic": {
    "actions": 40,
    "mean_branches_per_action": 17.45,
    "mean_child_support_per_branch": 1.833810888252149,
    "support": 32
  }
}
```

### issue012_proxy_order / sample32_h3_legal40

```json
{
  "hardle": {
    "actions": 40,
    "mean_branches_per_action": 8.325,
    "mean_child_support_per_branch": 3.843843843843844,
    "support": 32
  },
  "hardle_to_position_child_support_ratio": 2.096096096096096,
  "position_pattern_diagnostic": {
    "actions": 40,
    "mean_branches_per_action": 17.45,
    "mean_child_support_per_branch": 1.833810888252149,
    "support": 32
  }
}
```

## Profile buckets

| Run | Bucket | Calls | Internal s | Cumulative s |
|---|---|---:|---:|---:|
| issue011_order / sample100_h3_legal108 | cache_key_handling | 2244 | 0.001181 | 0.013273 |
| issue011_order / sample100_h3_legal108 | exact_matrix_batch | 3470 | 0.010972 | 0.051554 |
| issue011_order / sample100_h3_legal108 | posterior_construction | 1071 | 0.002214 | 0.009134 |
| issue011_order / sample100_h3_legal108 | recursive_child_state_expansion | 1041 | 0.026483 | 0.333940 |
| issue011_order / sample100_h3_legal108 | root_ordering | 1 | 0.000006 | 0.000036 |
| issue011_order / sample100_h3_legal108 | root_partition_or_transition_grouping | 108 | 0.002450 | 0.005517 |
| issue012_proxy_order / sample100_h3_legal108 | cache_key_handling | 2248 | 0.001198 | 0.012762 |
| issue012_proxy_order / sample100_h3_legal108 | exact_matrix_batch | 3470 | 0.010843 | 0.049415 |
| issue012_proxy_order / sample100_h3_legal108 | posterior_construction | 1074 | 0.002214 | 0.008983 |
| issue012_proxy_order / sample100_h3_legal108 | recursive_child_state_expansion | 1043 | 0.028647 | 0.331628 |
| issue012_proxy_order / sample100_h3_legal108 | root_ordering | 2 | 0.000023 | 0.000586 |
| issue012_proxy_order / sample100_h3_legal108 | root_partition_or_transition_grouping | 108 | 0.002397 | 0.005424 |

## Frontier

Largest completed horizon-3 row: `sample500_h3_legal508` / `issue011_order` with support=500, legal=508.
The curated 2,315 x 12,974 probe is explicitly bounded; its row records timeout rather than feasibility unless a worker completes it.
