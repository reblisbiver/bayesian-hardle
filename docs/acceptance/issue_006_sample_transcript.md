# ISSUE-006 OWNER acceptance sample transcript

This is a short local transcript captured from the isolated ISSUE-006
worktree. Timing values are machine observations, not acceptance thresholds.

## Simulated target: full-uniform, legal target outside curated 2,315

```text
$ python3 -m bayesian_hardle.cli simulate --target aahed --mode full-uniform --policy map
MODE: full-uniform | policy=map | support is resolved by the selected mode
TURN 1 | mode=full-uniform (PRIMARY STRICT FAIRNESS) | policy=map
  guess=aahed feedback=(5, 0) remaining_candidates=1 entropy_bits=0.000000 decision_ms=1.332
  top_candidates=aahed:1
  status=SOLVED
MODE: full-uniform (PRIMARY STRICT FAIRNESS) | support=12974
RESULT solved=True turns=1 total_time_ms=19.408
```

`aahed` is accepted by the full legal vocabulary but is absent from the
curated answer list. This demonstrates the fair modes' support boundary; the
same target is intentionally rejected by `curated-2315` as an answer-list-aware
diagnostic simulation.

## Live assist: accept a website observation and continue

```text
$ python3 -m bayesian_hardle.cli live --mode full-uniform --policy map
MODE: full-uniform (PRIMARY STRICT FAIRNESS) | support=12974 | policy=map | max_guesses=10
TURN 1 | mode=full-uniform (PRIMARY STRICT FAIRNESS) | policy=map
  guess=aahed feedback=unknown remaining_candidates=12974 entropy_bits=13.663336 decision_ms=1.315
  top_candidates=aahed:7.70772e-05, aalii:7.70772e-05, aargh:7.70772e-05, aarti:7.70772e-05, abaca:7.70772e-05
  status=AWAITING_FEEDBACK
Enter Hardle feedback (exact misplaced), or q: 0 0
TURN 1 | mode=full-uniform (PRIMARY STRICT FAIRNESS) | policy=map
  guess=aahed feedback=(0, 0) remaining_candidates=2543 entropy_bits=11.312316 decision_ms=1.315
  top_candidates=bibbs:0.000393236, biccy:0.000393236, biffo:0.000393236, biffs:0.000393236, biffy:0.000393236
  status=CONTINUE
TURN 2 | mode=full-uniform (PRIMARY STRICT FAIRNESS) | policy=map
  guess=bibbs feedback=unknown remaining_candidates=2543 entropy_bits=11.312316 decision_ms=0.412
  top_candidates=bibbs:0.000393236, biccy:0.000393236, biffo:0.000393236, biffs:0.000393236, biffy:0.000393236
  status=AWAITING_FEEDBACK
Enter Hardle feedback (exact misplaced), or q: q
status=QUIT
```
