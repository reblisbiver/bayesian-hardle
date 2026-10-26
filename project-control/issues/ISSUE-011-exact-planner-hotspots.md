# ISSUE-011 — Exact planner hotspot research and next scaling step

## Status

`READY_FOR_REVIEW` — executor evidence only; independent SUPERVISOR review is
required. No accepted project state is advanced by this handoff.

## Execution boundary

- Branch: `codex/issue-011-exact-planner-hotspots`
- Worktree: `.worktrees/issue-011-exact-planner-hotspots`
- Base: `a9f251a321b2fdf2cfd2911a01b1b9b7c23aa17c` (`codex/issue-010-exact-scaling`)
- Result checkpoint before this handoff: `b42f130`
- Canonical checkout: unchanged
- `project-control/PROJECT_STATE.md`: unchanged; SHA-256
  `16df9822c1b9267ae20d0f93c7aad5ac7b56b5732827b7c88e63230a3efce825`

## What changed

- Added the exact scalar horizon-2 value formula to the planner as an
  independently selectable `horizon_two_closed_form` layer.
- Added `ExactFeedbackCodeMatrix.horizon_two_values`, an exact matrix batch
  evaluator using per-feedback-code legal-candidate maxima, and wired it as
  `horizon_two_batch` only for compatible Hardle matrix semantics.
- Reused one normalized mass table and one matrix-eligibility decision through
  transition and posterior construction; public `BeliefState` observations
  remain unchanged.
- Added proof-oriented scalar/reference tests, duplicate-letter batch tests,
  deterministic random weighted equivalence, structural histograms, and
  matrix-eligibility reuse regression coverage.
- Added a deterministic ISSUE-011 benchmark/profiling driver, support 32/50/
  100/200/500 horizon-2 cases, a support-32 horizon-3 case, full curated
  2,315 × 12,974 probes, JSON/Markdown artifacts, and cProfile outputs.

## Exactness result

For horizon 2 and first guess `g`, with normalized state mass `p(w)` and
feedback branch `B_o(g)`:

```
success(g) = sum_o max({p(w): w in B_o(g) and w is legal}, default=0)
expected(g) = 2 - p(g)
```

The winning branch contributes `p(g)`. Every non-winning branch has one final
guess and contributes its largest legal candidate mass. The expected value is
`1 + P(first guess does not solve)`, because the second guess is always taken
after a non-winning first guess. The scalar formula matches the reference
planner on 32 deterministic random weighted states/action values and the
batch path matches scalar/reference selections on 24 duplicate-aware random
states.

## Benchmark result

Evidence paths:

- `experiments/results/issue_011_exact_hotspots.json`
- `experiments/results/issue_011_exact_hotspots_summary.md`
- `experiments/results/issue_011_profiles/`

The driver recorded 51 bounded rows: 50 completed and one explicit timeout.
The curated 2,315-support × 12,974-legal horizon-2 root now completed exactly
with the batch path in about 1.17 seconds total in the final run, including
about 0.55 seconds of uint8 matrix construction. The same exact scalar formula
without the batch path completed in about 15.09 seconds total. The old
ISSUE-010 recursive path timed out at its 30-second bound. This is a measured
exact completion for horizon 2, not a claim about horizon 3 or deeper full
support planning.

The deterministic support-500/horizon-2 row completed in about 0.011 seconds.
The support-32/horizon-3 row completed in about 0.012 seconds with the batch
shortcut; it retained exact branch-and-bound and matched the reference on the
covered states. The diagnostic Hardle-vs-position-level feedback comparison is
explicitly non-semantic: on the support-32 sample it measured a Hardle mean
child-support-per-branch about 2.10 times the position-pattern diagnostic.

The profile breakdown identifies the pre-change hotspots (`_mass_table`,
`_canonical_key`, `_can_use_matrix`, transitions, posterior construction,
recursion, cache, sorting/grouping) and the post-change shift to exact
finite-code NumPy batches plus remaining recursive state expansion. An
internal immutable state rewrite, alternative matrix partition, and stronger
branch bound were deferred because the new horizon-2 path removes the practical
frontier and the representative deeper profile does not yet justify their
semantic risk.

## Fresh verification

- `PYTHONPATH=src PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue011-final-pycache python3 -m unittest discover -s tests -v` — 85 passed, 9 skipped.
- `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue011-final-pycache python3 -m compileall -q src tests experiments` — passed.
- `PYTHONPATH=src python3 -c 'import bayesian_hardle; assert bayesian_hardle.__version__ == "0.1.0"'` — passed.
- JSON/Markdown artifact validator — passed: 51 rows, 50 completed, one timeout, full 2,315/horizon-2 batch row and 30,034,810 matrix cells recorded.
- `git diff --check` — passed.

## Commits

- `8caefdc` — failing horizon-2 formula tests
- `5fc7a9f` — exact scalar horizon-2 evaluator
- `158696d` — exact matrix batch evaluator
- `d662eb1` — matrix eligibility reuse regression test
- `590b264` — structural planner counters test
- `09d847e` — mass/eligibility reuse and instrumentation
- `a1b1bcd` — design, plan, benchmark driver, artifacts, and profiles
- `b42f130` — instrumentation type correction

Remaining unknowns are deeper-horizon full-support scaling, any remote/live
acceptance, and independent supervisor review.
