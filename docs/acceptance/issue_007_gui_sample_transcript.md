# ISSUE-007 GUI sample acceptance transcript

Date: 2026-10-25
Branch: `codex/issue-007-interactive-gui`

This is executor-local acceptance evidence. It demonstrates local service,
AppTest, and Streamlit startup behavior; it is not supervisor or live/business
acceptance.

## Known-target service runs

Command:

```bash
uv run --with . python -m bayesian_hardle.cli simulate \
  --target aahed --mode full-uniform --policy map --max-guesses 10
```

Observed:

```text
mode=full-uniform (PRIMARY STRICT FAIRNESS) | support=12974
guess=aahed feedback=(5, 0) remaining_candidates=1 status=SOLVED
RESULT solved=True turns=1 total_time_ms=12.212
```

Command:

```bash
uv run --with . python -m bayesian_hardle.cli simulate \
  --target aahed --mode full-uniform --policy max-ig --max-guesses 10
```

Observed: exact Max-IG solved `aahed` in 7 turns; the run retained support
`12974`, selected `tares`, `siled`, `menad`, `pawky`, `chafe`, `dadah`, then
`aahed`, and ended with `RESULT solved=True turns=7 total_time_ms=695.264`.
The cumulative per-turn decision time was `692.531 ms`.

## Streamlit startup and rendered UI

Exact OWNER launch command:

```bash
uv run --with . streamlit run src/bayesian_hardle/streamlit_app.py
```

The headless startup check printed:

```text
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8505
```

Streamlit AppTest rendered both tabs:

```text
tabs ['Strategy comparison', 'Human vs Solver']
buttons ['Run comparison', 'Start New Battle']
```

AppTest clicked `Run comparison` with `aahed` and the default MAP/Max-IG
selection. It reported no app exceptions, two result tables, and solved
metrics for both policies: MAP `1` turn and Max-IG `7` turns.

AppTest started a battle and confirmed the pre-finish view contained the
neutral hidden-target message, `Your legal guess`, `Submit guess`, `Give up`,
and `Reset / New Battle`, with no solver table. After one non-terminal human
guess, the only table columns were `Turn`, `Your guess`, `Feedback (exact,
misplaced)`, and `Status`. After Give up, a second table appeared with solver
columns including `Guess`, `Candidates left`, `Entropy (bits)`, `Decision
(ms)`, and `Cumulative (ms)`.

## Automated evidence

- Default Python: `66` tests passed, with `2` Streamlit-only tests skipped
  because Streamlit is intentionally exercised through uv.
- uv-managed environment: `66` tests passed, including Streamlit AppTest.
- `compileall`, `git diff --check`, known-target service tests, battle
  anti-leak transitions, and target/support validation passed.
- `project-control/PROJECT_STATE.md` was unchanged.

