# ISSUE-004 — Exact Bayesian core and first experiment

## Goal
Implement the already-decided exact Bayesian Hardle pipeline and run the first controlled baseline/sanity experiment. Do not reopen settled theory unless execution exposes a contradiction that changes the research definition.

## Settled research contract
- Hidden answer W is a five-letter word.
- Legal guesses A follow the current Hardle-compatible allowed-guess vocabulary; keep legal guesses separate from candidate answers.
- Candidate-answer hypothesis space for the non-leaking solver baseline is the original curated Wordle answer vocabulary (2315 words), not the leaked Hardle future schedule.
- The current Hardle scheduled-answer list may be used only by evaluation as hidden targets; the solver must not condition on membership in that schedule.
- Maximum guesses: 10.
- Feedback is the pair (exact-position count, present-but-wrong-position count), with repeated letters matched without exceeding the multiplicity available in the answer.
- Prior for the first baseline experiment: uniform over the candidate-answer hypothesis space.
- Posterior update is exact deterministic Bayesian filtering and renormalization.
- Entropy is Shannon entropy over posterior answer mass.
- Information gain is current entropy minus expected posterior entropy over all possible feedback outcomes.
- Primary metric: final solve probability within the finite guess horizon. Mean guesses is secondary.
- Baseline policies: Random, MAP, Max-IG.
- Bayes-optimal finite-horizon planning is the theoretical target. Implement and verify it first on a deliberately small tractable vocabulary only; do not pretend a full-2315 exact planner is tractable if it is not.

## Required execution
1. Implement the Hardle vocabulary/game/feedback behavior behind the accepted interfaces.
2. Implement uniform prior, deterministic likelihood/posterior update, probability normalization/invariants.
3. Implement outcome distribution, entropy, expected posterior entropy, and information gain exactly.
4. Implement Random, MAP, and Max-IG through the shared policy interface.
5. Implement exact finite-horizon Bayes-optimal planning for small vocabularies, reusing the shared FeedbackEngine and PosteriorUpdater and memoizing repeated belief/horizon states.
6. Add an EpisodeRunner/benchmark path sufficient to compare policies without leaking scheduled-answer membership into the solver.
7. Run a first experiment with two scopes:
   - full candidate vocabulary for Random / MAP / Max-IG if computationally practical;
   - small controlled vocabulary for Random / MAP / Max-IG / exact Bayes-optimal, proving the planner and objective end-to-end.
8. Save machine-readable experiment outputs plus a short human-readable result summary. Report solve rate first; mean guesses second; record compute cost/runtime enough to distinguish theory from scaling limitations.

## Evidence and correctness gates
- TDD for duplicate-letter feedback, posterior filtering, entropy/IG identities, policy behavior, and finite-horizon planner cases.
- Include adversarial duplicate-letter examples where naive membership counting fails.
- Verify posterior mass sums to 1 after every nonempty update and zero-mass impossible observations are handled explicitly.
- Verify outcome branch probabilities sum to 1.
- Verify IG >= 0 up to numerical tolerance and IG = 0 for a guess that cannot distinguish any remaining candidates.
- Verify planner terminal/base cases and one tiny hand-checkable decision tree.
- No policy may bypass shared FeedbackEngine or PosteriorUpdater.
- No learned model, RL, MCTS, heuristic alpha/beta policy, or leaked future-answer prior.

## Reporting
Work in an isolated branch/worktree. Append one [EXECUTION REPORT] to JOURNAL.md with branch/base/result SHA, tests, experiment configuration, results, runtime, any blocked scope, and READY_FOR_REVIEW. Do not update accepted PROJECT_STATE and do not claim supervisor acceptance.