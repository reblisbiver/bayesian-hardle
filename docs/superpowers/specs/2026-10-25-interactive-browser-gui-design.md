# Bayesian Hardle Interactive Browser GUI Design

## Intent

Provide a local browser acceptance interface for the existing exact Bayesian
Hardle solver. The OWNER should be able to inspect policy trajectories against
a known target and play a human-vs-solver game without reading terminal logs or
having the hidden target leaked during play.

## Goals

- Add a maintainable Streamlit local GUI with two explicit modes:
  known-target strategy comparison and human-vs-solver battle.
- Reuse ISSUE-006's exact feedback, priors, support modes, matrix acceleration,
  MAP, Random, and Max-IG implementations through a shared application/session
  layer used by both CLI and GUI.
- Preserve the 12,974-word full support, existing priors, tie rules, feedback
  semantics, and ten-guess horizon.
- Make all per-turn evidence readable: guess, feedback, candidate count,
  entropy, per-turn decision time, cumulative time, and terminal outcome.
- Provide an exact one-command `uv` launch path and a smoke test for the app
  import/startup surface.

## Non-goals and anti-goals

- No Bayesian theory, vocabulary fairness, feedback semantics, policy meaning,
  or research metric changes.
- No separate display-only solver or GUI-specific approximation.
- No scheduled answer membership or answer leakage in fair modes.
- No supervisor acceptance or modification of `project-control/PROJECT_STATE.md`.
- No browser automation requirement for the automated suite; human acceptance is
  performed through the live local browser UI.

## User-facing design

The app has a short title and two tabs.

### Strategy comparison

The sidebar contains target word, one or more policies, support/prior mode, and
the Run button. The mode selector explains that `full-uniform` is strict
fairness over all legal words, `full-frequency` is a broad non-leaking
human-like prior over the same support, and `curated-2315` is diagnostic and
answer-list-aware. Each selected policy gets a card/column with a prominent
solved/not-solved result, turns, and total decision time, followed by a table
with one row per turn and the required metrics.

### Human vs Solver battle

Before starting, the user chooses the solver policy and solver mode. The hidden
target is sampled uniformly from that mode's allowed support; the UI states
this explicitly, including that full-frequency changes the solver prior but
not the uniform target sampling rule. The target is stored only in the session
service and is absent from all pre-finish public state.

During play, only the human guess input, canonical feedback for that guess,
human progress, and a Give up button are shown. Solver guesses, feedback,
target, and solver candidate counts remain hidden. Once the human solves,
reaches ten guesses, or gives up, the app reveals the target, the full solver
trajectory, and a compact human-vs-solver comparison.

## Architecture

- `src/bayesian_hardle/application.py` owns public session services and result
  value objects. `SolverSession.step()` advances one exact solver turn;
  `run_simulation()` is implemented in terms of it. `BattleSession` advances
  one human turn and one hidden solver turn, exposing a redacted public view
  until finish.
- `src/bayesian_hardle/cli.py` remains the command-line adapter and imports the
  shared application functions. Existing CLI behavior and imports remain
  compatible.
- `src/bayesian_hardle/streamlit_app.py` is a thin rendering/input adapter. It
  creates the same repository, mode, policy, and session services; it contains
  no feedback, posterior, or policy algorithm.
- `tests/test_application_sessions.py` pins target validation, known-target
  execution, battle anti-leak transitions, and reveal timing.
- `tests/test_streamlit_smoke.py` verifies the module can be imported and the
  app entry point can be discovered using the uv-managed dependency set.

## Dependency and launch decision

Streamlit is added as a project dependency so the OWNER can launch from the
working repository with:

```bash
uv run --with . streamlit run src/bayesian_hardle/streamlit_app.py
```

The GUI uses the existing `wordfreq==3.1.1` dependency for full-frequency and
the existing NumPy matrix cache for Max-IG. The first full-support Max-IG use
may build the exact cache under `.cache/bayesian_hardle`; this is shown as a
normal local preparation step, not a different solver.

## Open implementation calls settled here

- Battle target support follows the selected solver mode's support, but target
  sampling is always uniform. Thus full-frequency means a uniform hidden target
  over all 12,974 legal words with a frequency-weighted solver prior.
- Random remains available in both modes and is seeded by the session service;
  MAP and Max-IG are the primary acceptance choices.
- Exact Bayes-optimal is not offered because the current accepted project state
  explicitly limits it to tractable small vocabularies.
- Streamlit session state stores only the opaque `BattleSession` object; all
  rendered state comes from its redacted public view.
