# Project state

This file records only the current state accepted by a `[SUPERVISOR REVIEW]`.
Executor reports and unreviewed proposals belong in `JOURNAL.md` instead.

## Final goal

Build and study a correct, testable, and interpretable Bayesian Hardle solver before considering learned policies or reinforcement learning.

## Current research question

Define the exact Hardle game mechanics and feedback semantics required to populate the accepted Bayesian component scaffold with correct behavior.

## Current milestone

Bayesian Hardle component/interface scaffold accepted; next milestone is formal Hardle mechanics definition before any FeedbackEngine implementation.

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

The accepted scaffold is organized into five groups: Game Model, Bayesian Belief Engine, Information Engine, Decision Engine, and Evaluation & Experiment System. `BeliefState` explicitly carries posterior probability mass; information outcomes carry feedback probability plus resulting posterior; finite-horizon decision state is belief plus remaining guesses. Numeric inference, information calculations, and planning behavior remain unimplemented.

## Accepted implementations

- Project control plane and repository scaffold from ISSUE-001.
- Five-group Bayesian Hardle component/interface scaffold from ISSUE-003, including shared game/belief semantics boundaries and typed information/decision/evaluation contracts.

## Accepted experiments

None.

## Active issue

Resume the deferred Hardle-mechanics specification: define exact feedback semantics and game rules before implementing the Feedback Engine.

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

## Current verified implementation checkpoint

Corrected ISSUE-003 executor checkpoint `60d3c73` on `codex/issue-003-component-scaffold`, independently verified by SUPERVISOR with 9 passing tests, compile/import checks, full-range `git diff --check`, and scope audit.
