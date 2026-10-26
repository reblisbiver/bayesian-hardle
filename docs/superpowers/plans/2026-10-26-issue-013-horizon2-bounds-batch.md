# ISSUE-013 Horizon-2 Bounds and Batch Fusion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (or superpowers:subagent-driven-development) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce exact horizon-3 child H2 wall time through measured ragged block fusion while proving and recording the capacity bound even though the bound is too loose to enable on the ISSUE-012 ladder.

**Architecture:** Keep the scalar/reference planner and existing single-child H2 matrix evaluator as semantic oracles. Add a general exact-safe capacity-bound helper for tests and benchmark accounting, add a ragged matrix block evaluator that shares code gathering across a bounded set of H2 children, and integrate that evaluator only at H3 branch flush points where branch-and-bound remains exact. The bound remains analysis-only unless fresh measurements demonstrate strict net benefit.

**Tech Stack:** Python 3.9+, `unittest`, NumPy, `cProfile`/`pstats`, JSON and Markdown benchmark artifacts, existing Hardle feedback and planner instrumentation.

**Spec:** `docs/superpowers/specs/2026-10-26-issue-013-horizon2-bounds-batch-design.md`

## Global Constraints

- Preserve solve-probability-first, expected-guesses-second lexicographic planning exactly.
- No heuristic approximation inside `ExactBayesOptimalPlanner`.
- Preserve deterministic tie behavior and scalar/reference equivalence.
- The capacity bound may only prune on a strict success upper-bound loss; equality stays live.
- Ragged blocks use no padded child-support tensor and flush before exact branch-and-bound checks.
- Do not add a cache solely because ISSUE-012 measured duplicates; existing memoization remains the only cache.
- Preserve the deterministic support 32/50/100/200/500 ladder and bounded curated 2,315 × 12,974 × h=3 probe.
- Do not modify the canonical checkout or `project-control/PROJECT_STATE.md`.
- Keep `project-control/JOURNAL.md` append-only and report executor state as awaiting supervisor review.

## Review Focus

- A child with fewer than 36 legal answers and duplicate-letter feedback: the capacity bound equals total legal mass and never underestimates exact H2 values; owned by Task 1 tests.
- A weighted child with more than 36 legal answers and a non-answer probe: block and scalar values agree and expected guesses remain `2 - p(first_guess)`; owned by Tasks 1 and 2 tests.
- A legal list whose order differs from sorted order with equal values: block selection uses the existing canonical tie rank; owned by Task 3 tests.
- An H3 action where branch-and-bound stops after a partial branch prefix: block flushes do not evaluate later branches and the exact value remains unchanged; owned by Task 3 tests.
- A large child block: reported logical cells and temporary bytes stay ragged and below the declared block-memory budget; owned by Tasks 2 and 4 tests/artifacts.

---

### Task 1: Add and falsify-proof the capacity bound helper

**Files:**
- Modify: `src/bayesian_hardle/accelerated.py`
- Modify: `tests/test_accelerated_maxig.py`
- Modify: `tests/test_decision_behavior.py`

**Interfaces:**
- Produces `ExactFeedbackCodeMatrix.horizon_two_capacity_upper_bound(answer_words, weights, legal_final_answers) -> float` with a docstring proving the finite-code top-mass bound and validation matching the existing normalized-weight contract.
- Produces `ExactFeedbackCodeMatrix.horizon_two_action_capacity_upper_bound(first_guess, answer_words, weights, legal_final_answers) -> float` for the tighter per-action answer-slot bound used by benchmark accounting.
- The helpers are analysis-only in this issue; they must not alter the planner's default pruning path.

- [ ] **Step 1: Write failing adversarial and weighted-random tests**

  Add tests that construct duplicate-letter Hardle matrices, answer-only and probe-inclusive legal sets, and deterministic weighted posteriors. For every legal first guess, assert the exact scalar/matrix H2 success is no greater than the capacity bound and the action-specific bound; assert the root branch-weighted bound is no less than the exact branch-weighted H2 value.

- [ ] **Step 2: Run the focused tests and verify they fail because the helpers are absent**

  Run: `PYTHONPATH=src PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue013-red-pycache python3 -m unittest tests.test_accelerated_maxig tests.test_decision_behavior -v`

  Expected: FAIL with missing bound-helper attributes.

- [ ] **Step 3: Implement the two bound helpers in `src/bayesian_hardle/accelerated.py`**

  Filter non-negative normalized masses to legal final answers, sort descending, and sum the largest `min(code_count, eligible_count)` masses. For an answer first guess, include its mass and take the largest `code_count - 1` masses from the other legal answers; for a non-answer use the global top-code-count sum. Document why each feedback code contributes at most one final-answer mass and why root branch weighting is safe.

- [ ] **Step 4: Run the focused tests and verify the bound never underestimates**

  Run the same focused command. Expected: PASS, including all adversarial/random states and exact root branch-weighted checks.

- [ ] **Step 5: Commit the proof-oriented bound layer**

  Commit with: `git add src/bayesian_hardle/accelerated.py tests/test_accelerated_maxig.py tests/test_decision_behavior.py && git commit -m "research: prove exact horizon-two capacity bounds"`

---

### Task 2: Add the exact ragged H2 block evaluator

**Files:**
- Modify: `src/bayesian_hardle/accelerated.py`
- Modify: `tests/test_accelerated_maxig.py`
- Modify: `tests/test_decision_behavior.py`

**Interfaces:**
- Produces `ExactFeedbackCodeMatrix.horizon_two_values_block(guesses, answer_words_batch, weights_batch, legal_final_answers) -> numpy.ndarray` with shape `(children, guesses, 2)` and float64 last axis `(success_probability, expected_guesses)`.
- Produces `ExactFeedbackCodeMatrix.horizon_two_block_temporary_bytes(child_count, guess_count, total_answer_count) -> int` or an equivalent stable accounting interface used by planner stats and benchmark artifacts.
- The existing `horizon_two_values` output and validation remain unchanged.

- [ ] **Step 1: Write failing block-equivalence tests**

  Add duplicate-letter and deterministic random weighted tests comparing every block cell to the existing scalar matrix evaluator and the scalar planner/reference planner. Include blocks with heterogeneous child support lengths, non-answer probes, legal-final subsets, and one-child blocks.

- [ ] **Step 2: Run the focused tests and verify the block method is absent**

  Run: `PYTHONPATH=src PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue013-block-red-pycache python3 -m unittest tests.test_accelerated_maxig tests.test_decision_behavior -v`

  Expected: FAIL with the block method absent.

- [ ] **Step 3: Implement the ragged block reduction**

  Concatenate answer indices, eligible weights, and child ids; gather `uint8` feedback codes for all legal rows once; for each legal row apply `np.maximum.at` into `child_id * code_count + code`; sum code maxima per child and construct expected values from each child's first-guess posterior mass. Do not create a padded `(children, guesses, max_support)` tensor. Track the logical cells and a conservative sum of simultaneously live temporary arrays.

- [ ] **Step 4: Run the block-equivalence tests and a memory sanity check**

  Run the focused command plus a small inline benchmark over heterogeneous supports. Expected: PASS; block values match within `1e-12`, logical cells equal `guess_count * sum(child_support)`, and reported temporary bytes are finite and bounded by the declared block budget.

- [ ] **Step 5: Commit the exact block evaluator**

  Commit with: `git add src/bayesian_hardle/accelerated.py tests/test_accelerated_maxig.py tests/test_decision_behavior.py && git commit -m "perf: add exact ragged horizon-two child batches"`

---

### Task 3: Integrate bounded child blocks without changing planner semantics

**Files:**
- Modify: `src/bayesian_hardle/decision.py`
- Modify: `tests/test_decision_behavior.py`

**Interfaces:**
- Adds optimization layer `horizon_two_child_batch` to `ExactBayesOptimalPlanner.ALL_OPTIMIZATION_LAYERS`.
- Adds a bounded batch size constant (initially 8) and stats for child block calls, child count, logical cells, peak temporary bytes, exact child solves, and bound-only skips.
- Keeps `horizon_two_batch_*` counters compatible while adding block-specific counters to root action records and `instrumentation()`.

- [ ] **Step 1: Write failing planner equivalence and control-flow tests**

  Add tests comparing the reference planner, existing scalar/matrix control, and the new block-enabled planner on deterministic weighted H3 states. Assert identical selected guesses and values, canonical tie behavior with permuted legal input, exact branch-and-bound pruning, child request accounting, and zero bound-only skips because the bound is analysis-only.

- [ ] **Step 2: Run the focused tests and verify the new layer is absent**

  Run: `PYTHONPATH=src PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue013-planner-red-pycache python3 -m unittest tests.test_decision_behavior -v`

  Expected: FAIL on the new optimization-layer/stat assertions.

- [ ] **Step 3: Implement sequential block collection and exact flushes**

  In H3 `_guess_value`, collect non-winning H2 child states in branch order up to the bounded block size, flush before a winning branch and at the end, and flush before applying the existing branch-and-bound test. Reuse existing cache/closed-form fallbacks for ineligible children; for eligible children call the block matrix evaluator, select each best action with the existing tolerance/tie rank, and populate the same value/planner caches. Record child H2 requests, exact solves, logical cells, block memory, and zero bound-only skips without changing the accepted objective.

- [ ] **Step 4: Run planner equivalence and full existing tests**

  Run: `PYTHONPATH=src PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue013-task3-pycache python3 -m unittest discover -s tests -v`. Expected: all baseline tests pass with no new failures; block/control selections and values match.

- [ ] **Step 5: Commit the planner integration**

  Commit with: `git add src/bayesian_hardle/decision.py tests/test_decision_behavior.py && git commit -m "perf: fuse exact horizon-two child planning blocks"`

---

### Task 4: Build the before/after measurement ladder and artifacts

**Files:**
- Create: `experiments/issue_013_horizon2_bounds_batch.py`
- Create: `experiments/results/issue_013_horizon2_bounds_batch.json`
- Create: `experiments/results/issue_013_horizon2_bounds_batch_summary.md`
- Create: `experiments/results/issue_013_profiles/`

**Interfaces:**
- The driver reports one machine-readable row per completed/control/after case with support, legal count, horizon, total/matrix/select time, root actions, branches, child requests, exact child H2 solves, bound-only skips, H2 logical cells, block calls/children, peak temporary bytes, root prune ratio, and declared timeout status.
- The driver preserves control layers from ISSUE-012, records the bound-only analysis separately, and does not treat a timeout as completion.

- [ ] **Step 1: Add a deterministic worker and artifact validation tests/helpers**

  Reuse ISSUE-012 word sampling and legal-list construction for support 32/50/100/200/500, add 750/1000 when the declared per-row budget allows, and add the curated 2,315 × 12,974 h=3 probe with an explicit bounded timeout. Add profile bucket extraction and JSON/Markdown consistency checks.

- [ ] **Step 2: Run the control ladder before measuring the integrated fusion**

  Run the control variant with the ISSUE-012 layers and record fresh before rows/profiles. Confirm the control reproduces the known support=500 dominant child-H2 timing and no bound-only skips.

- [ ] **Step 3: Run the block-enabled ladder and bounded curated probe**

  Run the after variant with `horizon_two_child_batch`; retain only rows whose worker completed within budget as completed rows, and record timeout rows verbatim. Record both logical H2 cells and block temporary-memory accounting.

- [ ] **Step 4: Compare before/after and decide promotion**

  Promote the layer in the default planner only if selected values/guesses match, the fresh ladder has a material net wall-time improvement, logical cells do not inflate beyond the bounded flush allowance, and temporary memory stays within the declared budget. Otherwise disable it by default and report the negative result.

- [ ] **Step 5: Commit benchmark code and artifacts**

  Commit with: `git add experiments/issue_013_horizon2_bounds_batch.py experiments/results/issue_013_horizon2_bounds_batch.json experiments/results/issue_013_horizon2_bounds_batch_summary.md experiments/results/issue_013_profiles && git commit -m "research: measure horizon-two bounds and child fusion"`

---

### Task 5: Produce the append-only handoff and final verification

**Files:**
- Create: `project-control/issues/ISSUE-013-horizon2-bounds-batch.md`
- Modify append-only: `project-control/JOURNAL.md`
- Modify as needed: `docs/superpowers/specs/2026-10-26-issue-013-horizon2-bounds-batch-design.md`

- [ ] **Step 1: Validate source, tests, and artifacts**

  Run fresh full tests, `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue013-final-pycache python3 -m compileall -q src tests experiments`, package import/version check, JSON/Markdown artifact validator, and `git diff --check`.

- [ ] **Step 2: Verify repository boundaries**

  Confirm branch `codex/issue-013-horizon2-bounds-batch`, base/result commits, worktree path, canonical checkout status untouched, and `sha256sum project-control/PROJECT_STATE.md` unchanged from the ISSUE-012 handoff.

- [ ] **Step 3: Write the executor handoff**

  Record the largest completed exact support/horizon, every timeout, the bound's zero-skip result, the before/after child-H2 timing movement, root prune ratio, exact block equivalence, temporary memory, evidence paths, and the explicit `READY_FOR_REVIEW`/supervisor-review boundary. Do not advance `PROJECT_STATE.md`.

- [ ] **Step 4: Commit the handoff and re-run final verification**

  Commit with: `git add project-control/issues/ISSUE-013-horizon2-bounds-batch.md project-control/JOURNAL.md docs/superpowers/specs/2026-10-26-issue-013-horizon2-bounds-batch-design.md && git commit -m "docs: hand off issue-013 horizon-two optimization"`, then rerun the final verification commands and report exact outputs.

---

## Self-review

- Spec coverage: Priority A is Task 1 and Task 4 bound accounting; Priority B is Tasks 2–4; Priority C is explicitly measured and recorded as zero bound-only skips; ladder, larger intermediates, curated timeout, tests, artifacts, journal, READY_FOR_REVIEW, and unchanged project state are Tasks 4–5.
- Exactness: every new value path is compared to the existing scalar matrix/reference planner; branch blocks flush before exact pruning; tie equality remains live.
- Memory: the chosen evaluator is ragged, reports logical cells separately from temporary arrays, and has a bounded block size.
- Scope: no cache redesign, root partition micro-optimization, algorithm change, or acceptance-state advancement is included.
