# ISSUE-013 — Horizon-2 child bounds and exact batch fusion

## Status

`READY_FOR_REVIEW` — executor evidence only. Independent SUPERVISOR review is
required. `project-control/PROJECT_STATE.md` is unchanged.

## Execution boundary

- Branch: `codex/issue-013-horizon2-bounds-batch`
- Worktree: `/private/tmp/bayesian-hardle-issue-013`
- Base: `34d4e58fdf940c40ca8a6a1f134e8a1125c573ae`
  (`codex/issue-012-horizon3-root-audit`)
- Implementation checkpoints: `f6428bc`, `465b240`, `93c57a6`, `aa59c10`
- `PROJECT_STATE.md` SHA-256 before and after: `16df9822c1b9267ae20d0f93c7aad5ac7b56b5732827b7c88e63230a3efce825`
- Canonical checkout was not modified.

## What changed

- Added an exact-safe H2 capacity upper bound and per-action bound helper.
  The proof is recorded in
  `docs/superpowers/specs/2026-10-26-issue-013-horizon2-bounds-batch-design.md`:
  at most 36 Hardle feedback codes can each contribute one legal final-answer
  mass, so the top-36 legal posterior masses upper-bound every H2 probe.
- Added weighted/adversarial bound tests, including duplicate-letter feedback,
  legal-final-answer filtering, and root branch-weighted upper-bound checks.
- Added an exact ragged H2 block evaluator. It gathers uint8 codes once for a
  bounded child block and reduces `child_id * code_count + feedback_code`
  slots without padding child supports. Block values match scalar matrix and
  reference planner values within `1e-12`.
- Added explicit opt-in `horizon_two_child_batch` planner integration,
  block/child/cell/memory/exact-solve instrumentation, and deterministic tie
  handling. The default planner deliberately excludes this layer after the
  fresh net-benefit measurement.
- Added the deterministic measurement driver, JSON/Markdown summary, and
  cProfile artifacts.

## Bound result

The capacity bound is exact-safe but too loose on the measured distribution.
The support=500 replay produced zero strict child-action skips and zero strict
root-action skips. The planner therefore reports `bound_only_skips=0` and does
not use the bound to remove work. No bound-based speedup is claimed.

## Before/after result

All seven completed ladder pairs selected the same action and had equal exact
values within `1e-12`. The fused path was slower in every pair because exact
branch-and-bound can only run after a bounded block flush, so it evaluates
extra child branches before proving an action noncompetitive.

| Support | Legal | Control select s | Fused select s | Control H2 cells | Fused H2 cells | Fused peak temp B |
|---:|---:|---:|---:|---:|---:|---:|
| 32 | 40 | 0.009 | 0.013 | 19,600 | 29,760 | 5,568 |
| 50 | 58 | 0.021 | 0.026 | 71,978 | 96,570 | 8,632 |
| 100 | 108 | 0.130 | 0.165 | 806,112 | 866,916 | 20,376 |
| 200 | 208 | 0.493 | 0.612 | 6,938,256 | 7,257,536 | 53,216 |
| 500 | 508 | 6.007 | 7.163 | 116,431,060 | 119,111,268 | 256,484 |
| 750 | 758 | 16.141 | 19.387 | 395,096,888 | 402,861,082 | 521,622 |
| 1000 | 1008 | 41.612 | 45.843 | 948,945,312 | 962,526,096 | 919,008 |

At support=500, the exact child-H2 term remains dominant, but fusion moves
work into `horizon_two_values_block` without reducing total logical cells;
the measured wall time increases by about 19%. This is why the opt-in layer
is not promoted into the default planner. Root prune ratios were equal in all
completed pairs; the difference is delayed pruning, not changed semantics.

## Scaling boundary

The largest completed exact horizon-3 row is support `1000` × legal `1008`.
The curated support `2315` × legal `12974` × horizon `3` probe used a declared
45-second budget for both variants and timed out at approximately 45.0s. No
full 2315/horizon-3 feasibility claim is made.

## Evidence

- Design: `docs/superpowers/specs/2026-10-26-issue-013-horizon2-bounds-batch-design.md`
- Plan: `docs/superpowers/plans/2026-10-26-issue-013-horizon2-bounds-batch.md`
- Machine-readable artifact: `experiments/results/issue_013_horizon2_bounds_batch.json`
- Markdown summary: `experiments/results/issue_013_horizon2_bounds_batch_summary.md`
- Profiles: `experiments/results/issue_013_profiles/`

## Verification

- Fresh full suite: `92` passed, `9` skipped.
- `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue013-task4-compile-pycache python3 -m compileall -q src tests experiments` — passed.
- Artifact validator — passed: `14` completed rows, `2` bounded curated timeouts.
- Completed control/fused equivalence validator — passed: `7` pairs, selected guesses and values equal within `1e-12`.
- `git diff --check` — passed before the handoff edit.
- Package import/version check and final boundary checks remain to be rerun after this handoff commit.

## Remaining boundary

This is executor evidence awaiting `[SUPERVISOR REVIEW]`; no accepted-state
advance, remote/live/device/business acceptance, or algorithm acceptance is
claimed. The exact fused evaluator remains available only through its explicit
optimization layer for future workloads; current evidence supports keeping it
disabled by default.
