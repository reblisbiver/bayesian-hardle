# Bayesian Hardle Interactive Browser GUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Streamlit acceptance GUI with known-target comparison and anti-leak human-vs-solver battle modes on top of ISSUE-006's exact solver.

**Architecture:** Extract the solver loop into `application.py` session services. Keep `cli.py` as an adapter, and make `streamlit_app.py` a thin input/rendering layer that consumes those services. Battle public state is explicitly redacted until human finish/give-up.

**Tech Stack:** Python 3.9+, existing NumPy/wordfreq exact core, Streamlit, unittest, uv.

**Spec:** `docs/superpowers/specs/2026-10-25-interactive-browser-gui-design.md`

## Global Constraints

- Preserve full support = 12,974 legal words for full-uniform/full-frequency.
- Preserve existing Hardle feedback semantics, priors, tie rules, exact Max-IG calculations, and ten-guess horizon.
- GUI must call shared solver/session services; do not duplicate algorithms in the GUI.
- Before human battle finish/give-up, do not expose solver guesses, solver feedback, hidden target, or target-leaking details.
- Do not modify `project-control/PROJECT_STATE.md`; append the final `EXECUTION REPORT` to `project-control/JOURNAL.md` only after verification.
- Leave the worktree clean and hand off `READY_FOR_REVIEW` with exact SHA, launch command, tests, and limitations.

## Review Focus

- A legal word outside curated-2315 (`aahed`) must run in full-uniform MAP and Max-IG without silently switching support; pin in application tests.
- Full-frequency must retain all legal words with positive mass while the GUI remains runnable; pin with an injected deterministic frequency prior in service tests.
- Invalid or non-legal target/guess input must be rejected without changing session state; pin in application tests.
- Battle public snapshots must contain no hidden target or solver trajectory before finish, while human feedback remains canonical; pin each transition.
- Solver completion before human completion must not reveal its path; pin by using a deterministic solver/target fixture and finishing later.

### Task 1: Shared solver session layer

**Files:**
- Create: `src/bayesian_hardle/application.py`
- Modify: `src/bayesian_hardle/cli.py`
- Test: `tests/test_application_sessions.py`

**Interfaces:**
- Produces `TurnResult`, `SimulationResult`, `SolverSession`, `run_simulation`, `BattleSession`, `BattlePublicState`, `HumanTurnResult`, and `BattleOutcome` from `bayesian_hardle.application`.
- Consumes existing `fairness`, `game`, `belief`, `decision`, `accelerated`, and `information` public services.
- `SolverSession.step() -> TurnResult` advances one solver decision/feedback/update and stops after solve or horizon.
- `BattleSession.submit_human_guess(guess: str) -> HumanTurnResult` returns human-only feedback before finish and a redacted/public result after each turn.
- `BattleSession.public_state() -> BattlePublicState` returns `target=None` and `solver_turns=()` before finish; after finish it returns the target and full solver trajectory.

- [ ] **Step 1: Write failing session tests**

  Add tests for `aahed` validation and full-uniform MAP/Max-IG runs, target rejection outside the selected curated support, battle human-only feedback, pre-finish redaction, finish/give-up reveal, and a solver-that-finishes-early fixture whose path remains hidden until human finish.

- [ ] **Step 2: Run the focused tests and verify the expected missing-service failure**

  Run `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue007-pycache python3 -m unittest tests.test_application_sessions -v`.
  Expected: collection/import failure because `bayesian_hardle.application` does not yet exist.

- [ ] **Step 3: Implement the minimal shared services**

  Move the existing context/turn construction and simulation loop into `application.py`, preserve CLI-compatible dataclass fields and serialization, add a stepwise solver session, then add a battle wrapper that samples uniformly from the selected mode support and redacts solver internals in its public state. Keep target and solver context private to the battle object.

- [ ] **Step 4: Re-run focused tests and the existing CLI tests**

  Run the focused test command and `PYTHONPYCACHEPREFIX=/tmp/bayesian-hardle-issue007-pycache python3 -m unittest tests.test_cli_acceptance -v`.
  Expected: all focused/session and existing CLI acceptance tests pass.

- [ ] **Step 5: Commit the shared application layer**

  ```bash
  git add src/bayesian_hardle/application.py src/bayesian_hardle/cli.py tests/test_application_sessions.py
  git commit -m "feat: extract reusable solver and battle sessions"
  ```

### Task 2: Streamlit UI and launch dependency

**Files:**
- Create: `src/bayesian_hardle/streamlit_app.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Test: `tests/test_streamlit_smoke.py`

**Interfaces:**
- `streamlit_app.py` exposes `main() -> None` and imports only shared application services for solver behavior.
- The app renders the two modes described in the design spec, with mode explanations, readable cards/tables, and anti-leak battle rendering.
- The exact OWNER launch command is `uv run --with . streamlit run src/bayesian_hardle/streamlit_app.py`.

- [ ] **Step 1: Write failing smoke/contract tests**

  Assert the app module exposes `main`, the launch path is present in README, and the UI source contains the two user-facing mode labels and no direct policy/feedback implementation.

- [ ] **Step 2: Run the smoke test to verify the dependency/import failure**

  Run `uv run --with . python -m unittest tests.test_streamlit_smoke -v`.
  Expected: failure because Streamlit and the app module have not yet been added.

- [ ] **Step 3: Add Streamlit and implement the thin UI**

  Add a bounded Streamlit dependency, render comparison cards with per-turn tables and timing metrics, store only the session service in `st.session_state`, and render battle solver details only from a finished public state. Disable unsupported exact Bayes-optimal selection by omitting it and explain the tractability boundary.

- [ ] **Step 4: Run the smoke test and launch help check**

  Run `uv run --with . python -m unittest tests.test_streamlit_smoke -v` and `uv run --with . streamlit run src/bayesian_hardle/streamlit_app.py --server.headless true --server.port 8505` with a bounded startup check.
  Expected: import smoke passes and Streamlit reports the app is serving on port 8505.

- [ ] **Step 5: Commit the UI slice**

  ```bash
  git add pyproject.toml README.md src/bayesian_hardle/streamlit_app.py tests/test_streamlit_smoke.py
  git commit -m "feat: add Streamlit acceptance GUI"
  ```

### Task 3: Full verification and audited handoff

**Files:**
- Modify: `project-control/JOURNAL.md`
- Create: `docs/acceptance/issue_007_gui_sample_transcript.md`

**Interfaces:**
- No research state advancement; the journal entry records executor evidence only.
- The sample transcript records commands, observed outputs, and evidence layers without claiming browser/business acceptance.

- [ ] **Step 1: Run the complete verification set**

  Run the full unittest suite, compile/import checks, `git diff --check`, the exact `uv` launch command smoke check, known-target `aahed` MAP and Max-IG service runs, and battle anti-leak tests.

- [ ] **Step 2: Record the sample acceptance transcript and append the execution report**

  Record exact test/launch outputs and limitations in the transcript; append an `EXECUTION REPORT` to `project-control/JOURNAL.md` with branch, commits, evidence paths, launch command, and explicit pending supervisor review. Do not edit `PROJECT_STATE.md`.

- [ ] **Step 3: Verify clean handoff state**

  Re-run status, branch, HEAD, `git diff --check`, and the final full test suite. Expected: clean `codex/issue-007-interactive-gui` worktree, all tests passing, no change to `PROJECT_STATE.md`, and the report points to the exact checkpoint SHA.

- [ ] **Step 4: Commit the audited handoff**

  ```bash
  git add project-control/JOURNAL.md docs/acceptance/issue_007_gui_sample_transcript.md
  git commit -m "docs: record issue-007 GUI execution report"
  ```

