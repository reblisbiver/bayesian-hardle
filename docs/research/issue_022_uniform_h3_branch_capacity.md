# ISSUE-022 — Exact uniform-H3 branch-capacity pruning

Status: `IMPLEMENTED — REPRODUCIBLE_LOCAL_RESULT`. This is local reproducibility
evidence; no external validation is claimed and
The solver state contract is unchanged.

The requested ISSUE-021 base `a37a22f7a795c7a3434283e204cb860db8f95f0d` is not
present in this checkout's Git object database. The isolated worktree uses the
nearest visible H3/B&B baseline, `9ac070cb49b15392da1e5e1dffc22da6c7ec9ed5`.
The benchmark artifact records both SHAs explicitly.

## The exact bound

Let the root posterior have support `S` of size `N` and be uniform, so each
hidden answer has mass `1/N`. A root action partitions `S` into feedback
branches `B_i` with support size `n_i = |B_i|`. The branch probability is
`n_i/N`.

For a non-winning branch, deterministic filtering preserves uniformity: the
child posterior assigns mass `1/n_i` to every answer in `B_i`. At H2, fix any
first child action. Its feedback partitions `B_i` into at most `K` buckets,
where `K=36` for the five-letter Hardle feedback encoding. On the final guess,
each bucket can contribute at most one answer's posterior mass, because the
policy chooses one final guess after observing that bucket. Therefore

```
child_success_i <= min(K, n_i) / n_i.
```

Multiplying by the root branch probability cancels the child support size:

```
root_contribution_i
    <= (n_i / N) * min(K, n_i) / n_i
    =  min(K, n_i) / N.
```

For a winning root branch, the feedback is all exact. Under the deterministic
Hardle semantics its support contains only the guessed answer, so the branch
solves immediately and contributes exactly `1/N`; it does not require an H2
solve. The implementation represents this as one capacity unit, while a
non-winning branch contributes `min(36, n_i)` units.

After a root action has processed branches `P`, let `s_P` be the exact success
contribution accumulated so far. The safe remaining-success upper bound is

```
U = s_P + (1/N) * sum(i not in P, c_i)

c_i = 1                 if branch i is winning
      min(36, n_i)       otherwise.
```

The capacity sum is constructed once from the existing root partition and is
then decremented by one integer `c_i` as each branch is processed. Thus the
bound is O(number of root branches) once per root action and O(1) per branch
update; it does not inspect child H2 metadata. Integer units also avoid
accumulated subtraction error. The final float upper bound is nudged upward by
one representable float before comparison, so rounding cannot turn it into a
lower bound.

## Lexicographic objective and tie tolerance

The planner compares `(success probability, expected guesses)`
lexicographically. Its current partial expected value is initialized at one
root guess and adds only already processed non-winning child contributions:

```
E_low = 1 + sum(processed non-winning i) p_i * E_i.
```

Unprocessed continuation costs are non-negative, so `E_low` is a valid lower
bound on the eventual expected-guesses component. A winning branch adds no
continuation cost because it terminates immediately.

The existing `_cannot_beat_incumbent` rule is retained unchanged:

1. prune if `U < incumbent_success - tolerance`;
2. when `U` is tied with incumbent success within
   `POLICY_TIE_TOLERANCE`, prune only if
   `E_low > incumbent_expected + POLICY_TIE_TOLERANCE`;
3. keep equality cases alive, so deterministic action order and the existing
   final tie rank remain unchanged.

The capacity bound is checked immediately after root partitioning. This can
return `None` before the first child H2 solve. Later checks use the same bound
after each processed branch. The bound never changes branch order.

## Eligibility and fallback boundary

The specialization is enabled only when all of the following hold:

- the optimization layer is enabled;
- `remaining_guesses == 3`;
- the feedback engine is the exact five-letter `HardleFeedbackEngine`;
- the normalized root mass is strictly uniform.

Strict equality is intentional. An explicitly weighted belief that is merely
near-uniform is not treated as uniform, because doing so could make the bound
unsound. Weighted/nonuniform roots, non-H3 states, non-five-letter engines,
and all other paths retain the prior bound
`success_so_far + (1 - processed_probability)`.

## Evidence added

- `src/bayesian_hardle/decision.py`: opt-in/default exact-safe layer,
  integer capacity accounting, and root/action counters.
- `tests/test_issue_022_uniform_h3_capacity.py`: capacity-unit edge cases,
  actual duplicate-aware child partitions, winning and absent winning branches,
  supports below/above 36, reference equivalence, weighted fallback, and tie
  tolerance.
- `experiments/issue_022_uniform_h3_capacity.py`: paired control/after runs
  for support `500/1000/1250/1500/1750/2000` plus bounded curated
  `2315 × 12974` H3, with a fresh curated confirmation if the first after run
  completes within 45 seconds.
- `experiments/results/issue_022_uniform_h3_capacity.json` and
  `issue_022_uniform_h3_capacity_summary.md`: machine-readable and compact
  benchmark evidence, when generated.

## Paired benchmark result

The first paired run completed 8 of 14 rows. The completed rows preserved the
selected guess and both value components within `1e-12`:

| Support | Control wall s | After wall s | Matrix-cell change | Selected | Value |
|---:|---:|---:|---:|---|---|
| 500 | 5.181 | 5.069 | 116,431,060 → 115,334,288 | `baler` | `(0.262, 2.972)` |
| 1000 | 39.520 | 37.401 | 948,945,312 → 936,532,800 | `stale` | `(0.165, 2.987)` |
| 1250 | 82.040 | 80.573 | 1,859,261,100 → 1,836,082,450 | `trace` | `(0.14, 2.988)` |
| 1500 | 266.906 | 271.381 | 3,219,727,784 → 3,178,512,636 | `stale` | `(0.12266666666666669, 2.99)` |

Thus the measured wall-clock result is mixed: a real local win at supports
500/1000/1250, a regression at 1500, and no completion within the declared
windows for paired 1750, 2000, or curated `2315 × 12974` (45s). The curated
row therefore has no exact selected guess/value and no confirmation run.
On completed rows, capacity pruned 503/1005/1255/1506 root actions after
child work; `pruned_before_first_child` was zero in all four paired rows.
The separate adversarial unit test demonstrates that immediate pre-child
pruning is possible when an incumbent already dominates the aggregate
capacity, but it was not observed in these real completed benchmark roots.

The separate 44s signal-partial curated probe recorded progress before the
deadline (not an exact completion):

| Variant | Root actions started/completed | Pruned before child | Child H2 exact solves | Matrix cells | Selected/value |
|---|---:|---:|---:|---:|---|
| control | 12 / 4 | 0 | 137 | 335,429,796 | unavailable |
| after | 10 / 4 | 0 | 116 | 277,721,444 | unavailable |

This is a partial-progress ratio of `4/12` versus `4/10` completed root
actions at 44s, with after doing fewer child H2 solves and cells. It does not
prove the curated action selection or value, and the original 45s paired rows
remain `timed_out`.

The benchmark must be interpreted in evidence layers: local exact tests and
local wall-clock measurements do not constitute remote, live, business, or
external validation.
