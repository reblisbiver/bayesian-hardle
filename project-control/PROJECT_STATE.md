# Project state

This file records only the current state accepted by a `[SUPERVISOR REVIEW]`.
Executor reports and unreviewed proposals belong in `JOURNAL.md` instead.

## Final goal

Build and study a correct, testable, and interpretable Bayesian Hardle solver before considering learned policies or reinforcement learning.

## Current research question

Define the exact Hardle game mechanics and feedback semantics required for a valid Bayesian inference engine.

## Current milestone

Project control plane accepted; next milestone is formal Hardle mechanics definition before any feedback-engine implementation.

## Confirmed decisions

- `project-control/` is the formal shared communication and supervision channel.
- OWNER is not used as a message relay between SUPERVISOR and EXECUTOR.
- Executor reports are not accepted state until independent SUPERVISOR review.
- Bayesian core work must precede neural-network or reinforcement-learning work.

## Hard constraints

- Preserve evidence boundaries between local implementation/tests and live or
  business acceptance.
- Keep `JOURNAL.md` append-only.
- Do not advance research stages without `[SUPERVISOR REVIEW]` acceptance.

## Current Bayesian formulation

Not yet defined.

## Accepted implementations

- Project control plane and repository scaffold from ISSUE-001.

## Accepted experiments

None.

## Active issue

Next issue to execute: define Hardle mechanics and feedback semantics before implementation of the feedback engine.

## Open questions

- What are the exact legal-guess and target vocabularies?
- What is the exact feedback alphabet and repeated-letter allocation rule?
- What Hardle-specific rules differ from Wordle?
- What guess limit and win condition are authoritative?
- Which rule source should be treated as canonical for future tests?

## Deferred ideas

None recorded.

## Superseded ideas

None recorded.

## Current verified Git checkpoint

`9218709a99d560c851b3015d88b789a93830c289` on `codex/issue-001-control-plane`, independently reverified by SUPERVISOR with clean status, passing tests, compile/import checks, `git diff --check`, and `git fsck --full`.
