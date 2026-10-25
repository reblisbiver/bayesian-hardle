# ISSUE-003 — Initialize Bayesian Hardle component scaffold

## Goal

Create the executable project skeleton for the accepted Bayesian Hardle architecture without implementing game semantics, Bayesian calculations, information-gain calculations, or planning algorithms.

## Architecture to initialize

A. Game Model
- VocabularyRepository
- GameSpec
- FeedbackEngine protocol
- TerminalRules protocol

B. Bayesian Belief Engine
- PriorModel protocol
- BeliefState value object
- LikelihoodModel protocol
- PosteriorUpdater protocol

C. Information Engine
- OutcomePartitioner protocol
- EntropyCalculator protocol
- ExpectedEntropyCalculator protocol
- InformationGainCalculator protocol

D. Decision Engine
- DecisionState value object
- Policy protocol
- RandomPolicy placeholder
- MAPPolicy placeholder
- MaxInformationGainPolicy placeholder
- BayesOptimalPlanner protocol
- PlannerCache protocol

E. Evaluation & Experiment System
- EpisodeRunner protocol
- BenchmarkSpec value object
- MetricsResult value object
- ExperimentConfig value object
- ArtifactSink protocol

## Information contracts

Primary runtime flow:
1. Game Model supplies legal guesses, target vocabulary, game limits, and feedback semantics.
2. Belief Engine consumes prior + observed guess/feedback history and produces `BeliefState`.
3. Information Engine consumes `BeliefState`, candidate guesses, and the shared feedback semantics; it produces per-guess information values/outcome distributions.
4. Decision Engine consumes `DecisionState(belief, remaining_guesses)` plus shared game/information interfaces; it returns the selected guess.
5. Game Model evaluates the selected guess against the hidden target and returns feedback.
6. Belief Engine updates the posterior; remaining horizon decreases; the loop repeats.
7. Evaluation wraps this loop and records outcomes/metrics without changing game semantics.

## Hard constraints

- No real Hardle feedback algorithm in this issue.
- No repeated-letter rule decision in this issue.
- No posterior numeric update implementation in this issue.
- No entropy / IG numeric implementation in this issue.
- No Bellman recursion or exact planner implementation in this issue.
- No neural networks, RL, MCTS, heuristics beyond named placeholder policy classes.
- All policies/planners must depend on the shared Game Model / Belief contracts rather than duplicate semantics.
- Keep public interfaces small and typed.
- Use standard library only unless the existing project already requires otherwise.

## Acceptance criteria

- Package contains focused modules for the five architecture groups.
- Public protocols/value objects listed above exist and import cleanly.
- One integration-level scaffold test demonstrates the intended dependency direction and data handoff using test doubles, not real algorithms.
- Existing scaffold tests still pass.
- No component contains hidden algorithmic behavior beyond validation and trivial data storage.
- `README.md` or architecture documentation contains a compact component map and information-flow summary.
- Executor records branch/base/result SHA, changed files, tests, and unresolved items in `[EXECUTION REPORT]`.

## Status

OPEN — supervisor-dispatched architecture initialization task.
