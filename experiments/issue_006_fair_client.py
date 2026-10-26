"""Fresh ISSUE-006 full-support matrix and interactive-latency evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import platform
from pathlib import Path
import random
import resource
import statistics
import sys
import tempfile
import time

from bayesian_hardle.accelerated import ExactFeedbackCodeMatrix
from bayesian_hardle.belief import UniformPrior
from bayesian_hardle.decision import DecisionState, MaxInformationGainPolicy
from bayesian_hardle.fairness import resolve_hypothesis_mode
from bayesian_hardle.game import HardleFeedbackEngine, WordListVocabularyRepository
from bayesian_hardle.cli import run_simulation


ROOT = Path(__file__).resolve().parents[1]
RESULT_JSON = ROOT / "experiments" / "results" / "issue_006_fair_client.json"
RESULT_MD = ROOT / "experiments" / "results" / "issue_006_fair_client_summary.md"
CONFIG = ROOT / "experiments" / "issue_006_fair_client_config.json"


def peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


def repo_root() -> Path:
    return ROOT


def deterministic_targets(legal, count):
    outside = [word for word in legal if word in {"aahed", "padel"}]
    rng = random.Random(20261029)
    sample = rng.sample(list(legal), count)
    result = []
    for word in outside + sample:
        if word not in result:
            result.append(word)
    return result[:count]


def first_move_measure(mode_name, vocabulary, matrix, repeats):
    feedback = HardleFeedbackEngine()
    mode = resolve_hypothesis_mode(mode_name, vocabulary)
    belief = mode.prior.initial_belief(mode.support)
    state = DecisionState(belief, 10)
    times = []
    guesses = []
    for _ in range(repeats):
        policy = MaxInformationGainPolicy(feedback, feedback_matrix=matrix)
        started = time.perf_counter()
        guesses.append(policy.select_guess(state, vocabulary.legal_guesses()))
        times.append((time.perf_counter() - started) * 1000.0)
    return {
        "mode": mode_name,
        "label": mode.label,
        "support_count": len(mode.support),
        "mean_decision_ms": statistics.mean(times),
        "min_decision_ms": min(times),
        "max_decision_ms": max(times),
        "guesses": guesses,
        "entropy_bits": __import__("bayesian_hardle").ShannonEntropyCalculator().calculate(belief),
        "frequency_provenance": mode.provenance if mode_name == "full-frequency" else None,
    }


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    vocabulary = WordListVocabularyRepository.from_repository_root(repo_root())
    legal = tuple(vocabulary.legal_guesses())
    curated = set(vocabulary.target_vocabulary())

    with tempfile.TemporaryDirectory(prefix="bayesian-hardle-issue006-") as cache:
        cache_dir = Path(cache)
        before_rss = peak_rss_bytes()
        started = time.perf_counter()
        matrix = ExactFeedbackCodeMatrix.load_or_build(legal, legal, cache_dir=cache_dir)
        cold_seconds = time.perf_counter() - started
        after_build_rss = peak_rss_bytes()

        started = time.perf_counter()
        reloaded = ExactFeedbackCodeMatrix.load_or_build(legal, legal, cache_dir=cache_dir)
        warm_load_seconds = time.perf_counter() - started

        first_moves = [
            first_move_measure(
                mode_name,
                vocabulary,
                reloaded,
                config["warm_first_move_repeats"],
            )
            for mode_name in ("full-uniform", "full-frequency")
        ]

        representative = []
        for mode_name in ("full-uniform", "full-frequency"):
            for target in config["representative_targets"]:
                result = run_simulation(
                    target,
                    mode_name,
                    "max-ig",
                    max_guesses=config["max_guesses"],
                    seed=config["seed"],
                    cache_dir=cache_dir,
                    repository_root=repo_root(),
                )
                representative.append(
                    {
                        "mode": mode_name,
                        "target": target,
                        "outside_curated_2315": target not in curated,
                        "solved": result.solved,
                        "turns": len(result.turns),
                        "total_time_ms": result.total_time_ms,
                        "decision_ms": [turn.decision_ms for turn in result.turns],
                        "statuses": [turn.status for turn in result.turns],
                    }
                )

        broad_targets = deterministic_targets(legal, config["broad_target_count"])
        broad = []
        for mode_name in ("full-uniform", "full-frequency"):
            for policy_name in ("map", "max-ig"):
                for target in broad_targets:
                    result = run_simulation(
                        target,
                        mode_name,
                        policy_name,
                        max_guesses=config["broad_benchmark_horizon"],
                        seed=config["seed"],
                        cache_dir=cache_dir,
                        repository_root=repo_root(),
                    )
                    broad.append(
                        {
                            "mode": mode_name,
                            "policy": policy_name,
                            "target": target,
                            "outside_curated_2315": target not in curated,
                            "solved": result.solved,
                            "turns": len(result.turns),
                            "total_time_ms": result.total_time_ms,
                        }
                    )

        artifact = {
            "issue": "ISSUE-006",
            "status": "executor-evidence",
            "machine": {
                "platform": platform.platform(),
                "python": platform.python_version(),
                "processor": platform.processor(),
            },
            "vocabulary": {
                "legal_count": len(legal),
                "curated_count": len(curated),
                "full_support_matrix_shape": list(matrix.matrix.shape),
            },
            "matrix": {
                "cold_build_seconds": cold_seconds,
                "warm_load_seconds": warm_load_seconds,
                "memory_bytes": matrix.memory_bytes,
                "disk_bytes": matrix.disk_bytes,
                "cache_key": matrix.vocabulary_identity,
                "cache_path_suffix": matrix.storage_path.name,
                "rss_peak_before_bytes": before_rss,
                "rss_peak_after_build_bytes": after_build_rss,
                "rss_peak_delta_bytes": max(0, after_build_rss - before_rss),
            },
            "warm_first_move_max_ig": first_moves,
            "representative_interactive_latency": representative,
            "broad_benchmark": {
                "selection": "seeded random sample with aahed/padel inclusion",
                "seed": config["seed"],
                "targets": broad_targets,
                "requested_horizon": config["broad_benchmark_horizon"],
                "exhaustive": False,
                "runs": broad,
            },
            "config": config,
        }
        RESULT_JSON.parent.mkdir(parents=True, exist_ok=True)
        RESULT_JSON.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# ISSUE-006 fair-client benchmark summary",
        "",
        "Status: executor evidence only; not supervisor acceptance.",
        "",
        f"- Full-support matrix: {artifact['vocabulary']['full_support_matrix_shape'][0]} x "
        f"{artifact['vocabulary']['full_support_matrix_shape'][1]} uint8; memory "
        f"{artifact['matrix']['memory_bytes']:,} bytes; disk {artifact['matrix']['disk_bytes']:,} bytes.",
        f"- Cold build: {artifact['matrix']['cold_build_seconds']:.6f}s; "
        f"warm load: {artifact['matrix']['warm_load_seconds']:.6f}s.",
        f"- Full-uniform warm first move mean: {first_moves[0]['mean_decision_ms']:.3f} ms; "
        f"full-frequency: {first_moves[1]['mean_decision_ms']:.3f} ms.",
        f"- Representative latency includes targets outside curated support: "
        f"{sum(item['outside_curated_2315'] for item in representative)}/{len(representative)} rows.",
        f"- Broad target benchmark is deterministic but non-exhaustive: {len(broad_targets)} targets, "
        f"{len(broad)} independent mode/policy runs.",
        "",
        "The full machine-readable record is in `issue_006_fair_client.json`.",
    ]
    RESULT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"json": str(RESULT_JSON), "markdown": str(RESULT_MD)}, indent=2))


if __name__ == "__main__":
    main()
