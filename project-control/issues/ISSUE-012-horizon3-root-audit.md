# ISSUE-012 — Horizon-3 root decomposition, reuse audit, and exact pruning

## Status

`READY_FOR_REVIEW` — executor evidence only. Independent SUPERVISOR review is
required; `project-control/PROJECT_STATE.md` is unchanged.

## Execution boundary

- Branch: `codex/issue-012-horizon3-root-audit`
- Worktree: `/private/tmp/bayesian-hardle-issue-012`
- Base: `36561c1d0d9bfc9d000de3bdd82c13939eb1c9ad`
  (`codex/issue-011-exact-planner-hotspots`)
- Result checkpoint before this handoff: `7441902`
- `PROJECT_STATE.md` SHA-256 remains
  `16df9822c1b9267ae20d0f93c7aad5ac7b56b5732827b7c88e63230a3efce825`
- Canonical checkout was not modified.

## Scope and exactness

The accepted Hardle feedback semantics, posterior normalization, finite-horizon
objective, and tie rules are unchanged. The new h=2 proxy calls the existing
exact `horizon_two_values` matrix evaluator and is used only to order h=3 root
actions. It never removes an action and is not used as a pruning bound.

Root auditing is opt-in through `root_audit=True`, with an optional positive
`root_audit_limit` for bounded probes. A completed audited h=3 root records all
first actions. Each action records total feedback branches, branch feedback,
posterior mass, child support size, processed/unprocessed status, child-state
key digest, child cache hit, h=2 batch calls/actions/cells, timing buckets,
incumbent updates, and exact-prune information. Global counters record child
state requests, distinct canonical keys, repeated requests, and cache hits.

The existing canonical planner cache is already keyed by remaining horizon,
normalized active support/masses, legal guesses, and the selected action value
key. The audit measures this exact reuse across root guesses and feedback
branches; it does not add a second cache without evidence.

## Dominant-term diagnosis

Evidence artifact:
`experiments/results/issue_012_horizon3_root_audit.json`

Summary:
`experiments/results/issue_012_horizon3_root_audit_summary.md`

On the pre-ISSUE-012 ordering control, the completed h=3 ladder reported:

| Support | Legal | Mean branches/action | Mean child support/branch | Child requests | Distinct | Reuse | h2 batch cells | Selection s |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 32 | 40 | 8.32 | 3.84 | 84 | 82 | 2.4% | 20,680 | 0.008 |
| 50 | 58 | 9.40 | 5.32 | 117 | 115 | 1.7% | 72,384 | 0.016 |
| 100 | 108 | 10.01 | 9.99 | 357 | 357 | 0.0% | 813,564 | 0.128 |
| 200 | 208 | 11.48 | 17.43 | 942 | 938 | 0.4% | 7,119,840 | 0.512 |
| 500 | 508 | 12.80 | 39.06 | 2,811 | 2,792 | 0.7% | 116,515,388 | 5.239 |

For support 500, aggregate root timing was approximately 4.77 s in child h=2
solves, 0.054 s in root partitioning, 0.195 s in cache/key handling, and
0.001 s in pruning checks. Thus the dominant exact term is repeated h=2 batch
work, not matrix construction, root partitioning, or the branch-bound check.
The low reuse ratio does not justify a new memoization scheme.

The Hardle structural diagnostic on support 32/legal 40 measured 8.325 Hardle
feedback branches/action and 3.844 child support/branch, versus 17.45 and
1.834 for the position-pattern diagnostic. The Hardle child-support ratio was
2.096. This is diagnostic only; planner semantics use Hardle feedback.

## Optimization result

Added the exact-safe `root_horizon_two_ordering` layer. It batches one exact
h=2 proxy over all root actions, then keeps remaining answer candidates before
probes and sorts within each group by proxy solve probability, proxy expected
guesses, posterior mass, and lexical order. The full action set and exact
branch-and-bound remain unchanged.

Across the five paired ladder rows, both variants selected the same guess and
had values equal within `1e-12`. The proxy reduced h=2 cells in every paired
row; the support-500 row moved from 116,515,388 to 116,431,060 cells and from
98.4% to 99.0% root-action pruning. The one-run wall-clock comparison is
reported in the JSON/Markdown artifact; it is treated as a measurement, not a
general scaling law. The proxy's own support-500 matrix work was 254,000
cells, much smaller than the child h=2 work.

No stronger root-level mathematical bound was introduced. The existing bound
is exact-safe and the reference-equivalence tests cover adversarial duplicate
letter states plus deterministic random weighted h=1–h=3 states. A stronger
bound would need to replace the unfinished-branch upper value of one with
additional exact child work; the measured profile did not establish a cheaper
certified bound with positive net benefit. Likewise, root partition batching
was profiled but not forced: at support 500 it was about 1% of selection time,
while child h=2 work was about 91%.

## Scaling boundary

The largest completed exact h=3 row is support 500 × legal 508. Its exact
matrix occupied 254,000 bytes. The curated 2,315-support × 12,974-legal h=3
probe was run in both ordering variants with a declared 45-second budget; both
timed out. This is an observed bounded frontier, not a claim that full
2,315/horizon-3 planning is feasible or infeasible beyond that budget. The
corresponding matrix dimensions are 30,034,810 uint8 cells, but no h=3 root
completion was recorded.

## Verification

- Baseline before implementation: 85 tests passed, 9 skipped.
- Fresh post-change suite: 87 tests passed, 9 skipped.
- Fresh `compileall` for `src`, `tests`, and `experiments`: passed.
- Import/version check: `bayesian_hardle.__version__ == "0.1.0"`.
- JSON artifact validator: passed; 12 runs, 10 completed paired ladder rows,
  2 explicit full-support timeouts; all completed root traces cover every
  legal first action and satisfy request = distinct + repeated.
- `git diff --check`: passed.

## Remaining frontier

- Independent SUPERVISOR review of this evidence and the exact-safe ordering
  change is pending.
- Full curated h=3 feasibility remains unknown beyond the declared 45-second
  probe; no live, remote, device, or business acceptance is claimed.

## Handoff

Status: `READY_FOR_REVIEW`

The append-only execution record is in `project-control/JOURNAL.md`.
