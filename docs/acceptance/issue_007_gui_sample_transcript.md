# ISSUE-007 GUI sample acceptance transcript

Date: 2026-10-25
Branch: `codex/issue-007-interactive-gui`

This is local acceptance evidence. It demonstrates local service,
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

## Streamlit 启动与界面渲染

Exact OWNER launch command:

```bash
uv run --with . streamlit run src/bayesian_hardle/streamlit_app.py
```

The headless startup check printed:

```text
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8505
```

Streamlit AppTest 渲染了两个页签：

```text
tabs ['策略比较', '人类对战求解器']
buttons ['运行策略比较', '开始新对战']
```

AppTest 确认比较页默认选择最大后验（MAP）和最大信息增益（Max-IG），随机基线（Random）可直接加入比较；精确贝叶斯最优（Exact Bayes-optimal）在界面中明确标记为当前不可用于 12,974 词全支持模式，并说明已接受的精确规划目前仅在较小词表上可计算且已完成验证。以 `aahed` 运行默认策略时无应用异常，并显示两张结果表：MAP `1` 回合，Max-IG `7` 回合。

AppTest 启动对战并确认结束前显示隐藏目标保密提示、`你的合法猜词`、`提交猜词`、`放弃本局`和`重置 / 新对战`，且不显示求解器表格。一次未结束的人类猜词后，表格列为`回合`、`你的猜词`、`反馈（命中、错位）`和`状态`；主动放弃后才出现求解器表格，其中包含`猜词`、`剩余候选数`、`熵（比特）`、`单步决策时间（毫秒）`和`累计时间（毫秒）`。

## Automated evidence

- uv-managed environment: `70` tests passed, including Streamlit AppTest.
- `compileall`, `git diff --check`, known-target service tests, battle
  anti-leak transitions, and target/support validation passed.
- The solver state contract was unchanged.

