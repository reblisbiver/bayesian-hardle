# ISSUE-013 horizon-2 bounds and exact child fusion

The capacity bound is mathematically safe but analysis-only: its strict skip count is recorded as zero because the support=500 replay found no useful skips. The fused variant shares exact ragged matrix work across bounded H2 child blocks. A timeout is a bounded observation, not a feasibility claim.

| Case | Variant | Status | Support | Legal | Total s | Select s | Root actions | Branches | Child requests | Exact child H2 | Bound skips | H2 cells | Blocks | Block children | Block cells | Peak temp B | Root prune | Selected |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| sample32_h3_legal40 | issue012_control | completed | 32 | 40 | 0.010 | 0.009 | 40 | 84 | 81 | 60 | 0 | 19600 | 0 | 0 | 0 | 0 | 0.925 | stage |
| sample32_h3_legal40 | fused_child_batch | completed | 32 | 40 | 0.014 | 0.013 | 40 | 119 | 116 | 95 | 0 | 29760 | 49 | 95 | 29760 | 5568 | 0.925 | stage |
| sample50_h3_legal58 | issue012_control | completed | 50 | 58 | 0.021 | 0.021 | 58 | 121 | 117 | 99 | 0 | 71978 | 0 | 0 | 0 | 0 | 0.9310344827586207 | crone |
| sample50_h3_legal58 | fused_child_batch | completed | 50 | 58 | 0.027 | 0.026 | 58 | 161 | 157 | 138 | 0 | 96570 | 70 | 138 | 96570 | 8632 | 0.9310344827586207 | crone |
| sample100_h3_legal108 | issue012_control | completed | 100 | 108 | 0.131 | 0.130 | 108 | 361 | 358 | 346 | 0 | 806112 | 0 | 0 | 0 | 0 | 0.9722222222222222 | forte |
| sample100_h3_legal108 | fused_child_batch | completed | 100 | 108 | 0.166 | 0.165 | 108 | 409 | 406 | 393 | 0 | 866916 | 198 | 393 | 866916 | 20376 | 0.9722222222222222 | forte |
| sample200_h3_legal208 | issue012_control | completed | 200 | 208 | 0.495 | 0.493 | 208 | 867 | 864 | 848 | 0 | 6938256 | 0 | 0 | 0 | 0 | 0.9855769230769231 | tower |
| sample200_h3_legal208 | fused_child_batch | completed | 200 | 208 | 0.614 | 0.612 | 208 | 973 | 970 | 954 | 0 | 7257536 | 479 | 954 | 7257536 | 53216 | 0.9855769230769231 | tower |
| sample500_h3_legal508 | issue012_control | completed | 500 | 508 | 6.014 | 6.007 | 508 | 2800 | 2795 | 2761 | 0 | 116431060 | 0 | 0 | 0 | 0 | 0.9901574803149606 | baler |
| sample500_h3_legal508 | fused_child_batch | completed | 500 | 508 | 7.169 | 7.163 | 508 | 3087 | 3082 | 3048 | 0 | 119111268 | 1534 | 3048 | 119111268 | 256484 | 0.9901574803149606 | baler |
| sample750_h3_legal758 | issue012_control | completed | 750 | 758 | 16.154 | 16.141 | 758 | 4520 | 4514 | 4452 | 0 | 395096888 | 0 | 0 | 0 | 0 | 0.9920844327176781 | crate |
| sample750_h3_legal758 | fused_child_batch | completed | 750 | 758 | 19.400 | 19.387 | 758 | 4941 | 4935 | 4873 | 0 | 402861082 | 2458 | 4873 | 402861082 | 521622 | 0.9920844327176781 | crate |
| sample1000_h3_legal1008 | issue012_control | completed | 1000 | 1008 | 41.635 | 41.612 | 1008 | 6381 | 6378 | 6322 | 0 | 948945312 | 0 | 0 | 0 | 0 | 0.9970238095238095 | stale |
| sample1000_h3_legal1008 | fused_child_batch | completed | 1000 | 1008 | 45.867 | 45.843 | 1008 | 6883 | 6880 | 6824 | 0 | 962526096 | 3437 | 6824 | 962526096 | 919008 | 0.9970238095238095 | stale |
| curated2315_h3_fulllegal | issue012_control | timed_out | 2315 | 12974 | 45.015 | - | - | - | - | - | 0 | - | - | - | - | - | - | - |
| curated2315_h3_fulllegal | fused_child_batch | timed_out | 2315 | 12974 | 45.014 | - | - | - | - | - | 0 | - | - | - | - | - | - | - |

## Interpretation

- `h2_matrix_cells` is the exact child H2 logical work; `child_batch_matrix_cells` is the same logical work observed through the fused path, not padded cells.
- `child_h2_exact_solves` counts child states whose H2 values were actually computed, excluding cache/closed-form-only children.
- `bound_only_skips` is zero because the capacity bound was not promoted into the planner after the measured zero-skip result; no work is claimed as avoided by the bound.
- `root_pruning_ratio` is exact branch-and-bound over fully traced completed rows; bounded full-support traces may have limited root audit records.

## Profile buckets

| Run | Bucket | Calls | Internal s | Cumulative s |
|---|---|---:|---:|---:|
| issue012_control / sample100_h3_legal108 | cache_key_handling | 2248 | 0.001260 | 0.013985 |
| issue012_control / sample100_h3_legal108 | exact_matrix_batch | 3470 | 0.011388 | 0.053925 |
| issue012_control / sample100_h3_legal108 | posterior_construction | 1074 | 0.002130 | 0.008823 |
| issue012_control / sample100_h3_legal108 | recursive_child_state_expansion | 1043 | 0.028239 | 0.349402 |
| issue012_control / sample100_h3_legal108 | root_ordering | 2 | 0.000022 | 0.000599 |
| issue012_control / sample100_h3_legal108 | root_partition_or_transition_grouping | 108 | 0.002516 | 0.005737 |
| fused_child_batch / sample100_h3_legal108 | cache_key_handling | 1330 | 0.000632 | 0.006159 |
| fused_child_batch / sample100_h3_legal108 | exact_child_block_batch | 198 | 0.035923 | 0.076929 |
| fused_child_batch / sample100_h3_legal108 | exact_matrix_batch | 25918 | 0.002685 | 0.014970 |
| fused_child_batch / sample100_h3_legal108 | posterior_construction | 1218 | 0.002395 | 0.010008 |
| fused_child_batch / sample100_h3_legal108 | recursive_child_state_expansion | 746 | 0.003215 | 0.329989 |
| fused_child_batch / sample100_h3_legal108 | root_ordering | 2 | 0.000022 | 0.000591 |
| fused_child_batch / sample100_h3_legal108 | root_partition_or_transition_grouping | 108 | 0.002498 | 0.005736 |
| issue012_control / sample500_h3_legal508 | cache_key_handling | 17228 | 0.019654 | 0.515148 |
| issue012_control / sample500_h3_legal508 | exact_matrix_batch | 27620 | 0.347791 | 2.015557 |
| issue012_control / sample500_h3_legal508 | posterior_construction | 8385 | 0.039830 | 0.251861 |
| issue012_control / sample500_h3_legal508 | recursive_child_state_expansion | 7077 | 2.603332 | 17.023274 |
| issue012_control / sample500_h3_legal508 | root_ordering | 2 | 0.000078 | 0.003620 |
| issue012_control / sample500_h3_legal508 | root_partition_or_transition_grouping | 508 | 0.045561 | 0.094453 |
| fused_child_batch / sample500_h3_legal508 | cache_key_handling | 9738 | 0.009177 | 0.155725 |
| fused_child_batch / sample500_h3_legal508 | exact_child_block_batch | 1534 | 1.458187 | 2.938635 |
| fused_child_batch / sample500_h3_legal508 | exact_matrix_batch | 814364 | 0.058527 | 0.439085 |
| fused_child_batch / sample500_h3_legal508 | posterior_construction | 9246 | 0.040726 | 0.302727 |
| fused_child_batch / sample500_h3_legal508 | recursive_child_state_expansion | 4603 | 0.051902 | 14.366523 |
| fused_child_batch / sample500_h3_legal508 | root_ordering | 2 | 0.000069 | 0.003350 |
| fused_child_batch / sample500_h3_legal508 | root_partition_or_transition_grouping | 508 | 0.044087 | 0.092002 |

## Frontier

Largest completed exact horizon-3 row: `sample1000_h3_legal1008` / `issue012_control` with support=1000, legal=1008.
The curated 2,315 × 12,974 h=3 probe is explicitly bounded; timeout rows are not feasibility claims.
