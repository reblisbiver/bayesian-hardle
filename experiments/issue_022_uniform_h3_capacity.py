"""Paired ISSUE-022 benchmark for the exact uniform-H3 root capacity bound."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import subprocess
import sys
import time
from typing import Any, Dict, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
RESULTS = ROOT / "experiments" / "results"
sys.path.insert(0, str(SRC))

from bayesian_hardle.accelerated import ExactFeedbackCodeMatrix  # noqa: E402
from bayesian_hardle.belief import ExactPosteriorUpdater, UniformPrior  # noqa: E402
from bayesian_hardle.decision import DecisionState, ExactBayesOptimalPlanner  # noqa: E402
from bayesian_hardle.game import HardleFeedbackEngine  # noqa: E402


CONTROL_LAYERS = tuple(
    layer
    for layer in ExactBayesOptimalPlanner.ALL_OPTIMIZATION_LAYERS
    if layer
    not in {
        "horizon_two_child_batch",
        "uniform_h3_branch_capacity",
    }
)
AFTER_LAYERS = CONTROL_LAYERS + ("uniform_h3_branch_capacity",)


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
        (500, 500011, 180),
        (1000, 1000011, 240),
        (1250, 1250011, 300),
        (1500, 1500011, 360),
        (1750, 1750011, 420),
        (2000, 2000011, 480),
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
        "root_actions_started": instrumentation["root_actions_started"],
        "root_actions_seen": instrumentation["root_actions_seen"],
        "root_actions_completed": instrumentation["root_actions_completed"],
        "root_actions_pruned": instrumentation["root_actions_pruned"],
        "root_actions_traced": instrumentation["root_actions_traced"],
        "root_actions_pruned_before_first_child": instrumentation[
            "uniform_h3_capacity_pruned_before_first_child"
        ],
        "branches_evaluated": instrumentation["branches_evaluated"],
        "root_branches_traced": len(traced_branches),
        "root_branches_processed": len(processed),
        "child_h2_solve_requests": instrumentation["root_child_state_requests"],
        "child_h2_value_calls": instrumentation["horizon_two_batch_calls"]
        + instrumentation["horizon_two_scalar_calls"],
        "child_h2_exact_solves": instrumentation["horizon_two_child_exact_solves"],
        "matrix_cells": instrumentation["horizon_two_batch_matrix_cells"]
        + instrumentation["horizon_two_child_batch_matrix_cells"],
        "capacity_initializations": instrumentation[
            "uniform_h3_capacity_initializations"
        ],
        "capacity_pruned_actions": instrumentation[
            "uniform_h3_capacity_pruned_actions"
        ],
        "root_pruning_ratio": (
            instrumentation["root_actions_pruned"]
            / instrumentation["root_actions_started"]
            if instrumentation["root_actions_started"]
            else None
        ),
        "matrix_memory_bytes": instrumentation["matrix_memory_bytes"],
        "timing_seconds": instrumentation["root_timing_seconds"],
    }


def _run_worker(
    case: Dict[str, Any], layers: Sequence[str]
) -> Dict[str, Any]:
    support = tuple(case["support"])
    legal = tuple(case["legal"])
    feedback = HardleFeedbackEngine()
    updater = ExactPosteriorUpdater(feedback)
    state = DecisionState(UniformPrior().initial_belief(support), 3)
    planner, matrix_build_seconds = _make_planner(
        layers, legal, support, case.get("root_audit_limit")
    )
    started = time.perf_counter()
    selected = planner.select_guess(state, legal, feedback, updater)
    value = planner._guess_value(state, selected, legal, feedback, updater)
    selection_seconds = time.perf_counter() - started
    instrumentation = planner.instrumentation()
    return {
        "status": "completed",
        "case": case["name"],
        "variant": "after" if "uniform_h3_branch_capacity" in layers else "control",
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
    }


def _variant_name(layers: Sequence[str]) -> str:
    return "after" if "uniform_h3_branch_capacity" in layers else "control"


def _run_bounded(case: Dict[str, Any], layers: Sequence[str]) -> Dict[str, Any]:
    variant = _variant_name(layers)
    payload = json.dumps({"case": case, "layers": list(layers)})
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
            "bounded_frontier": True,
        }
    if completed.returncode != 0:
        return {
            "status": "failed",
            "case": case["name"],
            "variant": variant,
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


def _equivalence(runs: Sequence[Dict[str, Any]]) -> Tuple[Dict[str, Any], ...]:
    by_case: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for row in runs:
        by_case.setdefault(row["case"], {})[row["variant"]] = row
    results = []
    for case, variants in sorted(by_case.items()):
        control = variants.get("control")
        after = variants.get("after")
        result: Dict[str, Any] = {"case": case}
        if not control or not after:
            result.update({"status": "not_comparable", "reason": "missing_variant"})
        elif control.get("status") != "completed" or after.get("status") != "completed":
            result.update(
                {
                    "status": "not_comparable",
                    "reason": "one_or_both_bounded",
                    "control_status": control.get("status"),
                    "after_status": after.get("status"),
                }
            )
        else:
            control_value = control["value"]
            after_value = after["value"]
            result.update(
                {
                    "status": "equivalent"
                    if control["selected_guess"] == after["selected_guess"]
                    and all(
                        abs(float(a) - float(b)) <= 1e-12
                        for a, b in zip(control_value, after_value)
                    )
                    else "mismatch",
                    "control_selected_guess": control["selected_guess"],
                    "after_selected_guess": after["selected_guess"],
                    "control_value": control_value,
                    "after_value": after_value,
                    "max_abs_value_delta": max(
                        abs(float(a) - float(b))
                        for a, b in zip(control_value, after_value)
                    ),
                }
            )
        results.append(result)
    return tuple(results)


def validate_artifact(artifact: Dict[str, Any]) -> None:
    if artifact.get("format") != 1 or artifact.get("issue") != "ISSUE-022":
        raise ValueError("unexpected artifact identity")
    for row in artifact.get("runs", ()):
        if row.get("status") == "completed":
            summary = row.get("root_summary", {})
            required = {
                "root_actions_started",
                "root_actions_completed",
                "root_actions_pruned_before_first_child",
                "child_h2_solve_requests",
                "child_h2_value_calls",
                "child_h2_exact_solves",
                "matrix_cells",
            }
            if not required.issubset(summary):
                raise ValueError(f"completed row missing fields: {row.get('case')}")
            if row.get("selected_guess") is None or row.get("value") is None:
                raise ValueError(f"completed row missing exact result: {row.get('case')}")
        elif row.get("status") == "timed_out":
            if not row.get("bounded_frontier") or row.get("timeout_seconds", 0) <= 0:
                raise ValueError(f"invalid timeout row: {row.get('case')}")
        else:
            raise ValueError(f"unexpected run status: {row.get('status')}")


def _markdown(artifact: Dict[str, Any]) -> str:
    lines = [
        "# ISSUE-022 uniform-H3 branch-capacity pruning",
        "",
        "Control and after use identical action/branch order and all existing exact layers; after adds only `uniform_h3_branch_capacity`. A timeout is a bounded observation, not a completion claim.",
        "",
        "| Case | Variant | Status | Support | Legal | Wall s | Root started | Root completed | Pruned before child | Child requests | Child H2 calls | Exact H2 solves | Matrix cells | Selected | Value |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in artifact["runs"]:
        if row.get("status") != "completed":
            lines.append(
                f"| {row.get('case')} | {row.get('variant')} | {row.get('status')} | {row.get('support_size', '-')} | {row.get('legal_size', '-')} | {row.get('elapsed_before_timeout', 0):.3f} | - | - | - | - | - | - | - | - | - |"
            )
            continue
        summary = row["root_summary"]
        lines.append(
            f"| {row['case']} | {row['variant']} | completed | {row['support_size']} | {row['legal_size']} | {row['selection_seconds']:.3f} | {summary['root_actions_started']} | {summary['root_actions_completed']} | {summary['root_actions_pruned_before_first_child']} | {summary['child_h2_solve_requests']} | {summary['child_h2_value_calls']} | {summary['child_h2_exact_solves']} | {summary['matrix_cells']} | {row['selected_guess']} | {row['value']} |"
        )
    lines.extend(["", "## Paired equivalence", ""])
    for result in artifact["paired_equivalence"]:
        lines.append(f"- `{result['case']}`: `{result['status']}` — {result}")
    lines.extend(
        [
            "",
            "## Bound accounting",
            "",
            "For eligible uniform H3 roots, each non-winning child of support `n` contributes at most `min(36,n)/N` to root success; a winning branch contributes exactly `1/N`. Capacity units are summed once per root partition and decremented as branches become processed. Weighted roots, non-H3 horizons, non-5-letter engines, and other ineligible paths retain the existing `1 - processed_probability` bound.",
            "",
            "## Curated confirmation",
            "",
            str(artifact.get("curated_confirmation")),
            "",
        ]
    )
    return "\n".join(lines)


def run_driver() -> Dict[str, Any]:
    cases = _cases()
    runs = []
    for case in cases:
        runs.append(_run_bounded(case, CONTROL_LAYERS))
        runs.append(_run_bounded(case, AFTER_LAYERS))
    confirmation = None
    curated_after = next(
        (
            row
            for row in runs
            if row["case"] == "curated2315_h3_fulllegal" and row["variant"] == "after"
        ),
        None,
    )
    if curated_after and curated_after.get("status") == "completed":
        confirmation = _run_bounded(
            next(case for case in cases if case["name"] == "curated2315_h3_fulllegal"),
            AFTER_LAYERS,
        )
        confirmation["variant"] = "after_confirmation"
    artifact = {
        "format": 1,
        "issue": "ISSUE-022",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": sys.version,
        "platform": sys.platform,
        "requested_base": "a37a22f7a795c7a3434283e204cb860db8f95f0d",
        "requested_base_available": False,
        "base_used": "9ac070cb49b15392da1e5e1dffc22da6c7ec9ed5",
        "control_layers": list(CONTROL_LAYERS),
        "after_layers": list(AFTER_LAYERS),
        "code_count": 36,
        "cases": list(cases),
        "runs": runs,
        "paired_equivalence": list(_equivalence(runs)),
        "curated_confirmation": confirmation,
    }
    validate_artifact(artifact)
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "issue_022_uniform_h3_capacity.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (RESULTS / "issue_022_uniform_h3_capacity_summary.md").write_text(
        _markdown(artifact), encoding="utf-8"
    )
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", help="JSON payload for one bounded worker run")
    parser.add_argument("--validate", type=Path, help="validate an artifact JSON")
    args = parser.parse_args()
    if args.worker:
        payload = json.loads(args.worker)
        print(json.dumps(_run_worker(payload["case"], payload["layers"]), sort_keys=True))
        return
    if args.validate:
        validate_artifact(json.loads(args.validate.read_text(encoding="utf-8")))
        print(json.dumps({"validated": str(args.validate)}))
        return
    artifact = run_driver()
    print(
        json.dumps(
            {
                "artifact": str(RESULTS / "issue_022_uniform_h3_capacity.json"),
                "runs": len(artifact["runs"]),
                "completed": sum(row.get("status") == "completed" for row in artifact["runs"]),
                "timed_out": sum(row.get("status") == "timed_out" for row in artifact["runs"]),
                "curated_confirmation": artifact["curated_confirmation"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
