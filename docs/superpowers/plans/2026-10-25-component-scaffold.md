# Bayesian Hardle Component Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Initialize the five accepted Bayesian Hardle architecture groups as typed, testable Python interfaces and value objects without implementing research semantics.

**Architecture:** Use five focused package modules matching Game, Belief, Information, Decision, and Evaluation. Value objects carry state; `typing.Protocol` defines behavior contracts. A single scaffold integration test uses test doubles to prove the information path without implementing the algorithms themselves.

**Tech Stack:** Python standard library, `dataclasses`, `typing.Protocol`, `unittest`.

**Spec:** `project-control/issues/ISSUE-003-component-scaffold.md`

## Global Constraints

- Do not implement real Hardle feedback semantics, Bayesian numeric updates, entropy/IG calculations, or Bellman recursion.
- Do not introduce ML/RL/MCTS.
- Keep shared semantics centralized; policies may not duplicate Game Model or posterior logic.
- Preserve current project-control discipline and append-only journal.

## Review Focus

- Interfaces accidentally contain algorithmic behavior that belongs to later issues.
- Module dependencies form cycles or allow Evaluation to alter game semantics.
- Decision policies bypass shared Game/Belief interfaces.
- Value objects accept structurally invalid state such as negative remaining guesses or unnormalized assumptions encoded as facts.
- Existing project scaffold and imports regress.

---

### Task 1: Create package architecture and value objects

**Files:**
- Create: `src/bayesian_hardle/game.py`
- Create: `src/bayesian_hardle/belief.py`
- Create: `src/bayesian_hardle/information.py`
- Create: `src/bayesian_hardle/decision.py`
- Create: `src/bayesian_hardle/evaluation.py`
- Modify: `src/bayesian_hardle/__init__.py`
- Test: `tests/test_component_contracts.py`

**Interfaces:**
- Produces all public types named in ISSUE-003.

- [ ] Write failing import/shape tests for every required type.
- [ ] Run the focused tests and confirm failure.
- [ ] Implement minimal dataclasses and Protocol definitions only.
- [ ] Run focused tests and confirm pass.
- [ ] Commit semantic checkpoint.

### Task 2: Prove component handoff with test doubles

**Files:**
- Modify: `tests/test_component_contracts.py`

**Interfaces:**
- Consumes `BeliefState`, `DecisionState`, Policy, FeedbackEngine, PosteriorUpdater, and evaluation contracts from Task 1.
- Produces no new production behavior.

- [ ] Add a failing integration-style scaffold test that passes a fake belief through a fake policy to a fake feedback engine and fake posterior updater, then verifies horizon decrement and evaluation observation boundaries.
- [ ] Run the focused test and confirm the intended failure.
- [ ] Add only the minimal structural glue needed for the contracts to compose; do not add real algorithms.
- [ ] Run focused and full test suites.
- [ ] Commit semantic checkpoint.

### Task 3: Document the frozen component map and handoff

**Files:**
- Modify: `README.md`
- Append: `project-control/JOURNAL.md`

**Interfaces:**
- Documents the five groups and runtime information flow from ISSUE-003.

- [ ] Add a compact component map and seven-step information flow to README.
- [ ] Run `python -m unittest discover -s tests -v`, import/compile checks, `git diff --check`, and `git status --short --branch`.
- [ ] Append one `[EXECUTION REPORT]` with branch, base SHA, result SHA, changed files, verification evidence, and unresolved semantics.
- [ ] Commit final handoff metadata if needed and leave status `READY_FOR_REVIEW`.
