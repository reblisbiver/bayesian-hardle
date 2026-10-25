# Project state

This file records only the current state accepted by a `[SUPERVISOR REVIEW]`.
Executor reports and unreviewed proposals belong in `JOURNAL.md` instead.

## Final goal

Build and study a correct, testable, and interpretable Bayesian Hardle solver before considering learned policies or reinforcement learning.

## Current research question

How do exact Bayesian baselines behave on Hardle, and where do exact information-gain and finite-horizon planning methods become computationally impractical as vocabulary size grows?

## Current milestone

ISSUE-004 exact Bayesian core and first controlled experiment accepted. The next engineering milestone is scaling the exact Max-IG path so it can complete meaningful full-vocabulary evaluation without changing the research definition.

## Confirmed decisions

- `project-control/` is the formal shared communication and supervision channel.
- OWNER is not used as a message relay between SUPERVISOR and EXECUTOR.
- Executor reports are not accepted state until independent SUPERVISOR review.
- Bayesian core work must precede neural-network or reinforcement-learning work.
- Legal guesses and candidate answers are separate vocabularies.
- Solver candidate-answer space is the non-leaking 2,315-word curated answer vocabulary; scheduled Hardle answer membership is not solver knowledge.
- Hardle feedback is `(exact-position count, present-but-wrong-position count)` with duplicate-aware multiplicity matching.
- Maximum guesses for the current full benchmark is 10.
- First-baseline prior is uniform over candidate answers.
- Primary objective is final solve probability within the finite horizon; expected guesses is a secondary tie-break only when solve probability is equal.

## Hard constraints

- Preserve evidence boundaries between local implementation/tests and live or business acceptance.
- Keep `JOURNAL.md` append-only.
- Do not advance research stages without `[SUPERVISOR REVIEW]` acceptance.
- No learned model, RL, MCTS, or heuristic replacement of exact Bayesian semantics before the exact baseline/scaling story is established.

## Current Bayesian formulation

The accepted system has five groups: Game Model, Bayesian Belief Engine, Information Engine, Decision Engine, and Evaluation & Experiment System. It now includes duplicate-aware Hardle feedback, uniform prior, exact deterministic posterior filtering/renormalization, Shannon entropy, expected posterior entropy, exact information gain, Random/MAP/Max-IG policies, and exact finite-horizon Bayes-optimal planning on tractable small vocabularies.

Max-IG maximizes exact information gain first; ties within numerical tolerance prefer a remaining answer candidate with highest posterior mass. Exact Bayes-optimal planning maximizes final solve probability first; equal-success actions prefer lower expected guesses to solve/termination.

## Accepted implementations

- ISSUE-001 project control plane and repository scaffold.
- ISSUE-003 five-group Bayesian Hardle component/interface scaffold.
- ISSUE-004 exact Hardle feedback, Bayesian posterior, entropy/information gain, Random/MAP/Max-IG baselines, exact small-vocabulary Bayes-optimal planner, evaluation runner, pinned word-list inputs, and reproducible experiment artifacts.

## Accepted experiments

First controlled ISSUE-004 experiment:
- Full 2,315-candidate benchmark: Random completed with solve rate `0.000864`; MAP completed with solve rate `1.000000` and mean guesses `5.360259`.
- Full Max-IG did not complete even one episode within the declared 30-second budget; this is accepted only as evidence of a naive scaling limit, not as a completed baseline comparison.
- Small five-answer / ten-legal-guess benchmark with three-guess horizon: Random `1/5`; MAP `5/5`, mean `2.2`; Max-IG `5/5`, mean `2.0`; exact Bayes-optimal `5/5`, mean `2.0`.
- On the small benchmark, Max-IG and exact Bayes-optimal both choose `arise` first, reduce the posterior to a singleton for every target, then immediately guess the known answer.

## Active issue

Scale exact Max-IG computation and then run a meaningful full-vocabulary Max-IG comparison. Exact full-vocabulary Bayes-optimal planning remains intentionally out of scope until tractability is reassessed.

## Open questions

- What exact computational optimizations are sufficient to make full Max-IG practical without changing its mathematical definition?
- After exact Max-IG is scaled, how does its solve-rate / guess-efficiency profile compare with MAP on the full benchmark?
- At what vocabulary/horizon size does exact finite-horizon Bayes-optimal planning cease to be practical, and what approximations should be studied only after that boundary is measured?

## Deferred ideas

- Neural policies, reinforcement learning, MCTS, and other learned/approximate controllers remain deferred until the exact Bayesian baseline/scaling story is established.

## Superseded ideas

None recorded.

## Current verified implementation checkpoint

ISSUE-004 correction checkpoint `9568d1b` on `codex/issue-004-exact-bayesian-core`, independently verified by SUPERVISOR with 35 passing tests, compile/import checks, `git diff --check`, clean worktree, regenerated experiment artifacts, and independent policy traces confirming the Max-IG and Bayes-optimal tie-handling fixes.