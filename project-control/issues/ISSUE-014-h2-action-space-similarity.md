# ISSUE-014 — H2 action-space structure and similarity-bound research

## Status

`READY_FOR_REVIEW` — executor evidence only. Independent SUPERVISOR review is
required. `project-control/PROJECT_STATE.md` is unchanged.

## Execution boundary

- Branch: `codex/issue-014-h2-action-similarity`
- Worktree: `/private/tmp/bayesian-hardle-issue-014`
- Base: `b50f3ba541327264e86b63137c3f37896b576dc8`
  (`codex/issue-013-horizon2-bounds-batch`)
- Canonical checkout was not modified.

## Result

The audit measured exact partition equivalence, immediate-hit effects,
refinement dominance, and total-variation similarity bounds on the ISSUE-013
H3 child distribution. No planner optimization was justified by the measured
dominant work, so no planner/default-layer change was made.

- Safe action collapse key: unlabeled partition plus immediate-hit posterior
  mass. Partition-only collapse is unsound for the secondary objective.
- Sampled logical H2-cell reduction from safe collapse: `5.9446%` overall;
  standalone representative benchmarks were `6.2×`–`35.7×` slower because
  Python partition canonicalization dominated the saved matrix work.
- Refinement-plus-immediate-mass dominance: exact-safe, zero violations on
  examined matrix pairs and adversarial small partitions; sampled strict
  dominance cell reduction after closed-form states were excluded: `0.1184%`.
- Similarity bounds: exact-safe total-variation action and optimal-value
  bounds; high-support completed-ladder strict skip ratio: `0.2715%`, with
  nearest-neighbor distance means `0.8567`/`0.8903`/`0.9181` for support
  500/750/1000. No solved-state index was integrated.
- Curated coverage: only a bounded frontier from eight deterministic root
  guesses was obtainable; the full curated H3 run remains a bounded timeout
  boundary inherited from ISSUE-013.

## Evidence

- Research/design note: `docs/research/issue_014_h2_action_similarity.md`
- Machine-readable artifact: `experiments/results/issue_014_h2_action_similarity.json`
- Markdown summary: `experiments/results/issue_014_h2_action_similarity_summary.md`
- Research helpers: `experiments/issue_014_h2_action_similarity.py`
- Tests: `tests/test_issue_014_action_similarity.py`

## Verification target

The final handoff must include fresh full tests, compile/import, artifact
validation, `git diff --check`, exact branch/base identity, and an append-only
JOURNAL record. No accepted-state advancement is claimed.
