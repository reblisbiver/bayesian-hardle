# ISSUE-011 exact planner hotspot research Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move exact horizon-2 planning beyond the ISSUE-010 support=20 frontier while explaining the remaining exact computation with reproducible profiling.

**Architecture:** Add a proof-oriented scalar horizon-2 evaluator first, then an exact `ExactFeedbackCodeMatrix` batch evaluator that computes per-feedback-code legal-candidate maxima for every legal first guess. Reuse the existing scalar reference planner, public `BeliefState`, deterministic lexicographic tie resolution, and opt-in optimization layers; remove only measured redundant mass/eligibility work.

**Tech Stack:** Python 3.9+, `unittest`, NumPy, `cProfile`/`pstats`, JSON and Markdown benchmark artifacts, existing Hardle feedback and matrix classes.

**Spec:** `docs/superpowers/specs/2026-10-26-issue-011-exact-planner-hotspots-design.md`

## Global Constraints

- Preserve the accepted lexicographic objective exactly: maximize finite-horizon solve probability first; among ties minimize expected guesses until solve/horizon termination.
- No heuristic approximation inside `ExactBayesOptimalPlanner`.
- Keep `ExactBayesOptimalReferencePlanner` as the oracle on tractable states.
- Do not modify the canonical checkout or `project-control/PROJECT_STATE.md`.
- Keep `project-control/JOURNAL.md` append-only.
- A bounded timeout is evidence of a measured limit, not an exact-feasibility claim.

## Review Focus

- A weighted state where a non-answer probe partitions answers but only legal final candidates may receive horizon-2 credit; test scalar and batch values.
- A winning first guess versus a non-winning branch; test `expected = 2 - p(g)` and exact success mass.
- Duplicate-letter Hardle outcomes; test matrix batch values against scalar feedback.
- A legal list whose order differs from sorted order and equal-valued actions; test deterministic tie rank.
- Matrix-ineligible/custom feedback inputs; test exact scalar fallback and unchanged public beliefs.

---

### Task 1: Add proof-oriented horizon-2 scalar tests

**Files:**
- Modify: `tests/test_decision_behavior.py`
- Test only; no production changes in this task.

**Interfaces:**
- Consumes: existing `ExactBayesOptimalReferencePlanner`, `ExactBayesOptimalPlanner`, `DecisionState`, `BeliefState`, and Hardle fixtures.
- Produces: named tests for the scalar closed-form value, expected-guess identity, legal-final-candidate restriction, random weighted equivalence, and tie behavior.

- [ ] **Step 1: Write tests for the scalar formula and random equivalence.** Add tests that assert for hand-checkable weighted states:
  - `success(g) = p(g) + sum(nonwinning branch max legal candidate mass)`;
  - `expected(g) = 2 - p(g)` when `g` is a legal remaining answer and `2` otherwise;
  - a probe cannot receive credit from an illegal final candidate;
  - deterministic random weighted supports compare every legal action's value with the reference planner at horizon 2.
- [ ] **Step 2: Run the focused tests and verify RED.** Run `PYTHONPATH=src PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue011-pycache python3 -m unittest tests.test_decision_behavior -v`; expect failure because the new horizon-2 layer and counters do not yet exist.
- [ ] **Step 3: Commit the failing tests.** Use `git add tests/test_decision_behavior.py && git commit -m "test: specify exact horizon-two values"`.

### Task 2: Implement and verify the exact scalar horizon-2 evaluator

**Files:**
- Modify: `src/bayesian_hardle/decision.py`
- Test: `tests/test_decision_behavior.py`

**Interfaces:**
- Consumes: `DecisionState`, normalized mass tables, exact transition branches, legal guesses, and the accepted tie tolerance.
- Produces: `horizon_two_closed_form` optimization layer; `_horizon_two_guess_value(...) -> PlannerValue`; deterministic `_horizon_two_best_guess(...) -> str`; instrumentation counters for scalar horizon-2 evaluations.

- [ ] **Step 1: Add the new layer and counters.** Keep existing ISSUE-010 layer behavior intact, add `horizon_two_closed_form` after `branch_and_bound`, and add stable counters for scalar horizon-2 value hits/actions.
- [ ] **Step 2: Implement `_horizon_two_guess_value(...)`.** Use the existing exact `_transition_branches` result. For each branch, add the largest mass among branch members whose target is in `candidate_guesses`; use the winning branch naturally as `p(g)`, and return `(success, 2 - p(g))` with `p(g)=0` for non-answer probes. Do not call recursive planning or posterior construction.
- [ ] **Step 3: Implement `_horizon_two_best_guess(...)`.** Evaluate every legal first guess with the scalar formula, cache complete values under the same canonical state/action keys, and resolve values with the existing lexicographic comparator and legal-order tie rank.
- [ ] **Step 4: Run the focused tests and verify GREEN.** Run the Task 1 command; expect all new formula/equivalence tests and existing decision tests to pass.
- [ ] **Step 5: Commit the scalar implementation.** Use `git add src/bayesian_hardle/decision.py tests/test_decision_behavior.py && git commit -m "feat: add exact horizon-two scalar evaluator"`.

### Task 3: Add and verify the exact matrix batch evaluator

**Files:**
- Modify: `src/bayesian_hardle/accelerated.py`
- Modify: `src/bayesian_hardle/decision.py`
- Modify: `tests/test_decision_behavior.py`
- Test: `tests/test_accelerated_maxig.py` if matrix helper coverage belongs there.

**Interfaces:**
- Consumes: `ExactFeedbackCodeMatrix`, support words, normalized weights, and legal guesses.
- Produces: an exact batch helper returning one `(success, expected)` value per legal guess; `horizon_two_batch` optimization layer; batch hit/action/cell counters.

- [ ] **Step 1: Write the batch equivalence tests.** Assert batch values equal scalar formula values on duplicate-letter fixtures, weighted random supports, legal subsets, and the full curated matrix's sampled rows; assert batch and reference planners select the same guess at horizon 2.
- [ ] **Step 2: Run the focused tests and verify RED.** Run the focused decision/accelerated commands; expect failure because the batch layer/helper is absent.
- [ ] **Step 3: Implement the exact matrix helper.** For each matrix row, use `np.maximum.at` over the finite feedback-code alphabet on weights restricted to legal answer candidates; sum code maxima for solve probability and use `2 - p(g)` for expected guesses. Return values aligned to the caller's legal order. Do not use an approximation, heuristic threshold, or altered feedback encoding.
- [ ] **Step 4: Wire batch selection into the planner.** Enable batch only when the exact Hardle engine, matrix, word length, legal guesses, and support are compatible; otherwise use the scalar horizon-2 evaluator. Preserve existing tie rank and public state semantics.
- [ ] **Step 5: Run the focused tests and verify GREEN.** Run all new formula, batch, duplicate-letter, and reference-equivalence tests.
- [ ] **Step 6: Commit the batch implementation.** Use `git add src/bayesian_hardle/accelerated.py src/bayesian_hardle/decision.py tests/test_decision_behavior.py tests/test_accelerated_maxig.py && git commit -m "feat: batch exact horizon-two action values"`.

### Task 4: Remove measured redundant mass/eligibility work

**Files:**
- Modify: `src/bayesian_hardle/decision.py`
- Modify: `tests/test_decision_behavior.py`

**Interfaces:**
- Consumes: the exact scalar and batch evaluators from Tasks 2–3.
- Produces: transition calls that accept already-computed mass/eligibility data where safe; counters/tests proving public `BeliefState` and reference values are unchanged.

- [ ] **Step 1: Add regression assertions for transition/canonicalization reuse.** Exercise a medium weighted state and assert the optimized planner's values/guess still equal the reference while the new reuse counters show no repeated matrix eligibility check per branch.
- [ ] **Step 2: Run the focused test and verify RED if the counter/API is absent.** Use the same `unittest` environment and assert the expected missing counter or pre-optimization count.
- [ ] **Step 3: Thread one normalized mass table and matrix-eligibility decision through `_guess_value`, `_transition_branches`, and `_posterior_for_branch`.** Do not alter scalar fallback semantics or public observation history.
- [ ] **Step 4: Run the focused tests and verify GREEN.** Confirm formula/batch/reference equivalence and unchanged existing tests.
- [ ] **Step 5: Commit the measured reuse change.** Use `git add src/bayesian_hardle/decision.py tests/test_decision_behavior.py && git commit -m "perf: reuse exact planner mass and matrix checks"`.

### Task 5: Expand benchmark/profiling artifacts and conditional diagnostics

**Files:**
- Modify: `experiments/issue_010_exact_scaling.py` or create `experiments/issue_011_exact_hotspots.py` if a separate artifact is clearer.
- Create: `experiments/results/issue_011_exact_hotspots.json`
- Create: `experiments/results/issue_011_exact_hotspots_summary.md`
- Create: `experiments/results/issue_011_profiles/` profile outputs.
- Modify: `tests/test_project_scaffold.py` only if artifact contract tests are needed.

**Interfaces:**
- Consumes: planner instrumentation, deterministic vocabulary samples, and cProfile/pstats.
- Produces: machine-readable before/after rows with support/legal/horizon, runtime, states/actions/branches, pruning, cache stats, matrix bytes, closed-form/batch hits, and explicit hotspot call/time breakdowns for mass tables, canonical keys, matrix eligibility, transitions/grouping, posterior construction, recursion/state expansion, cache handling, sorting, and NumPy work.

- [ ] **Step 1: Add deterministic cases.** Preserve ISSUE-010 cases and add support 32/50/100/200/500 horizon-2 rows plus a useful support-32 horizon-3 row, with explicit per-worker budgets and deterministic seeds.
- [ ] **Step 2: Add profile extraction and Markdown tables.** Parse selected cProfile outputs into JSON function rows with calls, primitive calls, internal time, and cumulative time; keep bounded timeout rows explicit.
- [ ] **Step 3: Run before/after benchmark variants.** Record ISSUE-010 ladder, scalar horizon-2, exact batch horizon-2, and any measured reuse variant. Run a bounded full 2,315 × 12,974 horizon-2 probe first; only run horizon 3 if horizon 2 completes.
- [ ] **Step 4: Add the diagnostic feedback-fattening comparison if lightweight.** Compare branch counts/support sizes for the same sampled guesses under Hardle `(exact, misplaced)` codes versus a position-level Wordle pattern, clearly labeling it diagnostic and non-semantic.
- [ ] **Step 5: Commit benchmark scripts and artifacts.** Use a semantic commit whose message names the measured frontier and exact batch result.

### Task 6: Final verification and control-plane handoff

**Files:**
- Modify: `project-control/JOURNAL.md` (append only)
- Create: `project-control/issues/ISSUE-011-exact-planner-hotspots.md` if the repository issue format requires a standalone handoff.
- Modify: no `project-control/PROJECT_STATE.md`.

- [ ] **Step 1: Run fresh verification.** Run the full unittest suite, `compileall`, import/version check, `git diff --check`, and the benchmark artifact validators.
- [ ] **Step 2: Verify exact boundaries.** Confirm reference equivalence on deterministic random weighted states, no heuristic path in the exact planner, selected largest completed support/horizon, timeout interpretation, branch/worktree, commit list, and unchanged canonical `PROJECT_STATE.md`.
- [ ] **Step 3: Append one READY_FOR_REVIEW executor handoff.** Include base SHA, branch/worktree, result commit(s), evidence paths, before/after timings, largest exact completed case, remaining bottleneck, and explicit supervisor review requirement.
- [ ] **Step 4: Commit the append-only handoff.** Use `git add project-control/JOURNAL.md project-control/issues/ISSUE-011-exact-planner-hotspots.md ... && git commit -m "docs: hand off issue-011 exact planner hotspots"`.
