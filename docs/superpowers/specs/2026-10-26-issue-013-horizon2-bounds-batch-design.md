# ISSUE-013 horizon-2 child bounds and exact batch fusion design

## Intent

ISSUE-012 established that exact horizon-3 selection on the support=500
ladder spends about 91% of selection time evaluating independent horizon-2
child states. Child-state reuse is only about 0.7%, so a second memoization
scheme is not justified. This design attacks that measured term while
preserving the exact Hardle semantics, the solve-probability-first objective,
the expected-guesses secondary objective, and deterministic tie resolution.

## Goals and non-goals

Goals:

- prove and test a cheap horizon-2 success-probability upper bound;
- measure whether the bound can skip child H2 cells or root actions;
- fuse a bounded block of independent H2 child evaluations through one exact
  ragged NumPy code gather and grouped maxima reduction when that is faster;
- report logical matrix cells, block temporary memory, child requests, exact
  child solves, bound-only skips, root pruning, and timing movement;
- preserve scalar/reference equivalence on weighted and duplicate-letter
  states and produce auditable JSON, Markdown, and profile artifacts.

Non-goals:

- no heuristic approximation inside `ExactBayesOptimalPlanner`;
- no speculative cache or change to public belief semantics;
- no replacement of the scalar reference planner;
- no full 2,315-support/horizon-3 feasibility claim from a bounded probe;
- no change to `project-control/PROJECT_STATE.md`.

## Approaches considered

### A. Capacity bound only

For a normalized child posterior with legal-answer masses `p_i`, a single
H2 probe produces at most `K` feedback codes. One final legal answer can
receive credit in each code branch, so every probe has success probability at
most the sum of the largest `min(K, n)` legal-answer masses. A root action gets
the immediate winning mass plus the branch-mass-weighted child bounds.

This is mathematically safe and inexpensive, but the support=500 exploratory
replay produced zero strict child-action skips and zero strict root-action
skips. It remains a tested, instrumented analysis result and is not enabled
as a planner shortcut unless a later benchmark supplies a positive case.

### B. Padded multi-child vectorization

Stack child supports into a rectangular tensor and reduce feedback codes in
three dimensions. This matched scalar values in a spike but padded support
indices by roughly 1.6--3.7x and was slower than scalar evaluation. It is
rejected because its speed/memory tradeoff fails the measured acceptance
criterion.

### C. Ragged exact child block fusion (chosen)

For a small sequential block of non-winning H3 branches, concatenate their
posterior answer indices and normalized weights without padding. Gather the
shared legal-guess rows once, then reduce each row into
`child_id * code_count + feedback_code` slots with exact `np.maximum.at`.
Return one `(child, guess, (success, expected))` array and select each
child's best action with the existing tolerance and tie rank. Flush blocks
before branch-and-bound decisions, so any extra work is bounded by the block
size and exact root-action pruning remains in control.

The chosen implementation uses an opt-in optimization layer with a small
bounded block size. The benchmark decides whether the default layer remains
enabled; if it loses on the ladder or exceeds the temporary-memory budget,
the implementation remains available for diagnosis but is not promoted.

## Exact bound proof

Let `A` be the child support, `L` the legal final answers, and `p(w)` the
normalized posterior mass. For a first H2 probe `g`, let `B_o(g)` be the
answer set with feedback code `o`. The exact success value is

```
V(g) = sum_o max({p(w): w in B_o(g) and w in L}, default=0).
```

There are at most `K=36` Hardle integer feedback codes for five-letter words.
Each code contributes at most one final-answer mass, so `V(g)` is no greater
than the sum of the largest `min(K, |A intersect L|)` values in
`{p(w): w in A intersect L}`. If `g` is itself a legal answer, the exact-win
code is one of those code slots; separating its mass and taking the largest
`K-1` remaining masses is an equivalent or tighter per-action bound.

The bound uses only nonnegative posterior masses and a finite branch count;
it does not assume a partition shape, uniformity, or an answer/probe
relationship. Therefore it cannot underestimate any exact H2 action value.
For a root action, summing the immediate winning branch exactly and applying
the child bound to every non-winning branch is safe by linearity of posterior
expectation. The bound can prune only when its success upper bound is strictly
below the incumbent success within the existing tolerance; equality remains
live so the expected-guesses and deterministic tie rules cannot change.

## Exact batch contract

The matrix layer will expose an internal block evaluator over:

- one legal-guess sequence;
- multiple non-empty answer-word sequences contained in the matrix;
- one normalized weight sequence per child;
- one legal final-answer sequence shared by the planner state.

It returns a float64 array with shape `(children, guesses, 2)`, where the last
axis is exactly `(solve_probability, expected_guesses)`. It must agree with
the existing scalar `horizon_two_values` values within the project tolerance.
Its temporary-memory accounting includes gathered uint8 codes, ragged index,
weight, group-id, maxima, expected-mass, and output arrays; logical matrix
cells remain `sum(child_support) * legal_count`, not padded cells.

The planner may use this evaluator only for H3 states whose child is H2,
whose feedback engine is the exact Hardle engine, and whose matrix contains
all legal guesses and child answers. Fallback is the existing scalar/batch
path. A block is evaluated in branch order and is flushed before applying the
existing exact branch-and-bound check.

## Verification boundary

- adversarial and deterministic random weighted bound tests must satisfy
  `upper_bound >= exact_value` for every legal probe and exact root bound;
- block values must match scalar matrix values and the reference planner;
- duplicate-letter feedback, non-answer probes, answer-only legal lists,
  weighted posteriors, and equal-value tie cases remain covered;
- before/after rows must include the ISSUE-012 ladder 32/50/100/200/500,
  larger feasible intermediates, and a declared bounded curated 2315 probe;
- no row is called complete unless its exact worker completed within budget;
- fresh full tests, compile/import, artifact validation, diff check,
  branch/worktree identity, append-only journal evidence, and unchanged
  `PROJECT_STATE.md` are required before `READY_FOR_REVIEW`.
