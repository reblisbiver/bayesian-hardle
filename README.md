# Bayesian Hardle

Bayesian Hardle is a research codebase for studying Bayesian reasoning in a
Hardle-style word-feedback environment.

The repository is currently at the control-plane initialization milestone.
The formal communication and audit records live in
[`project-control/`](project-control/README.md). No algorithm, model, or
experiment is accepted until a supervisor review records acceptance.

## Layout

- `src/bayesian_hardle/` — package code.
- `tests/` — behavior-oriented tests.
- `experiments/` — reproducible experiment inputs, runners, and outputs.
- `scripts/` — small operational helpers.
- `docs/` — research and engineering documentation.
- `project-control/` — append-only handoffs and current accepted state.

## Component scaffold (ISSUE-003)

The package currently contains typed boundaries and value objects only. It
does not yet choose Hardle feedback rules, a posterior representation,
entropy or information-gain formulas, or a planning algorithm.

| Group | Module | Public boundary |
| --- | --- | --- |
| Game Model | `game.py` | `VocabularyRepository`, `GameSpec`, `FeedbackEngine`, `TerminalRules` |
| Bayesian Belief Engine | `belief.py` | `PriorModel`, `BeliefState`, `LikelihoodModel`, `PosteriorUpdater` |
| Information Engine | `information.py` | `OutcomePartitioner`, `EntropyCalculator`, `ExpectedEntropyCalculator`, `InformationGainCalculator` |
| Decision Engine | `decision.py` | `DecisionState`, `Policy`, placeholder policies, `BayesOptimalPlanner`, `PlannerCache` |
| Evaluation & Experiment System | `evaluation.py` | `EpisodeRunner`, `BenchmarkSpec`, `MetricsResult`, `ExperimentConfig`, `ArtifactSink` |

The intended runtime information flow is:

1. The Game Model supplies legal guesses, target vocabulary, game limits, and the shared feedback boundary.
2. The Belief Engine consumes a prior and observed guess/feedback history and exposes a `BeliefState`.
3. The Information Engine consumes that belief, candidate guesses, and the shared feedback boundary for outcome partitions and future information values.
4. The Decision Engine consumes `DecisionState(belief, remaining_guesses)` plus shared game/information interfaces and selects a guess.
5. The Game Model evaluates the guess against the hidden target and returns feedback.
6. The Belief Engine receives the observation, updates the posterior boundary, and the decision horizon decreases.
7. Evaluation wraps the loop and records metrics/artifacts without changing game semantics.

## Local verification

Run the standard-library test suite from the repository root:

```bash
python3 -m unittest discover -s tests -v
```

The project is intentionally small at this stage. Dependencies and research
protocols will be added only when a reviewed issue requires them.
