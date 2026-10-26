# ISSUE-006 implementation plan — fair full-support solver and client

## Scope and preview

The public acceptance path will be:

```text
python -m bayesian_hardle.cli simulate --target <legal-word> \
  --mode full-uniform --policy max-ig
python -m bayesian_hardle.cli live --mode full-frequency --policy map
bayesian-hardle compare --target <legal-word> --modes full-uniform curated-2315
```

Every turn prints the mode label, policy, guess, feedback when known,
posterior candidate count, entropy, decision time, top posterior words, and
terminal status. Fair modes take the legal vocabulary as their complete
hypothesis support; only `curated-2315` reads the candidate-answer list.

## Vertical slices

1. Add explicit fair/diagnostic hypothesis modes and priors, with tests for
   support boundaries, positive normalized mass, provenance, and an outside-
   curated target.
2. Extend the exact feedback matrix with vocabulary-identity keyed on-disk
   NumPy cache and memmap loading; add full-support equivalence and cache tests.
3. Add matrix-backed filtering and wire full-support Max-IG to reuse the
   complete matrix rather than rebuilding per posterior state.
4. Add `simulate`, `live`, and optional `compare` CLI commands with stable
   human-readable output, validation, clean quit handling, and subprocess
   smoke tests.
5. Add README acceptance instructions, transcript, benchmark runner/artifacts,
   and the append-only execution report.

## Verification gates

- Full test suite, compile/import checks, CLI help/simulate/live smoke tests.
- Matrix/reference checks on adversarial duplicate words and 10,000 seeded
  full-vocabulary pairs.
- Weighted fast/scalar IG checks within `1e-12`.
- Fresh full-support cache and fair first-move timings with memory/disk bytes.
- `git diff --check`, worktree status, and explicit confirmation that
  `PROJECT_STATE.md` is unchanged.

## Non-goals

- No change to Hardle feedback semantics.
- No scheduled answer list in fair-mode inference.
- No approximation or silent pruning of the 12,974-word support.
- No supervisor acceptance or modification of accepted project state.
