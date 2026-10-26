# ISSUE-005 Exact Max-IG Performance Engineering Plan

**Goal:** Preserve exact Bayesian Hardle semantics while making the complete
12,974 × 2,315 Max-IG selection computationally practical.

**Root cause:** Fresh profiling on the accepted scalar implementation spends
the time in repeated Python-level guess/answer feedback evaluation and branch
posterior construction; entropy arithmetic is not the bottleneck.

**Design:** Keep the scalar game, partitioner, and information-gain classes as
the reference path. Add an exact NumPy-backed `uint8` matrix whose code is
`exact_count * (word_length + 1) + misplaced_count`. Build it in answer-vector
chunks from exact-position equality plus duplicate-aware multiset overlap.
For a current belief, compute each row's weighted code masses with
`numpy.bincount`; deterministic feedback makes `IG = H(outcome)`. Reuse one
matrix whenever a later belief is a subset of its candidate-answer universe,
and cache decisions by normalized belief, remaining horizon, and legal order.

## Vertical slices

- [x] **RED/GREEN matrix contract:** add tests for code encoding/decoding,
   adversarial repeated letters, and a deterministic 10,000-pair full-vocab
   sample; implement the matrix builder and read-only row/index API.
- [x] **RED/GREEN entropy equivalence:** add uniform, non-uniform, repeated-letter,
   and random-subset comparisons against `ExactOutcomePartitioner` plus
   `ExactInformationGainCalculator`; implement weighted matrix-row entropy.
- [x] **RED/GREEN policy equivalence:** add reference-vs-fast action tests,
   candidate filtering checks, legal-order/posterior-mass tie tests, and
   decision-cache hit tests; integrate the fast path without changing the
   existing custom/reference path.
- [x] **RED/GREEN benchmark:** add an ISSUE-005 benchmark entrypoint measuring
   cold construction, matrix bytes, warm full first move, and the existing
   full 2,315-episode Max-IG experiment. Keep the complete vocabulary and
   record any incomplete run honestly.
- [x] **Verification and handoff:** run the full suite, compile/import checks,
   diff checks, artifact validation, fresh performance measurements, and
   append the executor report. Do not modify `PROJECT_STATE.md`.

## Non-goals

- No change to the candidate-answer or legal-guess sets.
- No approximation, heuristic search, Rust/Numba/Cython, multiprocessing,
  prior/objective/feedback change, or scheduled-answer leakage.
- No claim of supervisor acceptance.
