# ISSUE-022 — Exact uniform-H3 branch-capacity pruning before child H2 solves

Status: `READY_FOR_REVIEW` — executor evidence only. No supervisor acceptance
is claimed.

## Scope

Validate and integrate the exact branch-capacity upper bound for a uniform
five-letter Hardle root posterior at `remaining_guesses == 3`. The change must
leave weighted/nonuniform semantics, branch ordering, and deterministic tie
handling unchanged. The formal proof and boundary analysis are in
`docs/research/issue_022_uniform_h3_branch_capacity.md`.

## Git boundary

The requested base `a37a22f7a795c7a3434283e204cb860db8f95f0d` is absent from the
local Git object database. This work was isolated in
`/private/tmp/bayesian-hardle-issue-022` on branch
`codex/issue-022-uniform-h3-capacity`, based on visible commit
`9ac070cb49b15392da1e5e1dffc22da6c7ec9ed5`. The mismatch is recorded rather
than silently normalized.

## Implementation

- Added opt-in/default layer `uniform_h3_branch_capacity`.
- Eligibility is strict: standard five-letter `HardleFeedbackEngine`, H3, and
  normalized root mass exactly uniform. All other states retain the former
  `success_so_far + (1 - processed_probability)` upper bound.
- Root partition support sizes produce integer capacity units: `1` for a win
  branch and `min(36, n)` for a non-win child. Units are summed once and
  decremented O(1) per processed branch.
- The lexicographic prune comparator and `POLICY_TIE_TOLERANCE` are unchanged;
  equality remains live for expected-guesses and deterministic tie rank.
- Added root action / child H2 / matrix-cell instrumentation needed for paired
  evidence.

## Tests and benchmark evidence

The new test module covers child sizes below/at/above 36, winning and absent
winning branches, duplicate-letter supports, actual H2 values versus the
capacity bound, weighted fallback, equality/tie tolerance, and reference
selection/value equivalence. Fresh full-suite evidence on this branch:

```
PYTHONPATH=src PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue022-pycache \
python3 -m unittest discover -s tests -v
110 passed, 9 skipped
```

The paired artifact is
`experiments/results/issue_022_uniform_h3_capacity.json` with compact report
`experiments/results/issue_022_uniform_h3_capacity_summary.md`.

Completed exact-equivalent pairs:

| Support | Control wall s | After wall s | Child matrix cells control → after | Selected |
|---:|---:|---:|---:|---|
| 500 | 5.181 | 5.069 | 116,431,060 → 115,334,288 | `baler` |
| 1000 | 39.520 | 37.401 | 948,945,312 → 936,532,800 | `stale` |
| 1250 | 82.040 | 80.573 | 1,859,261,100 → 1,836,082,450 | `trace` |
| 1500 | 266.906 | 271.381 | 3,219,727,784 → 3,178,512,636 | `stale` |

The result is mixed: a local wall-clock win at 500/1000/1250 and a regression
at 1500. Both variants timed out at the declared bounded windows for 1750,
2000, and curated `2315 × 12974` (45s), so there is no exact curated selected
guess/value and no fresh confirmation run. On completed real rows,
`pruned_before_first_child` was `0`; capacity pruned 503/1005/1255/1506 root
actions after child work. A separate 44s partial curated artifact,
`experiments/results/issue_022_curated_progress.json`, recorded control 12/4
root started/completed and after 10/4, with 137 versus 116 child H2 solves and
335,429,796 versus 277,721,444 matrix cells. It did not produce an exact
selection/value.

## Verification boundary

- `PROJECT_STATE.md` was not modified.
- No supervisor acceptance is claimed; this handoff is pending independent
  `[SUPERVISOR REVIEW]`.
- All timings are local machine evidence. No remote, live, device, business,
  or external acceptance is claimed.
