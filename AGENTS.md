# Bayesian Hardle — project working agreement

This repository is a research project. The current milestone is the project
control plane; no Bayesian Hardle algorithm or experiment is accepted yet.

## Roles

- OWNER decides the research goal, product meaning, and core hypotheses.
- SUPERVISOR independently audits evidence, accepts or rejects work, and
  assigns the next task.
- EXECUTOR implements, investigates, runs experiments, and records evidence.

`project-control/` is the formal handoff surface. Do not use OWNER as a
message relay between SUPERVISOR and EXECUTOR.

## Evidence discipline

Configuration, implementation, local tests, CI, remote reads, behavioral
end-to-end checks, and physical/live verification are distinct evidence
layers. A passing local test does not prove device, live, or business
acceptance.

Do not write executor results as accepted state. Only a recorded
`[SUPERVISOR REVIEW]` may advance `project-control/PROJECT_STATE.md`.

## Development discipline

- Read the relevant skill instructions before each task.
- For bugs, reproduce first and add a failing regression before fixing.
- For model training, evaluation, or ablation, use `train-coach` and record
  frozen protocol details before execution.
- Before claiming completion, run fresh verification commands and record the
  output or a precise evidence path.
- Keep `project-control/JOURNAL.md` append-only.
- Use semantic, independently recoverable Git commits.
