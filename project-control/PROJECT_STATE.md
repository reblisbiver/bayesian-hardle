# Project state

This file records only the current state accepted by a `[SUPERVISOR REVIEW]`.
Executor reports and unreviewed proposals belong in `JOURNAL.md` instead.

## Final goal

Build and study a correct, testable, and interpretable Bayesian Hardle solver before considering learned policies or reinforcement learning.

## Current research question

How do exact Bayesian baselines behave on Hardle, and where do exact information-gain and finite-horizon planning methods become computationally impractical as vocabulary size grows?

## Current milestone

ISSUE-005 exact Max-IG acceleration accepted. The next milestone is a fairness-oriented evaluation mode in which the solver does not know the curated answer subset, together with an interactive local acceptance interface the OWNER can use directly.

## Confirmed decisions

- `project-control/` is the formal shared communication and supervision channel.
- OWNER is not used as a message relay between SUPERVISOR and EXECUTOR.
- Executor reports are not accepted state until independent SUPERVISOR review.
- Bayesian core work must precede neural-network or reinforcement-learning work.
- Legal guesses and candidate answers remain conceptually separate, but the primary fairness benchmark must not assume knowledge of the curated 2,315-word answer subset.
- Primary fair hypothesis support is the full current Hardle legal vocabulary (12,974 words): every legal word remains possible. The curated 2,315-word list is retained only as a diagnostic/answer-list-aware comparison mode.
- Fair modes must not use scheduled Hardle answer membership. A full-uniform prior and a broad general-English-frequency prior may be compared, provided every legal word retains non-zero support and the prior uses no future/scheduled answer leakage.
- Hardle feedback is `(exact-position count, present-but-wrong-position count)` with duplicate-aware multiplicity matching.
- Maximum guesses for the current full benchmark is 10.
- ISSUE-004's original 2,315-answer baseline used a uniform prior; future fair benchmarks will compare full-uniform and full-frequency priors over the full legal support.
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
- ISSUE-005 exact Max-IG acceleration using an exact uint8 feedback matrix, vectorized outcome scoring, and deterministic decision caching while preserving scalar reference semantics.

## Accepted experiments

First controlled ISSUE-004 experiment:
- Full 2,315-candidate benchmark: Random completed with solve rate `0.000864`; MAP completed with solve rate `1.000000` and mean guesses `5.360259`.
- Full Max-IG did not complete even one episode within the declared 30-second budget; this is accepted only as evidence of a naive scaling limit, not as a completed baseline comparison.
- Small five-answer / ten-legal-guess benchmark with three-guess horizon: Random `1/5`; MAP `5/5`, mean `2.2`; Max-IG `5/5`, mean `2.0`; exact Bayes-optimal `5/5`, mean `2.0`.
- On the small benchmark, Max-IG and exact Bayes-optimal both choose `arise` first, reduce the posterior to a singleton for every target, then immediately guess the known answer.

## Active issue

Build the fairness-oriented full-support benchmark and an interactive local acceptance client. Exact full-vocabulary Bayes-optimal planning remains intentionally out of scope until tractability is reassessed.

## Open questions

- How much performance changes when the solver must treat all 12,974 legal words as possible hidden answers rather than knowing the curated 2,315 subset.
- How full-uniform and general-English-frequency priors compare under the same non-leaking full support.
- How Max-IG, MAP, and later finite-horizon methods behave when evaluated through the same interactive and reproducible acceptance client.

## Deferred ideas

- Neural policies, reinforcement learning, MCTS, and other learned/approximate controllers remain deferred until the exact Bayesian baseline/scaling story is established.

## Superseded ideas

None recorded.

## Current verified implementation checkpoint

ISSUE-005 checkpoint `fe4f035` on `codex/issue-005-maxig-speed`, independently verified by SUPERVISOR after merge with 44 passing tests. Exact Max-IG cold first move is ~0.61s, warm full first move ~0.12s, and the 2,315-target benchmark completes in ~18.4s with 100% solve rate and mean 4.586 guesses.