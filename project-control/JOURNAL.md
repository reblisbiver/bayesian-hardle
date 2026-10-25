
## 2026-10-25 — [OWNER DECISION] Enter engineering execution

Status: DIRECTIVE

OWNER confirms that previously settled Bayesian Hardle theory should no longer be reopened as discussion by default. SUPERVISOR should independently execute implementation and experiments, escalating only decisions that change the hypothesis space, objective, experimental comparison, or research conclusion.

## 2026-10-25 — [SUPERVISOR TASK] ISSUE-004 exact Bayesian core and first experiment

Status: OPEN

Executor must implement `project-control/issues/ISSUE-004-exact-bayesian-core-and-first-experiment.md` from the accepted component scaffold.

The settled path is: exact Hardle feedback semantics → exact Bayesian prior/posterior → entropy/information gain → Random/MAP/Max-IG baselines → exact finite-horizon Bayes-optimal planning on a tractable small vocabulary → first controlled experiment.

Do not reopen settled theory unless implementation evidence exposes a contradiction that would change the research definition. Do not use the leaked Hardle scheduled-answer set as solver knowledge. Use TDD, isolated worktree/branch execution, and verification-before-completion. Return READY_FOR_REVIEW with reproducible experiment artifacts and evidence; do not claim supervisor acceptance.
