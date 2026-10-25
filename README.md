# Bayesian Hardle

Bayesian Hardle is a research codebase for studying Bayesian reasoning in a
Hardle-style word-feedback environment.

The repository is currently at the control-plane initialization milestone.
The formal communication and audit records live in
[`project-control/`](project-control/README.md). No algorithm, model, or
experiment is accepted until a supervisor review records acceptance.

## Layout

- `src/bayesian_hardle/` — package code.
- `tests/` — behavior-oriented tests.
- `experiments/` — reproducible experiment inputs, runners, and outputs.
- `scripts/` — small operational helpers.
- `docs/` — research and engineering documentation.
- `project-control/` — append-only handoffs and current accepted state.

## Local verification

Run the standard-library test suite from the repository root:

```bash
python3 -m unittest discover -s tests -v
```

The project is intentionally small at this stage. Dependencies and research
protocols will be added only when a reviewed issue requires them.
