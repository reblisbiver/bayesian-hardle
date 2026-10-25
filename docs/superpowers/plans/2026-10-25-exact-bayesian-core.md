# Exact Bayesian Core and First Experiment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the settled exact Bayesian Hardle pipeline, prove its semantics with behavior-level tests, and run reproducible baseline and small-vocabulary Bayes-optimal experiments.

**Architecture:** Keep the five accepted component groups. Concrete implementations will use immutable typed values at the game/belief/information boundaries, exact deterministic feedback and posterior filtering, shared outcome partitioning for policies and planning, and an episode runner that receives hidden targets only from evaluation. The full 2315-answer comparison will be attempted honestly for Random/MAP/Max-IG; exact Bellman planning is restricted to a declared small vocabulary and memoizes canonical belief/horizon states.

**Tech Stack:** Python 3.9+ standard library, `unittest`, JSON/CSV artifacts, vendored plain-text word lists with provenance metadata.

**Spec:** `project-control/issues/ISSUE-004-exact-bayesian-core-and-first-experiment.md`

## Global Constraints

- Hidden answer W is a five-letter word; legal guesses and candidate answers remain separate.
- Candidate-answer hypothesis space is the original curated 2315-word answer vocabulary; no scheduled-answer membership is solver knowledge.
- Maximum guesses is 10; the prior is uniform for the first experiment.
- Feedback is `(exact-position count, present-but-wrong-position count)` with multiplicity-limited matching.
- Entropy is Shannon entropy over posterior answer mass; IG is current entropy minus expected posterior entropy.
- Full-vocabulary Max-IG is not silently reduced; if it is too expensive, record the scaling limit and the exact attempted scope.
- No learned model, RL, MCTS, heuristic alpha/beta planner, or leaked future-answer prior.
- `project-control/JOURNAL.md` is append-only and `PROJECT_STATE.md` is not modified.

## Review Focus

- Duplicate letters where naive membership counting overstates present letters; tests in the game slice.
- Zero-probability observations and empty posteriors; tests in the posterior slice.
- Guesses outside the candidate-answer set but inside legal guesses; tests in policy/evaluation slices.
- Equal-IG ties and guesses that cannot distinguish the belief; tests in the information/policy slice.
- Planner terminal states, horizon-one decisions, and memo-key reuse; tests in the planner slice.

### Task 1: Game semantics and reproducible vocabulary inputs

**Files:**
- Create: `src/bayesian_hardle/game.py` concrete repository, feedback engine, and terminal rules behind the accepted protocols.
- Create: `data/wordlists/wordle-legal-guesses.txt`, `data/wordlists/wordle-candidate-answers.txt`, and `data/wordlists/provenance.json`.
- Create: `tests/test_game_behavior.py`.

**Interfaces:**
- Produces `WordListVocabularyRepository`, `HardleFeedbackEngine.evaluate(guess, target) -> tuple[int, int]`, `HardleTerminalRules`, and `Feedback` for later slices.

- [ ] Write tests for normalization/counts, exact duplicate-letter examples, malformed words, win/loss terminal behavior, and legal-guess/answer separation.
- [ ] Run the focused tests and observe RED because concrete implementations/data are absent.
- [ ] Vendor the authoritative public lists with provenance and a validation command; preserve the exact 12974/2315 counts or record a blocker rather than silently substituting another list.
- [ ] Implement the two-pass multiplicity-limited feedback count and terminal rules with minimal concrete repositories.
- [ ] Run `PYTHONPATH=src python3 -m unittest tests.test_game_behavior -v` and confirm GREEN.

### Task 2: Prior, exact posterior filtering, and invariants

**Files:**
- Modify: `src/bayesian_hardle/belief.py` with concrete uniform prior and deterministic posterior updater.
- Create: `tests/test_belief_behavior.py`.

**Interfaces:**
- Consumes `Feedback`, `FeedbackEngine`, and `BeliefState` from Task 1.
- Produces `UniformPrior.initial_belief`, `ExactPosteriorUpdater.update`, and normalized immutable `BeliefState` values for later components.

- [ ] Test uniform initialization, exact filtering, posterior observations, normalization, candidate ordering, and explicit zero-mass/impossible-observation behavior.
- [ ] Run focused tests RED.
- [ ] Implement the prior and updater by comparing each target's shared feedback with the observed feedback, preserving float mass and rejecting empty posterior updates explicitly.
- [ ] Run focused tests GREEN and compile checks.

### Task 3: Outcome distributions, entropy, and information gain

**Files:**
- Modify: `src/bayesian_hardle/information.py` with concrete partition/entropy/expected-entropy/IG implementations.
- Create: `tests/test_information_behavior.py`.

**Interfaces:**
- Consumes `BeliefState`, `FeedbackEngine`, and the Task 2 updater semantics.
- Produces `ExactOutcomePartitioner`, `ShannonEntropyCalculator`, `ExpectedPosteriorEntropyCalculator`, and `InformationGainCalculator` for policies/planner.

- [ ] Test branch posterior correctness, branch probabilities summing to one, entropy identities, nonnegative IG within tolerance, and zero IG for an indistinguishing guess.
- [ ] Run focused tests RED.
- [ ] Implement exact grouping by feedback, posterior mass aggregation, Shannon entropy, and expected posterior entropy without ad hoc approximations.
- [ ] Run focused tests GREEN.

### Task 4: Policies and exact finite-horizon planner

**Files:**
- Modify: `src/bayesian_hardle/decision.py` with Random/MAP/Max-IG policies, a canonical planner cache, and exact Bellman planner.
- Create: `tests/test_decision_behavior.py`.

**Interfaces:**
- Consumes the shared game, updater, partitioner, entropy/IG implementations and `DecisionState`.
- Produces policies with deterministic injectable RNG/tie-breaking, and `ExactBayesOptimalPlanner.select_guess` using shared `FeedbackEngine` and `PosteriorUpdater` dependencies.

- [ ] Test seeded random selection, MAP mass ordering, Max-IG selection/ties, planner horizon/terminal cases, a hand-checkable decision tree, and memoization.
- [ ] Run focused tests RED.
- [ ] Implement policy selection and Bellman recursion where success has value one and failure value zero at the finite horizon; cache canonical belief masses plus remaining guesses.
- [ ] Run focused tests GREEN and verify no policy bypasses shared feedback/posterior components.

### Task 5: Episode runner, evaluation, and first controlled experiment

**Files:**
- Modify: `src/bayesian_hardle/evaluation.py` with concrete episode runner, metrics, and artifact writer.
- Create: `experiments/issue_004_first_experiment.py`, `experiments/issue_004_first_experiment_config.json`, `experiments/results/issue_004_first_experiment.json`, `experiments/results/issue_004_first_experiment_summary.md`, and `tests/test_evaluation_behavior.py`.
- Modify: `README.md` with the runnable command and evidence boundary.

**Interfaces:**
- Consumes `VocabularyRepository`, `GameSpec`, `TerminalRules`, `PriorModel`, `Policy`, and planner implementations.
- Produces machine-readable per-policy metrics including solve rate, mean guesses among episodes, runtime/cost, scope, seeds, and provenance paths.

- [ ] Test that evaluation supplies hidden targets only to the game loop, does not alter solver candidate belief, and computes solve rate/mean guesses correctly.
- [ ] Run focused tests RED.
- [ ] Implement deterministic benchmark orchestration for full candidate-target evaluation and a declared tractable small vocabulary, with JSON/Markdown artifacts.
- [ ] Run the first experiment with Random/MAP/Max-IG on full scope when practical and all four policies on the small scope; record any Max-IG scaling limit without shrinking the requested scientific comparison.
- [ ] Run focused tests GREEN, full suite, compileall, diff checks, and artifact validation.

### Task 6: Handoff and audit record

**Files:**
- Modify: `project-control/JOURNAL.md` by appending one ISSUE-004 `[EXECUTION REPORT]`.

- [ ] Capture base/result SHA, changed files, fresh verification commands, experiment configuration/results, runtime, blocked scope, unknowns, and `READY_FOR_REVIEW`.
- [ ] Confirm `PROJECT_STATE.md` is unchanged and the final working tree/diff are auditable.

## Self-review

The issue requirements map to Tasks 1–5: game and vocabulary (1), prior/update (2), information (3), baselines/planner (4), evaluation and both experiment scopes (5), and reporting (6). The only deliberate scope limitation is exact planning on the small vocabulary, explicitly required by the issue; full Max-IG is attempted or its cost is reported rather than silently reduced. Interfaces are shared through the accepted Protocol boundaries and all research claims remain executor evidence pending supervisor review.
