"""Measure and rerun the complete exact Max-IG experiment for ISSUE-005."""

from __future__ import annotations

import json
from pathlib import Path
import statistics
import time

from bayesian_hardle import (
    BenchmarkSpec,
    DecisionState,
    ExactEpisodeRunner,
    ExactOutcomePartitioner,
    ExactPosteriorUpdater,
    ExperimentConfig,
    GameSpec,
    HardleFeedbackEngine,
    HardleTerminalRules,
    MaxInformationGainPolicy,
    UniformPrior,
    WordListVocabularyRepository,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "experiments" / "issue_005_maxig_speed_config.json"
RESULT_DIR = ROOT / "experiments" / "results"
RESULT_PATH = RESULT_DIR / "issue_005_maxig_speed.json"
SUMMARY_PATH = RESULT_DIR / "issue_005_maxig_speed_summary.md"


def _first_move_measurement(vocabulary, feedback, answers, repeats):
    legal = tuple(vocabulary.legal_guesses())
    belief = UniformPrior().initial_belief(answers)
    state = DecisionState(belief, 10)

    cold_policy = MaxInformationGainPolicy(feedback)
    started = time.perf_counter()
    cold_guess = cold_policy.select_guess(state, legal)
    cold_seconds = time.perf_counter() - started
    matrix = cold_policy.feedback_matrix

    warm_seconds = []
    warm_guesses = []
    for _ in range(repeats):
        warm_policy = MaxInformationGainPolicy(feedback, feedback_matrix=matrix)
        started = time.perf_counter()
        warm_guesses.append(warm_policy.select_guess(state, legal))
        warm_seconds.append(time.perf_counter() - started)

    return {
        "legal_guess_count": len(legal),
        "candidate_answer_count": len(answers),
        "cold_first_move_seconds": cold_seconds,
        "cold_matrix_bytes": matrix.memory_bytes,
        "cold_matrix_mib": matrix.memory_bytes / (1024 * 1024),
        "cold_selected_guess": cold_guess,
        "cold_evaluated_guesses": cold_policy.evaluated_guesses,
        "warm_first_move_seconds": warm_seconds,
        "warm_first_move_mean_seconds": statistics.mean(warm_seconds),
        "warm_first_move_min_seconds": min(warm_seconds),
        "warm_selected_guesses": warm_guesses,
        "warm_evaluated_guesses": len(legal),
    }


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    vocabulary = WordListVocabularyRepository.from_repository_root(ROOT)
    game = GameSpec(word_length=5, max_guesses=10)
    feedback = HardleFeedbackEngine(game)
    prior = UniformPrior()
    updater = ExactPosteriorUpdater(feedback)
    terminal = HardleTerminalRules()
    answers = tuple(vocabulary.target_vocabulary())
    legal = tuple(vocabulary.legal_guesses())

    first_move = _first_move_measurement(
        vocabulary,
        feedback,
        answers,
        int(config["warm_measurement_repeats"]),
    )

    runner = ExactEpisodeRunner(
        vocabulary, feedback, prior, updater, terminal
    )
    benchmark = ExperimentConfig(
        game=game,
        benchmark=BenchmarkSpec(
            name="full-2315-candidates",
            episodes=int(config["requested_episodes"]),
            seed=int(config["seed"]),
        ),
        run_id="issue-005-full-max-ig",
    )
    policy = MaxInformationGainPolicy(
        feedback,
        partitioner=ExactOutcomePartitioner(updater),
        time_limit_seconds=float(config["max_ig_time_limit_seconds"]),
    )
    result = runner.run(benchmark, policy)
    full_result = result.as_dict()
    full_result.update(
        {
            "policy": "Max-IG",
            "requested_scope": "12974 legal guesses x 2315 candidate targets",
            "evaluated_guesses_before_stop": policy.evaluated_guesses,
            "decision_cache_hits": policy.decision_cache_hits,
            "decision_cache_misses": policy.decision_cache_misses,
            "matrix_bytes": (
                policy.feedback_matrix.memory_bytes
                if policy.feedback_matrix is not None
                else None
            ),
        }
    )

    prior_measurement = {
        "runtime_seconds": 30.039,
        "evaluated_guesses": 603,
        "completed_episodes": 0,
        "source": "ISSUE-004 accepted execution report",
    }
    speedup = prior_measurement["runtime_seconds"] / full_result["runtime_seconds"]

    output = {
        "issue": "ISSUE-005",
        "protocol": {
            "word_length": 5,
            "max_guesses": 10,
            "prior": "uniform",
            "feedback": "(exact-position, present-but-wrong-position), duplicate-aware",
            "scheduled_answer_membership_used_by_solver": False,
            "legal_guess_count": len(legal),
            "candidate_answer_count": len(answers),
        },
        "performance_gate": first_move,
        "full_experiment": full_result,
        "prior_accepted_measurement": prior_measurement,
        "speedup_vs_prior_wall_clock": speedup,
        "evidence_boundary": "executor-local tests and reproducible local measurements; recorded as local reproducibility evidence",
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    performance = output["performance_gate"]
    full = output["full_experiment"]
    lines = [
        "# ISSUE-005 exact Max-IG performance",
        "",
        "This is local evidence, not an external validation claim.",
        "",
        "## Performance gate",
        "",
        f"- Scope: {performance['legal_guess_count']} legal guesses x {performance['candidate_answer_count']} candidate answers.",
        f"- Cold first move, including matrix build: {performance['cold_first_move_seconds']:.6f}s; matrix: {performance['cold_matrix_bytes']} bytes ({performance['cold_matrix_mib']:.3f} MiB).",
        f"- Warm first move, full row scan: mean {performance['warm_first_move_mean_seconds']:.6f}s; min {performance['warm_first_move_min_seconds']:.6f}s; repeats: {performance['warm_first_move_seconds']}",
        f"- Selected opener: cold `{performance['cold_selected_guess']}`, warm {performance['warm_selected_guesses']}.",
        "- Gates: cold <= 2.0s and warm <= 0.5s.",
        "",
        "## Full experiment",
        "",
        "| Policy | Completed / requested | Solve rate | Mean guesses | Runtime (s) | Evaluated guesses | Cache hits / misses | Stop reason |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        f"| {full['policy']} | {full['completed_episodes']} / {full['requested_episodes']} | {full['solve_rate']:.6f} | {full['mean_guesses']:.6f} | {full['runtime_seconds']:.6f} | {full['evaluated_guesses_before_stop']} | {full['decision_cache_hits']} / {full['decision_cache_misses']} | {full['stopped_reason'] or 'completed'} |",
        "",
        "## Before / after reference",
        "",
        "The accepted ISSUE-004 baseline stopped after 30.039s, 603 guess evaluations, and 0 completed episodes. ISSUE-005 preserves the full scope and records the fresh result above; the ratio is computed from these measured runtimes, not from a reduced benchmark.",
        f"- Fresh full-experiment wall-clock speedup versus that accepted measurement: {speedup:.3f}x ({prior_measurement['runtime_seconds']:.3f}s / {full['runtime_seconds']:.6f}s).",
        "",
        f"Machine-readable output: `{RESULT_PATH.relative_to(ROOT)}`",
    ]
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(RESULT_PATH), "summary": str(SUMMARY_PATH)}))


if __name__ == "__main__":
    main()
