# ISSUE-004 first experiment

This is executor-local evidence, not supervisor acceptance.

## Scope

- Full: 12974 legal guesses, 2315 candidate answers, 2315 requested episodes.
- Small: 10 legal guesses, 5 candidate answers, 5 requested episodes.
- The scheduled Hardle answer membership was not provided to the solver.

## Results

| Scope | Policy | Completed / requested | Solve rate | Mean guesses | Runtime (s) | Stop reason |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| full-2315-candidates | Random | 2315 / 2315 | 0.000864 | 9.998272 | 11.440 | completed |
| full-2315-candidates | MAP | 2315 / 2315 | 1.000000 | 5.360259 | 14.233 | completed |
| full-2315-candidates | Max-IG | 0 / 2315 | 0.000000 | 0.000000 | 30.021 | Max-IG budget exceeded after 591 guess evaluations |
| small-exact-planning | Random | 5 / 5 | 0.200000 | 2.600000 | 0.000 | completed |
| small-exact-planning | MAP | 5 / 5 | 1.000000 | 2.200000 | 0.000 | completed |
| small-exact-planning | Max-IG | 5 / 5 | 0.000000 | 3.000000 | 0.004 | completed |
| small-exact-planning | Exact-Bayes-optimal | 5 / 5 | 1.000000 | 3.000000 | 0.003 | completed |

Full Max-IG uses the complete legal vocabulary. If it stops before 2,315 episodes, the row records the measured wall-clock limit and number of guess evaluations rather than substituting a reduced scope.

Machine-readable output: `experiments/results/issue_004_first_experiment.json`
