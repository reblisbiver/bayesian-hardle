# ISSUE-005 exact Max-IG performance

This is local evidence, not an external validation claim.

## Performance gate

- Scope: 12974 legal guesses x 2315 candidate answers.
- Cold first move, including matrix build: 0.610672s; matrix: 30034810 bytes (28.643 MiB).
- Warm first move, full row scan: mean 0.118602s; min 0.117829s; repeats: [0.11782858400000007, 0.119424792, 0.11855383299999989]
- Selected opener: cold `stare`, warm ['stare', 'stare', 'stare'].
- Gates: cold <= 2.0s and warm <= 0.5s.

## Full experiment

| Policy | Completed / requested | Solve rate | Mean guesses | Runtime (s) | Evaluated guesses | Cache hits / misses | Stop reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Max-IG | 2315 / 2315 | 1.000000 | 4.586177 | 18.410387 | 8978008 | 8112 / 2505 | completed |

## Before / after reference

The accepted ISSUE-004 baseline stopped after 30.039s, 603 guess evaluations, and 0 completed episodes. ISSUE-005 preserves the full scope and records the fresh result above; the ratio is computed from these measured runtimes, not from a reduced benchmark.
- Fresh full-experiment wall-clock speedup versus that accepted measurement: 1.632x (30.039s / 18.410387s).

Machine-readable output: `experiments/results/issue_005_maxig_speed.json`
