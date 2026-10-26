"""ISSUE-011 exact planner hotspot and horizon-2 scaling audit.

This driver preserves the ISSUE-010 small ladder, adds deterministic support
sizes above 20, and records exact planner structure plus selected cProfile
breakdowns. Bounded timeouts are emitted as observations, never feasibility
claims.
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
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
RESULTS = ROOT / "experiments" / "results"
PROFILE_DIR = RESULTS / "issue_011_profiles"
sys.path.insert(0, str(SRC))

from bayesian_hardle.accelerated import ExactFeedbackCodeMatrix  # noqa: E402
from bayesian_hardle.belief import ExactPosteriorUpdater, UniformPrior  # noqa: E402
from bayesian_hardle.decision import (  # noqa: E402
    DecisionState,
    ExactBayesOptimalPlanner,
    ExactBayesOptimalReferencePlanner,
)
from bayesian_hardle.game import HardleFeedbackEngine  # noqa: E402


ISSUE010_LAYERS = (
    "closed_forms",
    "matrix_transitions",
    "canonical_memoization",
    "action_ordering",
    "branch_ordering",
    "branch_and_bound",
)
FULL_LAYERS = ISSUE010_LAYERS + (
    "horizon_two_closed_form",
    "horizon_two_batch",
)

LEGACY_LADDER = (
    ("baseline_reference", ()),
    ("closed_forms", ("closed_forms",)),
    (
        "matrix_transitions",
        ("closed_forms", "matrix_transitions"),
    ),
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
        ISSUE010_LAYERS[:-1],
    ),
    ("issue010_full", ISSUE010_LAYERS),
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
    legacy = [
        {
            "name": "fixture5_h3_legal10",
            "support": ("awake", "cigar", "humph", "rebut", "sissy"),
            "legal": tuple(
                sorted(
                    {
                        "adieu",
                        "arise",
                        "awake",
                        "cigar",
                        "covid",
                        "humph",
                        "padel",
                        "rebut",
                        "sissy",
                        "stare",
                    }
                )
            ),
            "horizon": 3,
            "timeout_seconds": 30,
        }
    ]

    def sampled(size: int, seed: int) -> Tuple[str, ...]:
        return tuple(sorted(random.Random(seed).sample(curated, size)))

    def legal_for(support: Sequence[str], probes: int, seed: int) -> Tuple[str, ...]:
        support_set = set(support)
        extras = [word for word in legal_all if word not in support_set]
        extras = random.Random(seed).sample(extras, probes)
        return tuple(sorted(support_set | set(extras)))

    for size, seed, probes in ((8, 8010, 8), (12, 12010, 8), (20, 20010, 8)):
        support = sampled(size, seed)
        legacy.append(
            {
                "name": f"sample{size}_h3_legal{size + probes}",
                "support": support,
                "legal": legal_for(support, probes, seed + 1),
                "horizon": 3,
                "timeout_seconds": 60 if size >= 20 else 30,
            }
        )

    full_support = tuple(curated)
    full_legal = tuple(legal_all)
    legacy.extend(
        [
            {
                "name": "curated2315_h1_fulllegal",
                "support": full_support,
                "legal": full_legal,
                "horizon": 1,
                "timeout_seconds": 30,
            },
            {
                "name": "curated2315_h2_fulllegal",
                "support": full_support,
                "legal": full_legal,
                "horizon": 2,
                "timeout_seconds": 30,
            },
        ]
    )

    added = []
    for size, seed in ((32, 32011), (50, 50011), (100, 100011), (200, 200011), (500, 500011)):
        support = sampled(size, seed)
        added.append(
            {
                "name": f"sample{size}_h2_legal{size + 8}",
                "support": support,
                "legal": legal_for(support, 8, seed + 1),
                "horizon": 2,
                "timeout_seconds": 30,
            }
        )
    support32 = sampled(32, 32011)
    added.append(
        {
            "name": "sample32_h3_legal40",
            "support": support32,
            "legal": legal_for(support32, 8, 32012),
            "horizon": 3,
            "timeout_seconds": 60,
        }
    )
    return tuple(legacy + added)


def _make_planner(
    layers: Sequence[str], legal: Sequence[str], support: Sequence[str]
) -> Tuple[ExactBayesOptimalPlanner, float]:
    matrix = None
    build_started = time.perf_counter()
    if "matrix_transitions" in layers or "horizon_two_batch" in layers:
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


def _profile_breakdown(profile_path: Optional[Path]) -> Dict[str, Dict[str, float]]:
    if profile_path is None or not profile_path.exists():
        return {}
    stats = pstats.Stats(str(profile_path))
    buckets: Dict[str, Dict[str, float]] = {}

    def add(bucket: str, cc: int, nc: int, internal: float, cumulative: float) -> None:
        row = buckets.setdefault(
            bucket,
            {"calls": 0, "primitive_calls": 0, "internal_seconds": 0.0, "cumulative_seconds": 0.0},
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
        if "_mass_table" in name:
            bucket = "mass_table"
        elif "_canonical_key" in name:
            bucket = "canonical_key"
        elif "_can_use_matrix" in name:
            bucket = "matrix_eligibility"
        elif "_transition_branches" in name:
            bucket = "transition_grouping"
        elif "_posterior_for_branch" in name or "__post_init__" in name:
            bucket = "posterior_construction"
        elif "_best_guess" in name or "_guess_value" in name:
            bucket = "recursion_state_expansion"
        elif name in {"get", "put"} and path.endswith("decision.py"):
            bucket = "cache_handling"
        elif "_ordered_actions" in name or "builtins.sorted" in lowered:
            bucket = "sorting"
        elif "horizon_two_values" in name or "numpy" in path or "numpy.ufunc" in lowered:
            bucket = "numpy_matrix"
        if bucket is not None:
            add(bucket, cc, nc, internal, cumulative)
    return dict(sorted(buckets.items()))


def _wordle_pattern(guess: str, target: str) -> Tuple[int, ...]:
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


def _partition_metrics(
    legal: Sequence[str], support: Sequence[str], feedback_engine: HardleFeedbackEngine
) -> Dict[str, Any]:
    metric_rows: Dict[str, Dict[str, Any]] = {}
    for label, code in (
        ("hardle", lambda guess, target: feedback_engine.evaluate(guess, target)),
        ("wordle_pattern_diagnostic", _wordle_pattern),
    ):
        branch_count_histogram: Dict[str, int] = {}
        branch_size_histogram: Dict[str, int] = {}
        branch_counts = []
        for guess in legal:
            groups: Dict[object, int] = {}
            for target in support:
                outcome = code(guess, target)
                groups[outcome] = groups.get(outcome, 0) + 1
            branch_counts.append(len(groups))
            branch_count_histogram[str(len(groups))] = branch_count_histogram.get(str(len(groups)), 0) + 1
            for size in groups.values():
                branch_size_histogram[str(size)] = branch_size_histogram.get(str(size), 0) + 1
        total_branches = sum(branch_counts)
        mean_branches = total_branches / len(legal)
        mean_child_support = len(legal) * len(support) / total_branches
        metric_rows[label] = {
            "actions": len(legal),
            "support": len(support),
            "mean_branches_per_action": mean_branches,
            "mean_child_support_per_branch": mean_child_support,
            "branch_count_histogram": dict(sorted(branch_count_histogram.items(), key=lambda item: int(item[0]))),
            "branch_size_histogram": dict(sorted(branch_size_histogram.items(), key=lambda item: int(item[0]))),
        }
    metric_rows["diagnostic_hardle_child_support_ratio"] = (
        metric_rows["hardle"]["mean_child_support_per_branch"]
        / metric_rows["wordle_pattern_diagnostic"]["mean_child_support_per_branch"]
    )
    return metric_rows


def _run_worker(
    case: Dict[str, Any], layers: Sequence[str], profile_path: Optional[Path]
) -> Dict[str, Any]:
    support = tuple(case["support"])
    legal = tuple(case["legal"])
    feedback = HardleFeedbackEngine()
    updater = ExactPosteriorUpdater(feedback)
    state = DecisionState(UniformPrior().initial_belief(support), int(case["horizon"]))
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
            pstats.Stats(profile, stream=stream).sort_stats("cumulative").print_stats(30)
    elapsed = time.perf_counter() - started
    instrumentation = planner.instrumentation()
    result: Dict[str, Any] = {
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
        "instrumentation": instrumentation,
        "profile_path": str(profile_path.relative_to(ROOT)) if profile_path else None,
        "profile_breakdown": _profile_breakdown(profile_path),
    }
    if case["name"] == "sample32_h3_legal40" and "horizon_two_batch" in layers:
        result["feedback_fattening_diagnostic"] = _partition_metrics(legal, support, feedback)
    return result


def _run_bounded(
    case: Dict[str, Any], variant: str, layers: Sequence[str], profile: bool = False
) -> Dict[str, Any]:
    profile_path = None
    if profile:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        profile_path = PROFILE_DIR / f"{case['name']}__{variant}.prof"
    payload = json.dumps(
        {"case": case, "layers": list(layers), "profile_path": str(profile_path) if profile_path else None}
    )
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
            "variant": variant,
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
            "variant": variant,
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
            "variant": variant,
            "returncode": completed.returncode,
            "stderr": completed.stderr[-4000:],
            "stdout": completed.stdout[-4000:],
        }
    result["variant"] = variant
    result["driver_elapsed_seconds"] = time.perf_counter() - started
    return result


def _schedule(cases: Sequence[Dict[str, Any]]) -> Tuple[Tuple[Dict[str, Any], str, Tuple[str, ...], bool], ...]:
    by_name = {case["name"]: case for case in cases}
    rows = []
    for name in (
        "fixture5_h3_legal10",
        "sample8_h3_legal16",
        "sample12_h3_legal20",
        "sample20_h3_legal28",
    ):
        for variant, layers in LEGACY_LADDER:
            rows.append((by_name[name], variant, layers, variant in {"baseline_reference", "issue010_full"} and name in {"fixture5_h3_legal10", "sample20_h3_legal28"}))
        rows.append((by_name[name], "horizon_two_scalar", ISSUE010_LAYERS + ("horizon_two_closed_form",), False))
        rows.append((by_name[name], "horizon_two_batch", FULL_LAYERS, name in {"sample20_h3_legal28"}))

    for name in ("curated2315_h1_fulllegal", "curated2315_h2_fulllegal"):
        rows.append((by_name[name], "issue010_full", ISSUE010_LAYERS, False))
        if by_name[name]["horizon"] == 2:
            rows.append((by_name[name], "horizon_two_scalar", ISSUE010_LAYERS + ("horizon_two_closed_form",), False))
            rows.append((by_name[name], "horizon_two_batch", FULL_LAYERS, True))
        else:
            rows.append((by_name[name], "horizon_two_batch", FULL_LAYERS, False))

    for size in (32, 50, 100):
        case = next(case for case in cases if case["name"] == f"sample{size}_h2_legal{size + 8}")
        rows.append((case, "horizon_two_scalar", ISSUE010_LAYERS + ("horizon_two_closed_form",), False))
        rows.append((case, "horizon_two_batch", FULL_LAYERS, False))
    for size in (200, 500):
        case = next(case for case in cases if case["name"] == f"sample{size}_h2_legal{size + 8}")
        rows.append((case, "horizon_two_batch", FULL_LAYERS, False))
    case32h3 = by_name["sample32_h3_legal40"]
    rows.append((case32h3, "issue010_full", ISSUE010_LAYERS, False))
    rows.append((case32h3, "horizon_two_batch", FULL_LAYERS, True))
    return tuple(rows)


def _timing_summary(runs: Sequence[Dict[str, Any]]) -> Tuple[Dict[str, Any], ...]:
    wanted = (
        ("sample20_h3_legal28", "baseline_reference"),
        ("sample20_h3_legal28", "issue010_full"),
        ("sample20_h3_legal28", "horizon_two_scalar"),
        ("sample20_h3_legal28", "horizon_two_batch"),
        ("curated2315_h2_fulllegal", "issue010_full"),
        ("curated2315_h2_fulllegal", "horizon_two_scalar"),
        ("curated2315_h2_fulllegal", "horizon_two_batch"),
    )
    by_key = {(row.get("case"), row.get("variant")): row for row in runs}
    summary = []
    for case, variant in wanted:
        row = by_key.get((case, variant))
        if row is None:
            continue
        summary.append(
            {
                "case": case,
                "variant": variant,
                "status": row.get("status"),
                "total_seconds": row.get("total_seconds", row.get("elapsed_before_timeout")),
                "selection_seconds": row.get("selection_seconds"),
                "matrix_build_seconds": row.get("matrix_build_seconds"),
            }
        )
    return tuple(summary)


def _markdown(artifact: Dict[str, Any]) -> str:
    lines = [
        "# ISSUE-011 exact planner hotspot audit",
        "",
        "The objective and feedback semantics are unchanged. A bounded timeout is an observed limit, not an exact-feasibility claim.",
        "",
        "| Case | Variant | Status | Support | Legal | H | Total s | Selected | Value | States | Actions | Branches | Pruned | Cache H/M | Batch calls/actions | Matrix bytes |",
        "|---|---|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in artifact["runs"]:
        if row.get("status") != "completed":
            lines.append(
                f"| {row.get('case')} | {row.get('variant')} | {row.get('status')} | {row.get('support_size', '-')} | {row.get('legal_size', '-')} | {row.get('horizon', '-')} | {row.get('elapsed_before_timeout', 0):.3f} | - | - | - | - | - | - | - | - | - |"
            )
            continue
        stats = row["instrumentation"]
        lines.append(
            f"| {row['case']} | {row['variant']} | completed | {row['support_size']} | {row['legal_size']} | {row['horizon']} | {row['total_seconds']:.3f} | {row['selected_guess']} | {row['value']} | {stats['states_evaluated']} | {stats['actions_evaluated']} | {stats['branches_evaluated']} | {stats['actions_pruned']} | {stats['cache_hits']}/{stats['cache_misses']} | {stats['horizon_two_batch_calls']}/{stats['horizon_two_batch_actions']} | {stats['matrix_memory_bytes']} |"
        )
    lines.extend(
        [
            "",
            "## Exactness and time movement",
            "",
            "- `horizon_two_closed_form` uses the scalar identity `success(g) = sum_o max(p(w) for legal w in branch o)` and `expected(g) = 2 - p(g)`; the reference-equivalence tests cover deterministic random weighted states.",
            "- `horizon_two_batch` applies the same identity to matrix rows with exact per-code maxima; it is enabled only for the exact Hardle engine and a compatible matrix.",
            "- The current benchmark reports matrix build time separately from planner selection time. Matrix bytes are uint8 feedback-code storage.",
            "",
            "## Per-optimization timing",
            "",
            "| Case | Variant | Status | Total s | Selection s | Matrix build s |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in artifact["optimization_timing"]:
        lines.append(
            f"| {row['case']} | {row['variant']} | {row['status']} | {row['total_seconds']:.3f} | {row['selection_seconds'] if row['selection_seconds'] is not None else '-'} | {row['matrix_build_seconds'] if row['matrix_build_seconds'] is not None else '-'} |"
        )
    lines.extend(
        [
            "",
            "The support-20 horizon-3 comparison isolates the movement from the ISSUE-010 ladder to the scalar horizon-2 formula and then to the matrix batch path. The curated 2,315 horizon-2 rows are the direct practical-frontier comparison; the old recursive path is retained as a bounded timeout.",
            "",
            "## Deferred hypotheses",
            "",
            "- No internal immutable-state rewrite was made: after the horizon-2 shortcut, representative horizon-3 profile time is dominated by exact recursive state expansion and batch calls, while posterior construction is a small fraction of the run.",
            "- No alternative matrix partition was made: the finite-code `np.maximum.at` batch is already the measured dominant NumPy work and completes the full horizon-2 root; Python transition grouping remains only on deeper horizon-3 roots.",
            "- No stronger branch-and-bound bound was made: horizon-2 does not recurse or prune, and the support-32 horizon-3 row already shows exact pruning with reference-equivalent values; a new bound would need a separate adversarial proof and measured gain.",
            "",
            "## Profile breakdown",
            "",
            "| Profile | Bucket | Calls | Primitive calls | Internal s | Cumulative s |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in artifact["runs"]:
        for bucket, values in row.get("profile_breakdown", {}).items():
            lines.append(
                f"| {row['variant']} / {row['case']} | {bucket} | {int(values['calls'])} | {int(values['primitive_calls'])} | {values['internal_seconds']:.6f} | {values['cumulative_seconds']:.6f} |"
            )
    lines.extend(
        [
            "",
            "## Structural diagnostics",
            "",
            "Planner instrumentation contains state-support, feedback-branch, child-support, sorting/grouping, cache, matrix eligibility, and batch-cell counters for every completed row. The Hardle-vs-position-level pattern comparison is diagnostic only and does not define planner semantics.",
            "",
        ]
    )
    for row in artifact["runs"]:
        if row.get("feedback_fattening_diagnostic"):
            lines.append(f"### {row['case']} ({row['variant']})")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(row["feedback_fattening_diagnostic"], indent=2, sort_keys=True))
            lines.append("```")
            lines.append("")
    largest = artifact.get("largest_completed")
    boundary = (
        f"Largest completed row: `{largest['case']}` / `{largest['variant']}` / "
        f"support={largest['support_size']} / horizon={largest['horizon']}`"
        if largest
        else "No completed row."
    )
    lines.extend(["## Boundary", "", boundary, ""])
    return "\n".join(lines)


def run_driver() -> Dict[str, Any]:
    cases = _case_definitions()
    runs = []
    for case, variant, layers, profile in _schedule(cases):
        runs.append(_run_bounded(case, variant, layers, profile))
    completed = [row for row in runs if row.get("status") == "completed"]
    artifact = {
        "format": 1,
        "issue": "ISSUE-011",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": sys.version,
        "platform": sys.platform,
        "issue010_layers": list(ISSUE010_LAYERS),
        "full_layers": list(FULL_LAYERS),
        "cases": list(cases),
        "runs": runs,
        "optimization_timing": list(_timing_summary(runs)),
        "largest_completed": max(
            completed,
            key=lambda row: (row["support_size"], row["horizon"], row["legal_size"]),
            default=None,
        ),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "issue_011_exact_hotspots.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (RESULTS / "issue_011_exact_hotspots_summary.md").write_text(
        _markdown(artifact), encoding="utf-8"
    )
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
    print(
        json.dumps(
            {
                "artifact": str(RESULTS / "issue_011_exact_hotspots.json"),
                "runs": len(artifact["runs"]),
                "completed": len(completed),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
