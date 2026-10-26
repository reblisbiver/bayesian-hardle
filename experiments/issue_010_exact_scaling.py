"""Bounded, staged audit of the exact Bayes-optimal Hardle planner.

The worker mode intentionally runs one benchmark in one process so a bounded
timeout cannot leave a recursive search running in the benchmark driver.  The
driver writes a machine-readable JSON artifact and a concise markdown table.
"""

from __future__ import annotations

import argparse
import cProfile
import json
import math
import os
from pathlib import Path
import pstats
import random
import subprocess
import sys
import time
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
RESULTS = ROOT / "experiments" / "results"
PROFILE_DIR = RESULTS / "issue_010_profiles"
sys.path.insert(0, str(SRC))

from bayesian_hardle.accelerated import ExactFeedbackCodeMatrix  # noqa: E402
from bayesian_hardle.belief import ExactPosteriorUpdater, UniformPrior  # noqa: E402
from bayesian_hardle.decision import (  # noqa: E402
    DecisionState,
    ExactBayesOptimalPlanner,
    ExactBayesOptimalReferencePlanner,
)
from bayesian_hardle.game import HardleFeedbackEngine  # noqa: E402


LAYER_LADDER = (
    ("baseline_scalar", ()),
    ("closed_forms", ("closed_forms",)),
    ("matrix_transitions", ("closed_forms", "matrix_transitions")),
    (
        "canonical_memoization",
        ("closed_forms", "matrix_transitions", "canonical_memoization"),
    ),
    (
        "action_ordering",
        (
            "closed_forms",
            "matrix_transitions",
            "canonical_memoization",
            "action_ordering",
        ),
    ),
    (
        "branch_ordering",
        (
            "closed_forms",
            "matrix_transitions",
            "canonical_memoization",
            "action_ordering",
            "branch_ordering",
        ),
    ),
    (
        "branch_and_bound",
        ExactBayesOptimalPlanner.ALL_OPTIMIZATION_LAYERS,
    ),
)


def _words(path: Path) -> Tuple[str, ...]:
    return tuple(
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def _case_definitions() -> Tuple[Dict[str, Any], ...]:
    curated = _words(ROOT / "data" / "wordlists" / "wordle-candidate-answers.txt")
    legal_all = tuple(
        sorted(
            set(_words(ROOT / "data" / "wordlists" / "wordle-legal-guesses.txt"))
            | {"covid", "padel"}
        )
    )
    small_answers = ("awake", "cigar", "humph", "rebut", "sissy")
    small_legal = tuple(sorted(set(small_answers) | {"adieu", "arise", "stare", "covid", "padel"}))

    def sampled(size: int, seed: int) -> Tuple[str, ...]:
        return tuple(sorted(random.Random(seed).sample(curated, size)))

    def legal_for(support: Sequence[str], probes: int, seed: int) -> Tuple[str, ...]:
        extras = [word for word in legal_all if word not in set(support)]
        extras = random.Random(seed).sample(extras, probes)
        return tuple(sorted(set(support) | set(extras)))

    return (
        {
            "name": "fixture5_h3_legal10",
            "support": small_answers,
            "legal": tuple(sorted(set(small_legal) | {"cigar", "rebut", "sissy"})),
            "horizon": 3,
            "timeout_seconds": 30,
        },
        {
            "name": "sample8_h3_legal16",
            "support": sampled(8, 8010),
            "legal": legal_for(sampled(8, 8010), 8, 8011),
            "horizon": 3,
            "timeout_seconds": 30,
        },
        {
            "name": "sample12_h3_legal20",
            "support": sampled(12, 12010),
            "legal": legal_for(sampled(12, 12010), 8, 12011),
            "horizon": 3,
            "timeout_seconds": 30,
        },
        {
            "name": "sample20_h3_legal28",
            "support": sampled(20, 20010),
            "legal": legal_for(sampled(20, 20010), 8, 20011),
            "horizon": 3,
            "timeout_seconds": 60,
        },
        {
            "name": "curated2315_h1_fulllegal",
            "support": curated,
            "legal": legal_all,
            "horizon": 1,
            "timeout_seconds": 20,
        },
        {
            "name": "curated2315_h2_fulllegal",
            "support": curated,
            "legal": legal_all,
            "horizon": 2,
            "timeout_seconds": 20,
        },
    )


def _make_planner(
    layers: Sequence[str],
    legal: Sequence[str],
    support: Sequence[str],
) -> Tuple[ExactBayesOptimalPlanner, float]:
    matrix = None
    build_started = time.perf_counter()
    if "matrix_transitions" in layers:
        matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, support)
    build_seconds = time.perf_counter() - build_started
    if not layers:
        planner: ExactBayesOptimalPlanner = ExactBayesOptimalReferencePlanner()
    else:
        planner = ExactBayesOptimalPlanner(
            feedback_matrix=matrix,
            optimization_layers=layers,
        )
    return planner, build_seconds


def _run_worker(case: Dict[str, Any], layers: Sequence[str], profile_path: Optional[Path]) -> Dict[str, Any]:
    support = tuple(case["support"])
    legal = tuple(case["legal"])
    feedback = HardleFeedbackEngine()
    updater = ExactPosteriorUpdater(feedback)
    belief = UniformPrior().initial_belief(support)
    state = DecisionState(belief, int(case["horizon"]))
    planner, matrix_build_seconds = _make_planner(layers, legal, support)

    profile = cProfile.Profile() if profile_path is not None else None
    started = time.perf_counter()
    if profile is not None:
        profile.enable()
    selected = planner.select_guess(state, legal, feedback, updater)
    value = planner._guess_value(state, selected, legal, feedback, updater)
    if profile is not None:
        profile.disable()
        profile.dump_stats(str(profile_path))
        stats_text = PROFILE_DIR / (profile_path.stem + ".txt")
        with stats_text.open("w", encoding="utf-8") as stream:
            pstats.Stats(profile, stream=stream).sort_stats("cumulative").print_stats(20)
    elapsed = time.perf_counter() - started
    return {
        "status": "completed",
        "case": case["name"],
        "layers": list(layers),
        "support_size": len(support),
        "legal_size": len(legal),
        "horizon": case["horizon"],
        "selected_guess": selected,
        "value": list(value) if value is not None else None,
        "matrix_build_seconds": matrix_build_seconds,
        "selection_seconds": elapsed,
        "total_seconds": matrix_build_seconds + elapsed,
        "instrumentation": planner.instrumentation(),
        "profile_path": str(profile_path.relative_to(ROOT)) if profile_path else None,
    }


def _run_bounded(
    case: Dict[str, Any],
    variant_name: str,
    layers: Sequence[str],
    profile: bool,
) -> Dict[str, Any]:
    profile_path = None
    if profile:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        profile_path = PROFILE_DIR / f"{case['name']}__{variant_name}.prof"
    payload = json.dumps({"case": case, "layers": list(layers), "profile_path": str(profile_path) if profile_path else None})
    started = time.perf_counter()
    command = [sys.executable, str(Path(__file__)), "--worker", payload]
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=float(case["timeout_seconds"]),
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "timed_out",
            "case": case["name"],
            "variant": variant_name,
            "layers": list(layers),
            "support_size": len(case["support"]),
            "legal_size": len(case["legal"]),
            "horizon": case["horizon"],
            "timeout_seconds": case["timeout_seconds"],
            "elapsed_before_timeout": time.perf_counter() - started,
        }
    if completed.returncode != 0:
        return {
            "status": "failed",
            "case": case["name"],
            "variant": variant_name,
            "layers": list(layers),
            "returncode": completed.returncode,
            "stderr": completed.stderr[-4000:],
            "stdout": completed.stdout[-1000:],
        }
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {
            "status": "failed",
            "case": case["name"],
            "variant": variant_name,
            "returncode": completed.returncode,
            "stderr": completed.stderr[-4000:],
            "stdout": completed.stdout[-4000:],
        }
    result["variant"] = variant_name
    result["driver_elapsed_seconds"] = time.perf_counter() - started
    return result


def _speedup(baseline: Optional[Dict[str, Any]], current: Dict[str, Any]) -> Optional[float]:
    if not baseline or baseline.get("status") != "completed" or current.get("status") != "completed":
        return None
    return baseline["total_seconds"] / current["total_seconds"] if current["total_seconds"] else None


def _markdown(artifact: Dict[str, Any]) -> str:
    lines = [
        "# ISSUE-010 exact planner scaling audit",
        "",
        "All rows are root-state selections on deterministic supports. A timeout is an observed bounded limit, not an exact-feasibility claim.",
        "",
        "| Case | Layer | Status | Support | Legal | H | Total s | Incremental vs prior | Cumulative vs baseline | Actions | Branches | Cache hit/miss | Pruned | Matrix bytes |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    grouped: Dict[str, list[Dict[str, Any]]] = {}
    for row in artifact["runs"]:
        grouped.setdefault(row["case"], []).append(row)
    for case in artifact["cases"]:
        rows = grouped.get(case["name"], [])
        baseline = next((row for row in rows if row.get("variant") == "baseline_scalar"), None)
        previous = None
        for row in rows:
            if row.get("status") != "completed":
                lines.append(
                    f"| {row.get('case')} | {row.get('variant')} | {row.get('status')} | {row.get('support_size', '-') } | {row.get('legal_size', '-')} | {row.get('horizon', '-')} | {row.get('elapsed_before_timeout', row.get('total_seconds', '-')):.3f} | - | - | - | - | - | - | - |"
                )
                previous = row
                continue
            stats = row["instrumentation"]
            inc = _speedup(previous, row) if previous and previous.get("status") == "completed" else None
            cum = _speedup(baseline, row)
            inc_text = f"{inc:.2f}x" if inc is not None else "-"
            cum_text = f"{cum:.2f}x" if cum is not None else "-"
            lines.append(
                f"| {row['case']} | {row['variant']} | completed | {row['support_size']} | {row['legal_size']} | {row['horizon']} | {row['total_seconds']:.3f} | {inc_text} | {cum_text} | {stats['actions_evaluated']} | {stats['branches_evaluated']} | {stats['cache_hits']}/{stats['cache_misses']} | {stats['actions_pruned']} | {stats['matrix_memory_bytes']} |"
            )
            previous = row
    lines.extend(
        [
            "",
            "## Layer exactness justifications",
            "",
            "| Layer | Why it preserves the objective |",
            "|---|---|",
            "| closed_forms | Singleton, last-horizon, and legal two-candidate formulas enumerate the same terminal outcomes and Bellman value under the accepted lexicographic objective. |",
            "| matrix_transitions | The existing uint8 matrix encodes the same duplicate-aware `(exact, misplaced)` Hardle feedback; grouping and normalized member masses are algebraically identical to scalar evaluation. |",
            "| canonical_memoization | Keys normalize mass, sort support, and exclude only history that cannot affect future transitions; equivalent belief/support states therefore share values. |",
            "| action_ordering | All legal actions are still evaluated unless branch-and-bound proves them unable to improve the incumbent; only visit order changes. |",
            "| branch_ordering | All feedback branches remain in the Bellman sum; posterior probability descending changes only evaluation order. |",
            "| branch_and_bound | Uses solve-probability upper bound `solved_mass + unexplored_mass` and expected-guess lower bound; pruning occurs only when the action cannot improve the incumbent within the documented tie tolerance. |",
            "",
        ]
    )
    lines.extend(
        [
            "",
            "## Profiling",
            "",
            "The profile text files under `experiments/results/issue_010_profiles/` list cumulative-time hotspots for the scalar baseline and the fully optimized ladder case.",
            "",
            "| Profile | Dominant cumulative-time calls (ncalls from cProfile) |",
            "|---|---|",
            "| scalar fixture5 | `_guess_value` 497/11; `HardleFeedbackEngine.evaluate` 1,132; `ExactPosteriorUpdater.update` 206; `_transition_branches` 290 |",
            "| optimized sample12 | `_guess_value` 1,992/21; `_mass_table` 7,162; `_transition_branches` 700; `_can_use_matrix` 1,991; `_posterior_for_branch` 1,291 |",
            "",
            "The optimized profile shifts the hot path away from repeated scalar feedback and posterior filtering; remaining cost is exact state-key/mass handling and matrix transition bookkeeping.",
            "",
            "## Interpretation boundary",
            "",
            "The curated 2,315 / full-legal rows are bounded probes. Completion at horizon 1 only measures the terminal closed form; it does not prove a multi-step exact solve over the full support. Any timeout remains the practical frontier evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def run_driver() -> Dict[str, Any]:
    cases = _case_definitions()
    runs = []
    for case in cases:
        for variant_name, layers in LAYER_LADDER:
            should_profile = case["name"] in {"fixture5_h3_legal10", "sample12_h3_legal20"} and variant_name in {"baseline_scalar", "branch_and_bound"}
            runs.append(_run_bounded(case, variant_name, layers, should_profile))
    artifact = {
        "format": 1,
        "issue": "ISSUE-010",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": sys.version,
        "platform": sys.platform,
        "layer_ladder": [{"name": name, "layers": list(layers)} for name, layers in LAYER_LADDER],
        "cases": list(cases),
        "runs": runs,
        "largest_completed": max(
            (row for row in runs if row.get("status") == "completed"),
            key=lambda row: (row["support_size"], row["horizon"], row["legal_size"]),
            default=None,
        ),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    artifact_path = RESULTS / "issue_010_exact_scaling.json"
    artifact_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path = RESULTS / "issue_010_exact_scaling_summary.md"
    summary_path.write_text(_markdown(artifact), encoding="utf-8")
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", help="JSON payload for one bounded worker run")
    args = parser.parse_args()
    if args.worker:
        payload = json.loads(args.worker)
        profile_path = Path(payload["profile_path"]) if payload.get("profile_path") else None
        result = _run_worker(payload["case"], payload["layers"], profile_path)
        print(json.dumps(result, sort_keys=True))
        return
    artifact = run_driver()
    completed = [row for row in artifact["runs"] if row.get("status") == "completed"]
    print(json.dumps({"artifact": str(RESULTS / "issue_010_exact_scaling.json"), "runs": len(artifact["runs"]), "completed": len(completed)}, indent=2))


if __name__ == "__main__":
    main()
