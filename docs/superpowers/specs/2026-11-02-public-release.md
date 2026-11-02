# Bayesian Hardle Public Release Design

## Intent
Turn the completed Bayesian Hardle research prototype into a clean, truthful, reproducible public portfolio repository without changing solver semantics.

## Goals
- Present the project as an information-theoretic Bayesian decision system, not an internal agent-control artifact.
- Preserve implementation, tests, reproducible experiments, and useful architecture figures.
- Remove internal PM/supervisor/issue-control material from the public-facing tree.
- Make provenance, licensing, installation, verification, and limitations explicit.
- Do not publish until repository safety and provenance checks pass.

## Non-goals
- No algorithm redesign or benchmark inflation.
- No fabricated history, metrics, or authorship.
- No public-safe derivative of private Choice Engineering work.

## Constraints
- Keep all existing solver tests green.
- Keep exact-vs-approximate scope truthful.
- External wordlists must not be redistributed unless their redistribution status is defensible; prefer download/prepare scripts when uncertain.
- Publishing/pushing remains a separate explicit action after review.

## Approach
Use the existing completed branch as the technical base and create an isolated public-prep branch. Rewrite only the presentation/release surface, remove internal project-control files from that branch, retain provenance and reproducibility, and verify with tests plus a secret/path scan.
