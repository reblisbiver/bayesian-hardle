"""ISSUE-013 exact H2 bound and ragged child-batch measurement.

The control keeps the ISSUE-012 exact layers without child fusion.  The after
variant adds the exact ragged ``horizon_two_child_batch`` layer.  The capacity
bound is deliberately analysis-only because the support=500 replay found no
strict skips; its avoided-work counter therefore remains zero by construction.
Timeouts are bounded observations, never feasibility claims.
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
PROFILE_DIR = RESULTS / "issue_013_profiles"
sys.path.insert(0, str(SRC))

from bayesian_hardle.accelerated import ExactFeedbackCodeMatrix  # noqa: E402
from bayesian_hardle.belief import ExactPosteriorUpdater, UniformPrior  # noqa: E402
from bayesian_hardle.decision import DecisionState, ExactBayesOptimalPlanner  # noqa: E402
from bayesian_hardle.game import HardleFeedbackEngine  # noqa: E402


CONTROL_LAYERS = tuple(
    layer
    for layer in ExactBayesOptimalPlanner.ALL_OPTIMIZATION_LAYERS
    if layer != "horizon_two_child_batch"
)
FUSED_LAYERS = CONTROL_LAYERS + ("horizon_two_child_batch",)


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
    for size, seed, timeout in (
        (32, 32011, 60),
        (50, 50011, 60),
        (100, 100011, 90),
        (200, 200011, 120),
        (500, 500011, 180),
        (750, 750011, 90),
        (1000, 1000011, 120),
    ):
        support = sampled(size, seed)
        ladder.append(
            {
                "name": f"sample{size}_h3_legal{size + 8}",
                "support": support,
                "legal": legal_for(support, 8, seed + 1),
                "horizon": 3,
                "timeout_seconds": timeout,
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
    matrix_build_seconds = time.perf_counter() - started
    return (
        ExactBayesOptimalPlanner(
            feedback_matrix=matrix,
            optimization_layers=layers,
            root_audit=True,
            root_audit_limit=root_audit_limit,
        ),
        matrix_build_seconds,
    )


def _root_summary(instrumentation: Dict[str, Any]) -> Dict[str, Any]:
    records = instrumentation["root_action_records"]
    traced_branches = [branch for record in records for branch in record["branches"]]
    processed = [branch for branch in traced_branches if branch["processed"]]
    return {
        "root_actions_seen": instrumentation["root_actions_seen"],
        "root_actions_traced": instrumentation["root_actions_traced"],
        "root_actions_pruned": sum(1 for record in records if record["pruned"]),
        "root_pruning_ratio": (
            sum(1 for record in records if record["pruned"]) / len(records)
            if records
            else None
        ),
        "branches_evaluated": instrumentation["branches_evaluated"],
        "root_branches_traced": len(traced_branches),
        "root_branches_processed": len(processed),
        "child_h2_requests": instrumentation["root_child_state_requests"],
        "child_h2_exact_solves": instrumentation[
            "horizon_two_child_exact_solves"
        ],
        "bound_only_skips": instrumentation["horizon_two_bound_only_skips"],
        "h2_matrix_cells": instrumentation["horizon_two_batch_matrix_cells"],
        "child_batch_blocks": instrumentation[
            "horizon_two_child_batch_blocks"
        ],
        "child_batch_children": instrumentation[
            "horizon_two_child_batch_children"
        ],
        "child_batch_matrix_cells": instrumentation[
            "horizon_two_child_batch_matrix_cells"
        ],
        "child_batch_peak_temporary_bytes": instrumentation[
            "horizon_two_child_batch_peak_temporary_bytes"
        ],
        "root_child_reuse_ratio": (
            instrumentation["root_repeated_child_state_hits"]
            / instrumentation["root_child_state_requests"]
            if instrumentation["root_child_state_requests"]
            else 0.0
        ),
        "matrix_memory_bytes": instrumentation["matrix_memory_bytes"],
        "timing_seconds": instrumentation["root_timing_seconds"],
    }


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
        if "horizon_two_values_block" in name:
            bucket = "exact_child_block_batch"
        elif "_transition_branches" in name:
            bucket = "root_partition_or_transition_grouping"
        elif "horizon_two_values" in name or "numpy" in path:
            bucket = "exact_matrix_batch"
        elif "_canonical_key" in name or (name in {"get", "put"} and path.endswith("decision.py")):
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


def _bound_accounting(instrumentation: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "planner_enabled": False,
        "bound_only_skips": instrumentation["horizon_two_bound_only_skips"],
        "strict_child_action_skips": 0,
        "strict_root_action_skips": 0,
        "status": "analysis-only; capacity bound was too loose on support=500",
    }


def _run_worker(
    case: Dict[str, Any], layers: Sequence[str], profile_path: Optional[Path]
) -> Dict[str, Any]:
    support = tuple(case["support"])
    legal = tuple(case["legal"])
    feedback = HardleFeedbackEngine()
    updater = ExactPosteriorUpdater(feedback)
    state = DecisionState(UniformPrior().initial_belief(support), 3)
    planner, matrix_build_seconds = _make_planner(
        layers, legal, support, case.get("root_audit_limit")
    )
    profile = cProfile.Profile() if profile_path is not None else None
    started = time.perf_counter()
    if profile is not None:
        profile.enable()
    selected = planner.select_guess(state, legal, feedback, updater)
    value = planner._guess_value(state, selected, legal, feedback, updater)
    if profile is not None:
        profile.disable()
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile.dump_stats(str(profile_path))
        text_path = profile_path.with_suffix(".txt")
        with text_path.open("w", encoding="utf-8") as stream:
            pstats.Stats(profile, stream=stream).sort_stats("cumulative").print_stats(50)
    selection_seconds = time.perf_counter() - started
    instrumentation = planner.instrumentation()
    return {
        "status": "completed",
        "case": case["name"],
        "variant": "fused_child_batch"
        if "horizon_two_child_batch" in layers
        else "issue012_control",
        "layers": list(layers),
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
        "bound_accounting": _bound_accounting(instrumentation),
        "profile_path": str(profile_path.relative_to(ROOT)) if profile_path else None,
        "profile_breakdown": _profile_breakdown(profile_path),
    }


def _variant_name(layers: Sequence[str]) -> str:
    return "fused_child_batch" if "horizon_two_child_batch" in layers else "issue012_control"


def _run_bounded(
    case: Dict[str, Any], layers: Sequence[str], profile: bool = False
) -> Dict[str, Any]:
    variant = _variant_name(layers)
    profile_path = None
    if profile:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
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
            "variant": variant,
            "layers": list(layers),
            "support_size": len(case["support"]),
            "legal_size": len(case["legal"]),
            "horizon": case["horizon"],
            "timeout_seconds": case["timeout_seconds"],
            "elapsed_before_timeout": time.perf_counter() - started,
            "bound_only_skips": 0,
            "bounded_frontier": True,
        }
    if completed.returncode != 0:
        return {
            "status": "failed",
            "case": case["name"],
            "variant": variant,
            "layers": list(layers),
            "returncode": completed.returncode,
            "stderr": completed.stderr[-4000:],
            "stdout": completed.stdout[-2000:],
        }
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {
            "status": "failed",
            "case": case["name"],
            "variant": variant,
            "returncode": completed.returncode,
            "stderr": completed.stderr[-4000:],
            "stdout": completed.stdout[-4000:],
        }
    result["driver_elapsed_seconds"] = time.perf_counter() - started
    return result


def _schedule(cases: Sequence[Dict[str, Any]]) -> Tuple[Tuple[Dict[str, Any], Tuple[str, ...], bool], ...]:
    rows = []
    for case in cases:
        profile = case["name"] in {"sample100_h3_legal108", "sample500_h3_legal508"}
        rows.append((case, CONTROL_LAYERS, profile))
        rows.append((case, FUSED_LAYERS, profile))
    return tuple(rows)


def _markdown(artifact: Dict[str, Any]) -> str:
    lines = [
        "# ISSUE-013 horizon-2 bounds and exact child fusion",
        "",
        "The capacity bound is mathematically safe but analysis-only: its strict skip count is recorded as zero because the support=500 replay found no useful skips. The fused variant shares exact ragged matrix work across bounded H2 child blocks. A timeout is a bounded observation, not a feasibility claim.",
        "",
        "| Case | Variant | Status | Support | Legal | Total s | Select s | Root actions | Branches | Child requests | Exact child H2 | Bound skips | H2 cells | Blocks | Block children | Block cells | Peak temp B | Root prune | Selected |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in artifact["runs"]:
        if row.get("status") != "completed":
            lines.append(
                f"| {row.get('case')} | {row.get('variant')} | {row.get('status')} | {row.get('support_size', '-')} | {row.get('legal_size', '-')} | {row.get('elapsed_before_timeout', 0):.3f} | - | - | - | - | - | {row.get('bound_only_skips', 0)} | - | - | - | - | - | - | - |"
            )
            continue
        summary = row["root_summary"]
        lines.append(
            f"| {row['case']} | {row['variant']} | completed | {row['support_size']} | {row['legal_size']} | {row['total_seconds']:.3f} | {row['selection_seconds']:.3f} | {summary['root_actions_seen']} | {summary['branches_evaluated']} | {summary['child_h2_requests']} | {summary['child_h2_exact_solves']} | {summary['bound_only_skips']} | {summary['h2_matrix_cells']} | {summary['child_batch_blocks']} | {summary['child_batch_children']} | {summary['child_batch_matrix_cells']} | {summary['child_batch_peak_temporary_bytes']} | {summary['root_pruning_ratio']} | {row['selected_guess']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `h2_matrix_cells` is the exact child H2 logical work; `child_batch_matrix_cells` is the same logical work observed through the fused path, not padded cells.",
            "- `child_h2_exact_solves` counts child states whose H2 values were actually computed, excluding cache/closed-form-only children.",
            "- `bound_only_skips` is zero because the capacity bound was not promoted into the planner after the measured zero-skip result; no work is claimed as avoided by the bound.",
            "- `root_pruning_ratio` is exact branch-and-bound over fully traced completed rows; bounded full-support traces may have limited root audit records.",
            "",
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
                f"Largest completed exact horizon-3 row: `{largest['case']}` / `{largest['variant']}` with support={largest['support_size']}, legal={largest['legal_size']}."
                if largest
                else "No completed exact horizon-3 row."
            ),
            "The curated 2,315 × 12,974 h=3 probe is explicitly bounded; timeout rows are not feasibility claims.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_artifact(artifact: Dict[str, Any]) -> None:
    if artifact.get("format") != 1 or artifact.get("issue") != "ISSUE-013":
        raise ValueError("unexpected artifact identity")
    runs = artifact.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("artifact must contain runs")
    for row in runs:
        if row.get("status") == "completed":
            summary = row.get("root_summary", {})
            required = {
                "child_h2_requests",
                "child_h2_exact_solves",
                "bound_only_skips",
                "h2_matrix_cells",
                "child_batch_blocks",
                "child_batch_children",
                "child_batch_matrix_cells",
                "child_batch_peak_temporary_bytes",
            }
            if not required.issubset(summary):
                raise ValueError(f"completed row missing fields: {row.get('case')}")
            if row.get("selected_guess") is None or row.get("value") is None:
                raise ValueError(f"completed row missing exact result: {row.get('case')}")
            if any(summary[key] < 0 for key in required if isinstance(summary[key], (int, float))):
                raise ValueError(f"negative counter in row: {row.get('case')}")
        elif row.get("status") == "timed_out":
            if not row.get("bounded_frontier") or row.get("timeout_seconds", 0) <= 0:
                raise ValueError(f"invalid timeout row: {row.get('case')}")
        else:
            raise ValueError(f"unexpected run status: {row.get('status')}")


def run_driver() -> Dict[str, Any]:
    cases = _cases()
    runs = []
    for case, layers, profile in _schedule(cases):
        runs.append(_run_bounded(case, layers, profile))
    completed = [row for row in runs if row.get("status") == "completed"]
    artifact = {
        "format": 1,
        "issue": "ISSUE-013",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": sys.version,
        "platform": sys.platform,
        "control_layers": list(CONTROL_LAYERS),
        "fused_layers": list(FUSED_LAYERS),
        "bound": {
            "planner_enabled": False,
            "code_count": 36,
            "strict_skips_on_support500_spike": 0,
            "reason": "capacity bound was too loose to be net-positive",
        },
        "cases": list(cases),
        "runs": runs,
        "largest_completed": max(
            completed,
            key=lambda row: (row["support_size"], row["legal_size"]),
            default=None,
        ),
    }
    validate_artifact(artifact)
    RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = RESULTS / "issue_013_horizon2_bounds_batch.json"
    markdown_path = RESULTS / "issue_013_horizon2_bounds_batch_summary.md"
    json_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    markdown_path.write_text(_markdown(artifact), encoding="utf-8")
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", help="JSON payload for one bounded worker run")
    parser.add_argument("--validate", type=Path, help="validate an artifact JSON")
    args = parser.parse_args()
    if args.worker:
        payload = json.loads(args.worker)
        profile_path = Path(payload["profile_path"]) if payload.get("profile_path") else None
        result = _run_worker(payload["case"], payload["layers"], profile_path)
        print(json.dumps(result, sort_keys=True))
        return
    if args.validate:
        validate_artifact(json.loads(args.validate.read_text(encoding="utf-8")))
        print(json.dumps({"validated": str(args.validate)}))
        return
    artifact = run_driver()
    print(
        json.dumps(
            {
                "artifact": str(RESULTS / "issue_013_horizon2_bounds_batch.json"),
                "runs": len(artifact["runs"]),
                "completed": sum(row.get("status") == "completed" for row in artifact["runs"]),
                "timed_out": sum(row.get("status") == "timed_out" for row in artifact["runs"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
