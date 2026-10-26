# Bayesian Hardle

Bayesian Hardle is a research codebase for studying Bayesian reasoning in a
Hardle-style word-feedback environment.

The repository contains an executor implementation of the exact Bayesian
core for ISSUE-004. The formal communication and audit records live in
[`project-control/`](project-control/README.md). These local tests and
experiments remain unaccepted until a supervisor review records acceptance.

## Layout

- `src/bayesian_hardle/` — package code.
- `tests/` — behavior-oriented tests.
- `experiments/` — reproducible experiment inputs, runners, and outputs.
- `data/wordlists/` — vendored supervisor-specified vocabularies plus source
  provenance.
- `scripts/` — small operational helpers.
- `docs/` — research and engineering documentation.
- `project-control/` — append-only handoffs and current accepted state.

## Component scaffold (ISSUE-003)

The package now implements the settled exact semantics: duplicate-aware
feedback, a uniform prior, deterministic posterior filtering, Shannon
entropy/expected posterior entropy/information gain, Random/MAP/Max-IG, and
an exact finite-horizon planner for small vocabularies. Evaluation keeps
hidden targets outside the solver state.

| Group | Module | Public boundary |
| --- | --- | --- |
| Game Model | `game.py` | `VocabularyRepository`, `GameSpec`, `FeedbackEngine`, `TerminalRules` |
| Bayesian Belief Engine | `belief.py` | `PriorModel`, `BeliefState`, `LikelihoodModel`, `PosteriorUpdater` |
| Information Engine | `information.py` | `OutcomePartitioner`, `EntropyCalculator`, `ExpectedEntropyCalculator`, `InformationGainCalculator` |
| Decision Engine | `decision.py` | `DecisionState`, `Policy`, placeholder policies, `BayesOptimalPlanner`, `PlannerCache` |
| Evaluation & Experiment System | `evaluation.py` | `EpisodeRunner`, `BenchmarkSpec`, `MetricsResult`, `ExperimentConfig`, `ArtifactSink` |

The intended runtime information flow is:

1. The Game Model supplies legal guesses, target vocabulary, game limits, and the shared feedback boundary.
2. The Belief Engine consumes a prior and observed guess/feedback history and exposes a `BeliefState`.
3. The Information Engine consumes that belief, candidate guesses, and the shared feedback boundary for outcome partitions and future information values.
4. The Decision Engine consumes `DecisionState(belief, remaining_guesses)` plus shared game/information interfaces and selects a guess.
5. The Game Model evaluates the guess against the hidden target and returns feedback.
6. The Belief Engine receives the observation, updates the posterior boundary, and the decision horizon decreases.
7. Evaluation wraps the loop and records metrics/artifacts without changing game semantics.

## Local verification

Run the standard-library test suite from the repository root:

```bash
python3 -m unittest discover -s tests -v
```

Run the first controlled experiment with:

```bash
PYTHONPATH=src python3 experiments/issue_004_first_experiment.py
```

It writes `experiments/results/issue_004_first_experiment.json` and a short
Markdown summary. The full Random/MAP comparison uses all 2,315 candidate
answers and 12,974 legal guesses. Full Max-IG uses that same scope; its
configured wall-clock limit is reported as a scaling measurement if reached,
not replaced by a smaller vocabulary. Exact Bellman planning is deliberately
restricted to the declared small scope.

## Interactive acceptance / try it yourself (ISSUE-006)

Install the project from this worktree to enable both the console script and
the pinned general-English frequency source:

```bash
python3 -m pip install .
```

The equivalent module entrypoint is available from the repository root. The
three explicit hypothesis/prior modes are:

- `full-uniform` — PRIMARY STRICT FAIRNESS; all 12,974 legal words, uniform.
- `full-frequency` — PRIMARY HUMAN-LIKE EXPLORATORY; all 12,974 legal words,
  positive `wordfreq==3.1.1` English Zipf-frequency mass, with no scheduled
  answer-list membership.
- `curated-2315` — DIAGNOSTIC / ANSWER-LIST-AWARE only; the historical 2,315
  candidate-answer support, retained for comparison and not the primary
  fairness claim.

Simulate a target known to the OWNER. `aahed` is legal but outside the curated
2,315 list, so it is a useful fairness smoke test:

```bash
bayesian-hardle simulate --target aahed --mode full-uniform --policy max-ig
python3 -m bayesian_hardle.cli simulate --target aahed \
  --mode full-frequency --policy map --max-guesses 20
```

The solver prints the mode label, policy, guess, Hardle feedback, remaining
candidate count, entropy in bits, decision time in milliseconds, and the top
five posterior words on every turn. Max-IG builds or reuses a vocabulary-keyed
exact `uint8` matrix under `.cache/bayesian_hardle/`; the matrix is about
160.6 MiB for full support.

For live assistance, enter the two numbers returned by the real website. A
malformed or posterior-impossible observation is rejected without changing the
belief state; `q`, Ctrl-D, or Ctrl-C exits cleanly:

```bash
python3 -m bayesian_hardle.cli live --mode full-uniform --policy max-ig
# at each prompt, enter for example: 0 0
```

Independent policy/mode comparisons are also available:

```bash
bayesian-hardle compare --target aahed \
  --modes full-uniform full-frequency \
  --policies map max-ig --max-guesses 10
```

The benchmark and acceptance transcript are kept in
[`experiments/results/issue_006_fair_client_summary.md`](experiments/results/issue_006_fair_client_summary.md),
[`experiments/results/issue_006_fair_client.json`](experiments/results/issue_006_fair_client.json),
and [`docs/acceptance/issue_006_sample_transcript.md`](docs/acceptance/issue_006_sample_transcript.md).
The frequency prior is a reproducible human-like heuristic, not a claim about
the true Hardle target-generating process.

To refresh the machine-readable performance evidence after installing the
project dependencies:

```bash
PYTHONPATH=src python3 experiments/issue_006_fair_client.py
```

## 交互式浏览器验收（ISSUE-007/008/009）

在本仓库中用 uv 启动本地可视化验收界面：

```bash
uv run --with . streamlit run src/bayesian_hardle/streamlit_app.py
```

打开 Streamlit 输出的本地地址。在 `策略比较` 页顶部的 `实验范围` 选择：

- `全词表（公平主实验）`：继续选择 `full-uniform`、`full-frequency` 或 `curated-2315`，只运行 Random / MAP / Max-IG；Exact 会显示为不可用，并标明“仅小词表精确实验可用”。
- `小词表（Exact 实验）`：固定使用 ISSUE-004 accepted fixture，包含 5 个候选目标、10 个合法猜词（含仓库自动加入的 `covid`、`padel`）和 3 回合上限。目标输入必须是 `awake`、`cigar`、`humph`、`rebut` 或 `sissy` 之一。

要在一个目标上运行四种策略：选择 `小词表（Exact 实验）`，输入一个候选目标（例如 `awake`），保留默认勾选的 Random / MAP / Max-IG / Exact Bayes-optimal，然后点击 `运行策略比较`。结果会按策略并列显示；每张表包含每回合猜词、反馈、剩余候选数、单步与累计决策时间、状态和回合数。`人类对战求解器`页仍只提供可扩展的三种策略，并明确提示 Exact 比较位于小词表策略比较页。

全词表的 `精选 2,315（curated-2315）` 明确标为诊断/答案列表感知模式，不代表主要公平模式。

`精确贝叶斯最优（Exact Bayes-optimal）`在全词表范围会显示为不可用；它只在上述小词表实验中执行，且复用已接受的精确规划语义。
