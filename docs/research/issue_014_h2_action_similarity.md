# ISSUE-014 — H2 action-space structure and similarity-bound research

Status: `REPRODUCIBLE_LOCAL_RESULT` — local evidence. No planner optimization
was integrated and `project-control/PROJECT_STATE.md` was not modified.

Base: `b50f3ba541327264e86b63137c3f37896b576dc8` on
`codex/issue-013-horizon2-bounds-batch`.

The machine-readable evidence is in
`experiments/results/issue_014_h2_action_similarity.json`; its compact report
is in `experiments/results/issue_014_h2_action_similarity_summary.md`.

## What was tested

For an H2 child posterior `p`, legal final-answer set `L`, and a first guess
`g`, the exact success component is

```
F_g(p) = sum over feedback blocks B of max({p(w): w in B intersect L}, default=0).
```

The expected-guesses component is

```
E_g(p) = 2 - p(g),
```

where `p(g)=0` for a probe-only guess. The planner compares `(F, E)`
lexicographically, with expected guesses used only when success probability
tied.

The audit reconstructs child supports from the completed ISSUE-013 H3 root
records at support 100, 200, 500, 750, and 1000. It also builds a bounded
curated-2315 frontier from eight deterministic legal first guesses because the
full curated H3 probe was a timeout in ISSUE-013. For each selected child, all
legal guesses are evaluated against the existing exact `uint8` feedback
matrix. Six deterministic child states per case are used for partition and
dominance reports; 24 unique child states per case are used for similarity
replay. The full child-request and unique-child counts are retained in the
artifact.

## A. Partition signatures and the immediate-hit caveat

The raw row for `g` is the sequence of exact Hardle feedback codes over the
active child support. The unlabeled signature is the canonical set of answer
index blocks obtained after erasing the numeric feedback labels. This treats
two rows as future-information equivalent only when they induce the same
candidate partition, even if the code names differ.

Partition equality alone is not an exact action-equivalence rule. If one
member of a class is a remaining answer candidate and another is probe-only,
their `F` values are equal for the same posterior and partition, but their
`E` values differ by the candidate's immediate-hit mass. The exact safe key is

```
(unlabeled_partition_signature, posterior_mass_of_first_guess)
```

and the deterministic representative must be the first action under the
planner's active tie order. Tests cover code relabeling, a mixed candidate /
probe class, weighted duplicate-letter states, and equality against
`ExactFeedbackCodeMatrix.horizon_two_values`.

The sampled action-collapse cell counts were:

```
before: 17,913,506 H2 logical cells
after:  16,848,625 H2 logical cells
reduction: 5.9446%
```

The local standalone collapse evaluator was exact, but its partition
canonicalization overhead made the representative large-state benchmark
`6.2×` to `35.7×` slower than the existing matrix evaluator across the six
cases. Small singleton and tiny-support states can show very large class
fractions, but their H2 work is not the dominant term and they are already
covered by closed forms or contribute few matrix cells. No collapse layer was
added to `ExactBayesOptimalPlanner`.

## B. Exact dominance condition

Let `P_a` and `P_b` be the unlabeled partitions of actions `a` and `b`. If
`P_a` refines `P_b`, each block of `P_b` is split into disjoint blocks of
`P_a`. For every split block,

```
max(x_1, ..., x_k) <= max(x_1, ..., x_i) + ... + max(x_{i+1}, ..., x_k),
```

so `F_a(p) >= F_b(p)`. If, in addition, `p(a) >= p(b)`, then
`E_a(p) <= E_b(p)`. Therefore the refinement-plus-immediate-mass condition is
an exact sufficient condition for action `a` to dominate action `b` under the
lexicographic H2 objective. Equal-value pairs still require the planner's tie
rank; they are not removed merely because the inequality is non-strict.

The rule was adversarially tested over all set partitions of four positions
with 32 deterministic random positive weight vectors, and against the
audited matrix action pairs. The artifact reports zero rule violations on all
examined pairs. It is nevertheless not useful at the measured scale: after
excluding singleton/two-candidate closed-form states, the sampled H2-cell
reduction attributable to strict dominance was only `0.1184%`. No dominance
layer was integrated.

## C. Similarity bounds

For normalized posteriors `p` and `q` over the same vocabulary, define

```
d(p, q) = 1/2 * sum_w |p(w) - q(w)|.
```

The positive and negative difference masses are both `d`; the artifact also
records added/removed candidate counts separately. For a fixed action `g`,
`F_g` is a maximum of linear selections with coefficients in `[0, 1]`, so

```
|F_g(p) - F_g(q)| <= d(p, q).
```

Also `|E_g(p)-E_g(q)| = |p(g)-q(g)| <= d(p,q)`. Thus a solved state's action
value gives the exact-safe fixed-action interval

```
F_g(q) in [F_g(p)-d, F_g(p)+d]
E_g(q) in [E_g(p)-d, E_g(p)+d],
```

clamped to the legal ranges `[0,1]` and `[1,2]`.

For the optimal success component, using the solved state's optimal action as
a witness gives

```
F*(p)-d <= F*(q) <= F*(p)+d.
```

For expected guesses, an action that can be optimal at `q` must satisfy
`F_g(p) >= F*(p)-2d`; otherwise its upper success bound is below the solved
state witness's lower success bound. Restricting to this `2d` near-optimal
set gives a safe expected interval from the minimum and maximum solved-state
expected values in that set, expanded by `d`.

The bound implementation was checked against exact matrix H2 values and
optimal selections on weighted neighboring states. Every bounded replay kept
the exact best value after simulated strict skips. It is still too loose for
the measured H3 child distribution: nearest-neighbor distances on completed
support 500/750/1000 ladder samples averaged `0.8567`, `0.8903`, and `0.9181`,
respectively; the high-support strict action-skip ratio was only `0.2715%`.
The curated bounded frontier produced `3.7905%` skips, but it is not a full
curated H3 run and its mean nearest-neighbor distance was `0.8486`. A
bounded solved-state index would add lookup and posterior-distance overhead
without a demonstrated net benefit, so no similarity index was integrated.

## D. Precise query-game reconnaissance

Only the following directly testable ideas are retained:

1. **Feedback-capacity mass bound.** Hardle has at most `K=36` encoded
   feedback codes. An H2 probe can credit at most one legal final-answer mass
   per code, so its success is at most the sum of the largest `min(K, n)` legal
   posterior masses. This is the ISSUE-013 bound and remains exact-safe but
   loose.
2. **Partition refinement monotonicity.** Splitting an H2 feedback block can
   only increase the sum of per-block maxima. With the separate immediate-hit
   condition, this yields the dominance rule tested above.
3. **Shallow-tree leaf capacity.** A depth-`h` exact query tree with at most
   `K` feedback outcomes per query has at most `K^h` terminal feedback paths;
   each path can certify at most one hidden answer. Therefore success is at
   most the sum of the largest `K^h` legal posterior masses, and a positive
   posterior over `n > K^h` answers cannot be guaranteed solved within `h`
   guesses. This is a safe feasibility bound, not an approximation.

These are stated as finite-count or partition inequalities that can be
tested against the existing matrix; no broader literature claim is used.

## Conclusion and boundary

All three proposed optimization directions are falsified as default planner
changes by the current evidence:

- safe partition collapse is exact but low on dominant logical cells and
  slower in the standalone benchmark;
- refinement dominance is exact but removes only a negligible weighted cell
  fraction at representative states;
- similarity bounds are exact-safe but have large distances/gaps and almost no
  strict skips on the completed high-support ladder.

The branch therefore contains research helpers, machine-readable evidence,
tests, and the handoff only. It does not change the planner, default
optimization layers, accepted project state, or any ISSUE-013 controls.
