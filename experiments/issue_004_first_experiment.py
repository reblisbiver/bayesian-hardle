"""Run ISSUE-004's first exact Bayesian baseline experiment.

The full comparison keeps the complete legal and candidate vocabularies.  A
bounded Max-IG run is deliberately reported as incomplete when its measured
cost exceeds the configured wall-clock budget; it is never replaced by a
smaller vocabulary.  Exact Bellman planning is only run on the declared
small scope.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import time

from bayesian_hardle import (
    BenchmarkSpec,
    ExactBayesOptimalPlanner,
    ExactEpisodeRunner,
    ExactPosteriorUpdater,
    ExactOutcomePartitioner,
    ExperimentConfig,
    GameSpec,
    HardleFeedbackEngine,
    HardleTerminalRules,
    MAPPolicy,
    MaxInformationGainPolicy,
    PlannerPolicyAdapter,
    RandomPolicy,
    UniformPrior,
    WordListVocabularyRepository,
)


ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = ROOT / "experiments" / "results"
RESULT_PATH = RESULT_DIR / "issue_004_first_experiment.json"
SUMMARY_PATH = RESULT_DIR / "issue_004_first_experiment_summary.md"
CONFIG_PATH = ROOT / "experiments" / "issue_004_first_experiment_config.json"


def _metrics(policy_name, result, policy, requested_scope):
    payload = result.as_dict()
    payload.update(
        {
            "policy": policy_name,
            "requested_scope": requested_scope,
        }
    )
    if hasattr(policy, "evaluated_guesses"):
        payload["evaluated_guesses_before_stop"] = policy.evaluated_guesses
    return payload


def _run_policy(runner, config, policy_name, policy, requested_scope):
    result = runner.run(config, policy)
    return _metrics(policy_name, result, policy, requested_scope)


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    max_ig_limit = float(
        os.environ.get(
            "HARDLE_MAX_IG_LIMIT_SECONDS",
            str(config["full_scope"]["max_ig_time_limit_seconds"]),
        )
    )
    legal_path = ROOT / "data" / "wordlists" / "wordle-legal-guesses.txt"
    answer_path = ROOT / "data" / "wordlists" / "wordle-candidate-answers.txt"
    vocabulary = WordListVocabularyRepository.from_files(legal_path, answer_path)
    feedback = HardleFeedbackEngine(GameSpec(word_length=5, max_guesses=10))
    updater = ExactPosteriorUpdater(feedback)
    prior = UniformPrior()
    terminal = HardleTerminalRules()
    shared_partitioner = ExactOutcomePartitioner(updater)
    full_runner = ExactEpisodeRunner(
        vocabulary, feedback, prior, updater, terminal
    )
    full_config = ExperimentConfig(
        game=GameSpec(word_length=5, max_guesses=10),
        benchmark=BenchmarkSpec(
            name="full-2315-candidates",
            episodes=config["full_scope"]["requested_episodes"],
            seed=config["seed"],
        ),
        run_id="issue-004-full",
    )

    full_results = []
    full_results.append(
        _run_policy(
            full_runner,
            full_config,
            "Random",
            RandomPolicy(seed=config["seed"]),
            "12974 legal guesses x 2315 candidate targets",
        )
    )
    full_results.append(
        _run_policy(
            full_runner,
            full_config,
            "MAP",
            MAPPolicy(),
            "12974 legal guesses x 2315 candidate targets",
        )
    )
    full_max_ig = MaxInformationGainPolicy(
        feedback,
        partitioner=shared_partitioner,
        time_limit_seconds=max_ig_limit,
    )
    full_results.append(
        _run_policy(
            full_runner,
            full_config,
            "Max-IG",
            full_max_ig,
            "12974 legal guesses x 2315 candidate targets",
        )
    )

    small_answers = tuple(config["small_scope"]["candidate_answers"])
    small_legal = tuple(config["small_scope"]["legal_guesses"])
    small_vocabulary = WordListVocabularyRepository(small_legal, small_answers)
    small_runner = ExactEpisodeRunner(
        small_vocabulary, feedback, prior, updater, terminal
    )
    small_config = ExperimentConfig(
        game=GameSpec(word_length=5, max_guesses=config["small_scope"]["max_guesses"]),
        benchmark=BenchmarkSpec(
            name="small-exact-planning",
            episodes=config["small_scope"]["requested_episodes"],
            seed=config["seed"],
        ),
        run_id="issue-004-small",
    )
    small_results = []
    small_results.append(
        _run_policy(
            small_runner,
            small_config,
            "Random",
            RandomPolicy(seed=config["seed"]),
            "small declared vocabulary",
        )
    )
    small_results.append(
        _run_policy(
            small_runner,
            small_config,
            "MAP",
            MAPPolicy(),
            "small declared vocabulary",
        )
    )
    small_results.append(
        _run_policy(
            small_runner,
            small_config,
            "Max-IG",
            MaxInformationGainPolicy(feedback, partitioner=shared_partitioner),
            "small declared vocabulary",
        )
    )
    planner = ExactBayesOptimalPlanner()
    small_results.append(
        _run_policy(
            small_runner,
            small_config,
            "Exact-Bayes-optimal",
            PlannerPolicyAdapter(planner, feedback, updater),
            "small declared vocabulary",
        )
    )

    result = {
        "issue": "ISSUE-004",
        "protocol": {
            "word_length": 5,
            "max_guesses": 10,
            "prior": "uniform",
            "feedback": "(exact-position, present-but-wrong-position), duplicate-aware",
            "scheduled_answer_membership_used_by_solver": False,
            "legal_guess_count": len(vocabulary.legal_guesses()),
            "candidate_answer_count": len(vocabulary.target_vocabulary()),
        },
        "full_scope": {
            "requested_episodes": full_config.benchmark.episodes,
            "max_ig_time_limit_seconds": max_ig_limit,
            "results": full_results,
        },
        "small_scope": {
            "candidate_answers": list(small_answers),
            "legal_guesses": list(small_vocabulary.legal_guesses()),
            "requested_episodes": small_config.benchmark.episodes,
            "results": small_results,
            "planner_cache_hits": planner.cache_hits,
            "planner_cache_misses": planner.cache_misses,
        },
        "evidence_boundary": "executor-local tests and reproducible local experiments; recorded as local reproducibility evidence",
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# ISSUE-004 first experiment",
        "",
        "This is local evidence, not an external validation claim.",
        "",
        "## Scope",
        "",
        f"- Full: {len(vocabulary.legal_guesses())} legal guesses, {len(vocabulary.target_vocabulary())} candidate answers, {full_config.benchmark.episodes} requested episodes.",
        f"- Small: {len(small_vocabulary.legal_guesses())} legal guesses, {len(small_answers)} candidate answers, {small_config.benchmark.episodes} requested episodes.",
        "- The scheduled Hardle answer membership was not provided to the solver.",
        "",
        "## Results",
        "",
        "| Scope | Policy | Completed / requested | Solve rate | Mean guesses | Runtime (s) | Stop reason |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in full_results + small_results:
        stop = row["stopped_reason"] or "completed"
        lines.append(
            f"| {row['scope']} | {row['policy']} | {row['completed_episodes']} / {row['requested_episodes']} | {row['solve_rate']:.6f} | {row['mean_guesses']:.6f} | {row['runtime_seconds']:.3f} | {stop} |"
        )
    lines.extend(
        [
            "",
            "Full Max-IG uses the complete legal vocabulary. If it stops before 2,315 episodes, the row records the measured wall-clock limit and number of guess evaluations rather than substituting a reduced scope.",
            "",
            f"Machine-readable output: `{RESULT_PATH.relative_to(ROOT)}`",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(RESULT_PATH), "summary": str(SUMMARY_PATH)}))


if __name__ == "__main__":
    main()
