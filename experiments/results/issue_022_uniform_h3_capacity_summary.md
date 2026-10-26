# ISSUE-022 uniform-H3 branch-capacity pruning

Control and after use identical action/branch order and all existing exact layers; after adds only `uniform_h3_branch_capacity`. A timeout is a bounded observation, not a completion claim.

| Case | Variant | Status | Support | Legal | Wall s | Root started | Root completed | Pruned before child | Child requests | Child H2 calls | Exact H2 solves | Matrix cells | Selected | Value |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| sample500_h3_legal508 | control | completed | 500 | 508 | 5.181 | 508 | 5 | 0 | 2795 | 2761 | 2761 | 116431060 | baler | [0.26199999999999996, 2.9719999999999986] |
| sample500_h3_legal508 | after | completed | 500 | 508 | 5.069 | 508 | 5 | 0 | 2761 | 2727 | 2727 | 115334288 | baler | [0.26199999999999996, 2.9719999999999986] |
| sample1000_h3_legal1008 | control | completed | 1000 | 1008 | 39.520 | 1008 | 3 | 0 | 6378 | 6322 | 6322 | 948945312 | stale | [0.16500000000000004, 2.9869999999999997] |
| sample1000_h3_legal1008 | after | completed | 1000 | 1008 | 37.401 | 1008 | 3 | 0 | 6197 | 6141 | 6141 | 936532800 | stale | [0.16500000000000004, 2.9869999999999997] |
| sample1250_h3_legal1258 | control | completed | 1250 | 1258 | 82.040 | 1258 | 3 | 0 | 8614 | 8499 | 8499 | 1859261100 | trace | [0.14, 2.9879999999999995] |
| sample1250_h3_legal1258 | after | completed | 1250 | 1258 | 80.573 | 1258 | 3 | 0 | 8373 | 8258 | 8258 | 1836082450 | trace | [0.14, 2.9879999999999995] |
| sample1500_h3_legal1508 | control | completed | 1500 | 1508 | 266.906 | 1508 | 2 | 0 | 10532 | 10399 | 10399 | 3219727784 | stale | [0.12266666666666669, 2.9899999999999993] |
| sample1500_h3_legal1508 | after | completed | 1500 | 1508 | 271.381 | 1508 | 2 | 0 | 10190 | 10057 | 10057 | 3178512636 | stale | [0.12266666666666669, 2.9899999999999993] |
| sample1750_h3_legal1758 | control | timed_out | 1750 | 1758 | 420.323 | - | - | - | - | - | - | - | - | - |
| sample1750_h3_legal1758 | after | timed_out | 1750 | 1758 | 420.117 | - | - | - | - | - | - | - | - | - |
| sample2000_h3_legal2008 | control | timed_out | 2000 | 2008 | 480.105 | - | - | - | - | - | - | - | - | - |
| sample2000_h3_legal2008 | after | timed_out | 2000 | 2008 | 480.131 | - | - | - | - | - | - | - | - | - |
| curated2315_h3_fulllegal | control | timed_out | 2315 | 12974 | 45.018 | - | - | - | - | - | - | - | - | - |
| curated2315_h3_fulllegal | after | timed_out | 2315 | 12974 | 45.014 | - | - | - | - | - | - | - | - | - |

## Paired equivalence

- `curated2315_h3_fulllegal`: `not_comparable` — {'case': 'curated2315_h3_fulllegal', 'status': 'not_comparable', 'reason': 'one_or_both_bounded', 'control_status': 'timed_out', 'after_status': 'timed_out'}
- `sample1000_h3_legal1008`: `equivalent` — {'case': 'sample1000_h3_legal1008', 'status': 'equivalent', 'control_selected_guess': 'stale', 'after_selected_guess': 'stale', 'control_value': [0.16500000000000004, 2.9869999999999997], 'after_value': [0.16500000000000004, 2.9869999999999997], 'max_abs_value_delta': 0.0}
- `sample1250_h3_legal1258`: `equivalent` — {'case': 'sample1250_h3_legal1258', 'status': 'equivalent', 'control_selected_guess': 'trace', 'after_selected_guess': 'trace', 'control_value': [0.14, 2.9879999999999995], 'after_value': [0.14, 2.9879999999999995], 'max_abs_value_delta': 0.0}
- `sample1500_h3_legal1508`: `equivalent` — {'case': 'sample1500_h3_legal1508', 'status': 'equivalent', 'control_selected_guess': 'stale', 'after_selected_guess': 'stale', 'control_value': [0.12266666666666669, 2.9899999999999993], 'after_value': [0.12266666666666669, 2.9899999999999993], 'max_abs_value_delta': 0.0}
- `sample1750_h3_legal1758`: `not_comparable` — {'case': 'sample1750_h3_legal1758', 'status': 'not_comparable', 'reason': 'one_or_both_bounded', 'control_status': 'timed_out', 'after_status': 'timed_out'}
- `sample2000_h3_legal2008`: `not_comparable` — {'case': 'sample2000_h3_legal2008', 'status': 'not_comparable', 'reason': 'one_or_both_bounded', 'control_status': 'timed_out', 'after_status': 'timed_out'}
- `sample500_h3_legal508`: `equivalent` — {'case': 'sample500_h3_legal508', 'status': 'equivalent', 'control_selected_guess': 'baler', 'after_selected_guess': 'baler', 'control_value': [0.26199999999999996, 2.9719999999999986], 'after_value': [0.26199999999999996, 2.9719999999999986], 'max_abs_value_delta': 0.0}

## Bound accounting

For eligible uniform H3 roots, each non-winning child of support `n` contributes at most `min(36,n)/N` to root success; a winning branch contributes exactly `1/N`. Capacity units are summed once per root partition and decremented as branches become processed. Weighted roots, non-H3 horizons, non-5-letter engines, and other ineligible paths retain the existing `1 - processed_probability` bound.

## Curated confirmation

None

## Curated 44s partial progress (separate probe)

The paired 45s curated rows both timed out. A separate signal-partial probe
read counters at 44s; these are progress observations, not exact selected
guess/value results:

| Variant | Root started/completed | Pruned before child | Child H2 exact solves | Matrix cells | Selected/value |
|---|---:|---:|---:|---:|---|
| control | 12 / 4 | 0 | 137 | 335,429,796 | unavailable |
| after | 10 / 4 | 0 | 116 | 277,721,444 | unavailable |
