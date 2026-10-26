# ISSUE-006 — Fair full-support solver and interactive acceptance client

## Goal

Make the primary human-comparison hypothesis space the complete current legal
Hardle vocabulary (12,974 words), add a reproducible non-leaking general-English
frequency prior, retain the 2,315-word behavior only as a visibly diagnostic
answer-list-aware mode, and provide a local interactive client for direct OWNER
acceptance.

## Accepted contract for this execution

- `full-uniform` is the primary strict-fairness mode: all 12,974 legal words
  are possible targets with equal prior mass.
- `full-frequency` is the primary human-like exploratory mode: all 12,974 legal
  words remain possible and receive positive mass from `wordfreq==3.1.1`
  general-English Zipf frequencies only. It never reads scheduled answers or
  the curated 2,315 list.
- `curated-2315` is retained only as a diagnostic / answer-list-aware mode.
- Feedback remains Hardle's exact duplicate-aware `(exact, misplaced)` pair.
- Random, MAP, and exact Max-IG are exposed. Full-support exact Bayes-optimal
  planning remains out of scope unless a future issue establishes tractability.
- The OWNER can run simulated-target and live-assist sessions without editing
  code, using both `python -m bayesian_hardle.cli` and an installed console
  script.

## Required evidence

1. Full-support matrix codes match `HardleFeedbackEngine` on duplicate-letter
   cases and 10,000 deterministic full-vocabulary pairs.
2. Matrix weighted information gain matches the scalar reference within
   `1e-12` on controlled uniform and non-uniform beliefs.
3. Full-support posterior filtering preserves legal words outside the curated
   list; at least one such target is solved in both fair simulated modes.
4. Frequency prior provenance/version, positive support, and normalization are
   testable; scheduled-answer membership is absent from fair-mode inputs.
5. Existing ISSUE-001..005 tests remain green.
6. Fresh machine-readable benchmark artifacts record cache construction/load,
   memory/disk footprint, fair first-move timings, and representative CLI
   latency. Results are executor evidence pending supervisor review.

## Handoff boundary

Work in `codex/issue-006-fair-client` under the isolated worktree. Keep
`project-control/PROJECT_STATE.md` unchanged and `JOURNAL.md` append-only.
Handoff status must be `READY_FOR_REVIEW` with exact commit SHA(s), commands,
evidence paths, and any performance or dependency limitations. No supervisor
acceptance is claimed by the executor.
