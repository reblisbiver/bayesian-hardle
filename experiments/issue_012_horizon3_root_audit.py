"""ISSUE-012 horizon-3 root decomposition and exact ordering audit.

The benchmark keeps the ISSUE-011 exact planner semantics and compares its
ordering with one additional exact-safe ordering proxy. Every completed
horizon-3 ladder row records root action branches, child-state reuse, h=2
batch work, timing buckets, and exact pruning. The 2,315 x 12,974 probe is
bounded and a timeout is reported as an observed frontier, never feasibility.
"""

from __future__ import annotations

import argparse
import cProfile
import json
from pathlib import Path
import pstats
import random
import subprocess
import sys
import time
from typing import Any, Dict, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
RESULTS = ROOT / "experiments" / "results"
PROFILE_DIR = RESULTS / "issue_012_profiles"
sys.path.insert(0, str(SRC))

from bayesian_hardle.accelerated import ExactFeedbackCodeMatrix  # noqa: E402
from bayesian_hardle.belief import ExactPosteriorUpdater, UniformPrior  # noqa: E402
from bayesian_hardle.decision import DecisionState, ExactBayesOptimalPlanner  # noqa: E402
from bayesian_hardle.game import HardleFeedbackEngine  # noqa: E402


ISSUE011_LAYERS = (
    "closed_forms",
    "matrix_transitions",
    "canonical_memoization",
    "action_ordering",
    "branch_ordering",
    "branch_and_bound",
    "horizon_two_closed_form",
    "horizon_two_batch",
)
PROXY_LAYERS = ISSUE011_LAYERS + ("root_horizon_two_ordering",)


def _words(path: Path) -> Tuple[str, ...]:
    return tuple(
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def _cases() -> Tuple[Dict[str, Any], ...]:
    curated = _words(ROOT / "data" / "wordlists" / "wordle-candidate-answers.txt")
    legal_all = tuple(
        sorted(
            set(_words(ROOT / "data" / "wordlists" / "wordle-legal-guesses.txt"))
            | {"covid", "padel"}
        )
    )

    def sampled(size: int, seed: int) -> Tuple[str, ...]:
        return tuple(sorted(random.Random(seed).sample(curated, size)))

    def legal_for(support: Sequence[str], probes: int, seed: int) -> Tuple[str, ...]:
        support_set = set(support)
        extras = [word for word in legal_all if word not in support_set]
        return tuple(
            sorted(support_set | set(random.Random(seed).sample(extras, probes)))
        )

    ladder = []
    for size, seed in (
        (32, 32011),
        (50, 50011),
        (100, 100011),
        (200, 200011),
        (500, 500011),
    ):
        support = sampled(size, seed)
        ladder.append(
            {
                "name": f"sample{size}_h3_legal{size + 8}",
                "support": support,
                "legal": legal_for(support, 8, seed + 1),
                "horizon": 3,
                "timeout_seconds": 120 if size >= 200 else 60,
            }
        )
    ladder.append(
        {
            "name": "curated2315_h3_fulllegal",
            "support": tuple(curated),
            "legal": tuple(legal_all),
            "horizon": 3,
            "timeout_seconds": 45,
            "root_audit_limit": 8,
        }
    )
    return tuple(ladder)


def _make_planner(
    layers: Sequence[str],
    legal: Sequence[str],
    support: Sequence[str],
    root_audit_limit: Optional[int],
) -> Tuple[ExactBayesOptimalPlanner, float]:
    started = time.perf_counter()
    matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, support)
    build_seconds = time.perf_counter() - started
    planner = ExactBayesOptimalPlanner(
        feedback_matrix=matrix,
        optimization_layers=layers,
        root_audit=True,
        root_audit_limit=root_audit_limit,
    )
    return planner, build_seconds


def _root_summary(instrumentation: Dict[str, Any]) -> Dict[str, Any]:
    records = instrumentation["root_action_records"]
    branches = [branch for record in records for branch in record["branches"]]
    processed = [branch for branch in branches if branch["processed"]]
    support_total = sum(branch["support_size"] for branch in branches)
    return {
        "states_evaluated": instrumentation["states_evaluated"],
        "actions_evaluated": instrumentation["actions_evaluated"],
        "branches_evaluated": instrumentation["branches_evaluated"],
        "matrix_memory_bytes": instrumentation["matrix_memory_bytes"],
        "root_actions_seen": instrumentation["root_actions_seen"],
        "root_actions_traced": instrumentation["root_actions_traced"],
        "root_audit_truncated": instrumentation["root_audit_truncated"],
        "root_branches_total": len(branches),
        "root_branches_processed": len(processed),
        "mean_branches_per_traced_action": (
            len(branches) / len(records) if records else None
        ),
        "mean_child_support_per_branch": (
            support_total / len(branches) if branches else None
        ),
        "root_actions_pruned": sum(1 for record in records if record["pruned"]),
        "root_pruning_ratio": (
            sum(1 for record in records if record["pruned"]) / len(records)
            if records
            else None
        ),
        "root_child_state_requests": instrumentation["root_child_state_requests"],
        "root_distinct_child_state_keys": instrumentation[
            "root_distinct_child_state_keys"
        ],
        "root_repeated_child_state_hits": instrumentation[
            "root_repeated_child_state_hits"
        ],
        "root_child_reuse_ratio": (
            instrumentation["root_repeated_child_state_hits"]
            / instrumentation["root_child_state_requests"]
            if instrumentation["root_child_state_requests"]
            else 0.0
        ),
        "root_child_cache_hits": sum(
            record["child_cache_hits"] for record in records
        ),
        "horizon_two_batch_calls": sum(
            record["horizon_two_batch_calls"] for record in records
        ),
        "horizon_two_batch_actions": sum(
            record["horizon_two_batch_actions"] for record in records
        ),
        "horizon_two_batch_matrix_cells": sum(
            record["horizon_two_batch_matrix_cells"] for record in records
        ),
        "timing_seconds": instrumentation["root_timing_seconds"],
        "time_to_first_incumbent_seconds": instrumentation[
            "root_first_incumbent_seconds"
        ],
        "time_to_final_incumbent_seconds": instrumentation[
            "root_final_incumbent_seconds"
        ],
    }


def _partition_diagnostic(
    legal: Sequence[str], support: Sequence[str], feedback: HardleFeedbackEngine
) -> Dict[str, Any]:
    def wordle_pattern(guess: str, target: str) -> Tuple[int, ...]:
        pattern = [0] * len(guess)
        remaining: Dict[str, int] = {}
        for index, (guessed, actual) in enumerate(zip(guess, target)):
            if guessed == actual:
                pattern[index] = 2
            else:
                remaining[actual] = remaining.get(actual, 0) + 1
        for index, guessed in enumerate(guess):
            if pattern[index] == 0 and remaining.get(guessed, 0):
                pattern[index] = 1
                remaining[guessed] -= 1
        return tuple(pattern)

    result: Dict[str, Any] = {}
    for name, evaluator in (
        ("hardle", lambda guess, target: feedback.evaluate(guess, target)),
        ("position_pattern_diagnostic", wordle_pattern),
    ):
        branch_counts = []
        support_per_branch = []
        for guess in legal:
            groups: Dict[object, int] = {}
            for target in support:
                outcome = evaluator(guess, target)
                groups[outcome] = groups.get(outcome, 0) + 1
            branch_counts.append(len(groups))
            support_per_branch.extend(groups.values())
        result[name] = {
            "actions": len(legal),
            "support": len(support),
            "mean_branches_per_action": sum(branch_counts) / len(legal),
            "mean_child_support_per_branch": sum(support_per_branch)
            / len(support_per_branch),
        }
    result["hardle_to_position_child_support_ratio"] = (
        result["hardle"]["mean_child_support_per_branch"]
        / result["position_pattern_diagnostic"]["mean_child_support_per_branch"]
    )
    return result


def _profile_breakdown(profile_path: Optional[Path]) -> Dict[str, Dict[str, float]]:
    if profile_path is None or not profile_path.exists():
        return {}
    stats = pstats.Stats(str(profile_path))
    buckets: Dict[str, Dict[str, float]] = {}

    def add(bucket: str, cc: int, nc: int, internal: float, cumulative: float) -> None:
        row = buckets.setdefault(
            bucket,
            {
                "calls": 0,
                "primitive_calls": 0,
                "internal_seconds": 0.0,
                "cumulative_seconds": 0.0,
            },
        )
        row["calls"] += cc
        row["primitive_calls"] += nc
        row["internal_seconds"] += internal
        row["cumulative_seconds"] += cumulative

    for (filename, _, function), (cc, nc, internal, cumulative, _) in stats.stats.items():
        name = str(function)
        lowered = name.lower()
        path = str(filename)
        bucket = None
        if "_transition_branches" in name:
            bucket = "root_partition_or_transition_grouping"
        elif "horizon_two_values" in name or "numpy" in path:
            bucket = "exact_matrix_batch"
        elif "_canonical_key" in name or name in {"get", "put"} and path.endswith("decision.py"):
            bucket = "cache_key_handling"
        elif "_best_guess" in name or "_guess_value" in name:
            bucket = "recursive_child_state_expansion"
        elif "_ordered_actions" in name or "_root_horizon_two_proxy" in name:
            bucket = "root_ordering"
        elif "_posterior_for_branch" in name or "__post_init__" in name:
            bucket = "posterior_construction"
        if bucket is not None:
            add(bucket, cc, nc, internal, cumulative)
    return dict(sorted(buckets.items()))


def _run_worker(
    case: Dict[str, Any], layers: Sequence[str], profile_path: Optional[Path]
) -> Dict[str, Any]:
    support = tuple(case["support"])
    legal = tuple(case["legal"])
    feedback = HardleFeedbackEngine()
    updater = ExactPosteriorUpdater(feedback)
    state = DecisionState(UniformPrior().initial_belief(support), 3)
    planner, matrix_build_seconds = _make_planner(
        layers,
        legal,
        support,
        case.get("root_audit_limit"),
    )
    profile = cProfile.Profile() if profile_path is not None else None
    started = time.perf_counter()
    if profile is not None:
        profile.enable()
    selected = planner.select_guess(state, legal, feedback, updater)
    value = planner._guess_value(state, selected, legal, feedback, updater)
    if profile is not None:
        profile.disable()
        profile.dump_stats(str(profile_path))
        text_path = PROFILE_DIR / (profile_path.stem + ".txt")
        with text_path.open("w", encoding="utf-8") as stream:
            pstats.Stats(profile, stream=stream).sort_stats("cumulative").print_stats(40)
    selection_seconds = time.perf_counter() - started
    instrumentation = planner.instrumentation()
    result: Dict[str, Any] = {
        "status": "completed",
        "case": case["name"],
        "layers": list(layers),
        "variant": "issue012_proxy_order"
        if "root_horizon_two_ordering" in layers
        else "issue011_order",
        "support_size": len(support),
        "legal_size": len(legal),
        "horizon": 3,
        "selected_guess": selected,
        "value": list(value) if value is not None else None,
        "matrix_build_seconds": matrix_build_seconds,
        "selection_seconds": selection_seconds,
        "total_seconds": matrix_build_seconds + selection_seconds,
        "instrumentation": instrumentation,
        "root_summary": _root_summary(instrumentation),
        "profile_path": str(profile_path.relative_to(ROOT)) if profile_path else None,
        "profile_breakdown": _profile_breakdown(profile_path),
    }
    if case["name"] == "sample32_h3_legal40":
        result["feedback_partition_diagnostic"] = _partition_diagnostic(
            legal, support, feedback
        )
    return result


def _run_bounded(
    case: Dict[str, Any], layers: Sequence[str], profile: bool = False
) -> Dict[str, Any]:
    profile_path = None
    if profile:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        variant = "issue012_proxy_order" if "root_horizon_two_ordering" in layers else "issue011_order"
        profile_path = PROFILE_DIR / f"{case['name']}__{variant}.prof"
    payload = json.dumps(
        {
            "case": case,
            "layers": list(layers),
            "profile_path": str(profile_path) if profile_path else None,
        }
    )
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            [sys.executable, str(Path(__file__)), "--worker", payload],
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
            "variant": "issue012_proxy_order"
            if "root_horizon_two_ordering" in layers
            else "issue011_order",
            "layers": list(layers),
            "support_size": len(case["support"]),
            "legal_size": len(case["legal"]),
            "horizon": case["horizon"],
            "timeout_seconds": case["timeout_seconds"],
            "elapsed_before_timeout": time.perf_counter() - started,
            "bounded_frontier": True,
        }
    if completed.returncode != 0:
        return {
            "status": "failed",
            "case": case["name"],
            "variant": "issue012_proxy_order"
            if "root_horizon_two_ordering" in layers
            else "issue011_order",
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
            "variant": "issue012_proxy_order"
            if "root_horizon_two_ordering" in layers
            else "issue011_order",
            "returncode": completed.returncode,
            "stderr": completed.stderr[-4000:],
            "stdout": completed.stdout[-4000:],
        }
    result["driver_elapsed_seconds"] = time.perf_counter() - started
    return result


def _schedule(cases: Sequence[Dict[str, Any]]) -> Tuple[Tuple[Dict[str, Any], Tuple[str, ...], bool], ...]:
    rows = []
    for case in cases:
        rows.append((case, ISSUE011_LAYERS, case["name"] in {"sample100_h3_legal108"}))
        rows.append((case, PROXY_LAYERS, case["name"] in {"sample100_h3_legal108"}))
    return tuple(rows)


def _markdown(artifact: Dict[str, Any]) -> str:
    lines = [
        "# ISSUE-012 horizon-3 root decomposition and exact pruning",
        "",
        "All planner values use the accepted exact Hardle semantics and lexicographic objective. `issue011_order` is the pre-ISSUE-012 ordering control; `issue012_proxy_order` adds one exact h=2 matrix proxy for order only. A timeout is a bounded observation, not a feasibility claim.",
        "",
        "| Case | Variant | Status | Support | Legal | Total s | Matrix s | Select s | States | Actions | Branches | Root branches/action | Child requests | Distinct | Reuse ratio | h2 cells | Root prune ratio | Matrix bytes | Selected |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in artifact["runs"]:
        if row.get("status") != "completed":
            lines.append(
                f"| {row.get('case')} | {row.get('variant')} | {row.get('status')} | {row.get('support_size', '-') } | {row.get('legal_size', '-') } | {row.get('elapsed_before_timeout', 0):.3f} | - | - | - | - | - | - | - | - | - | - | - | - | - |"
            )
            continue
        summary = row["root_summary"]
        lines.append(
            f"| {row['case']} | {row['variant']} | completed | {row['support_size']} | {row['legal_size']} | {row['total_seconds']:.3f} | {row['matrix_build_seconds']:.3f} | {row['selection_seconds']:.3f} | {summary['states_evaluated']} | {summary['actions_evaluated']} | {summary['branches_evaluated']} | {summary['mean_branches_per_traced_action']:.2f} | {summary['root_child_state_requests']} | {summary['root_distinct_child_state_keys']} | {summary['root_child_reuse_ratio']:.3f} | {summary['horizon_two_batch_matrix_cells']} | {summary['root_pruning_ratio']:.3f} | {summary['matrix_memory_bytes']} | {row['selected_guess']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `horizon_two_batch_matrix_cells` is child h=2 work; root ordering proxy cells are reported separately in planner instrumentation and are not counted as child solves.",
            "- `root_child_reuse_ratio` counts repeated exact canonical child-state keys across feedback branches and root guesses. The planner already has exact canonical memoization; a new cache is not added merely because a duplicate exists.",
            "- Root pruning is exact branch-and-bound only. Ordering changes visit order and incumbent timing; it does not remove candidates or change the result.",
            "- Root partition, child h=2, cache/key, pruning, and proxy timings are in each completed row's `root_summary.timing_seconds`.",
            "",
            "## Hardle structural diagnostic",
            "",
        ]
    )
    for row in artifact["runs"]:
        diagnostic = row.get("feedback_partition_diagnostic")
        if diagnostic:
            lines.append(f"### {row['variant']} / {row['case']}")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(diagnostic, indent=2, sort_keys=True))
            lines.append("```")
            lines.append("")
    lines.extend(
        [
            "## Profile buckets",
            "",
            "| Run | Bucket | Calls | Internal s | Cumulative s |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for row in artifact["runs"]:
        for bucket, values in row.get("profile_breakdown", {}).items():
            lines.append(
                f"| {row['variant']} / {row['case']} | {bucket} | {int(values['calls'])} | {values['internal_seconds']:.6f} | {values['cumulative_seconds']:.6f} |"
            )
    largest = artifact.get("largest_completed")
    lines.extend(
        [
            "",
            "## Frontier",
            "",
            (
                f"Largest completed horizon-3 row: `{largest['case']}` / `{largest['variant']}` with support={largest['support_size']}, legal={largest['legal_size']}."
                if largest
                else "No completed horizon-3 row."
            ),
            "The curated 2,315 x 12,974 probe is explicitly bounded; its row records timeout rather than feasibility unless a worker completes it.",
            "",
        ]
    )
    return "\n".join(lines)


def run_driver() -> Dict[str, Any]:
    cases = _cases()
    runs = []
    for case, layers, profile in _schedule(cases):
        runs.append(_run_bounded(case, layers, profile))
    completed = [row for row in runs if row.get("status") == "completed"]
    artifact = {
        "format": 1,
        "issue": "ISSUE-012",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": sys.version,
        "platform": sys.platform,
        "issue011_layers": list(ISSUE011_LAYERS),
        "proxy_layers": list(PROXY_LAYERS),
        "cases": list(cases),
        "runs": runs,
        "largest_completed": max(
            completed,
            key=lambda row: (row["support_size"], row["legal_size"]),
            default=None,
        ),
        "full_probe": [
            {
                "variant": row.get("variant"),
                "status": row.get("status"),
                "support_size": row.get("support_size"),
                "legal_size": row.get("legal_size"),
                "timeout_seconds": row.get("timeout_seconds"),
                "elapsed_before_timeout": row.get("elapsed_before_timeout"),
            }
            for row in runs
            if row.get("case") == "curated2315_h3_fulllegal"
        ],
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = RESULTS / "issue_012_horizon3_root_audit.json"
    markdown_path = RESULTS / "issue_012_horizon3_root_audit_summary.md"
    json_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(_markdown(artifact), encoding="utf-8")
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
    print(
        json.dumps(
            {
                "artifact": str(RESULTS / "issue_012_horizon3_root_audit.json"),
                "runs": len(artifact["runs"]),
                "completed": sum(row.get("status") == "completed" for row in artifact["runs"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
