"""Small exact-safe primitives used by the ISSUE-014 research audit.

The module intentionally does not alter ``ExactBayesOptimalPlanner``.  It
contains the algebra used by the audit and by its regression tests so that a
future planner integration would have a separately checkable semantic oracle.
"""

from __future__ import annotations

import math
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple, Union

import numpy as np


PartitionSignature = Tuple[Tuple[int, ...], ...]
PlannerValue = Tuple[float, float]

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "experiments" / "results"
ISSUE013_ARTIFACT = RESULTS / "issue_013_horizon2_bounds_batch.json"


def canonical_partition_signature(codes: Sequence[int]) -> PartitionSignature:
    """Erase feedback labels and return the canonical partition of positions."""

    blocks: Dict[int, list[int]] = {}
    for position, code in enumerate(codes):
        blocks.setdefault(int(code), []).append(position)
    return tuple(sorted(tuple(block) for block in blocks.values()))


def action_value_from_partition(
    partition: PartitionSignature,
    answer_words: Sequence[str],
    weights: Sequence[float],
    legal_final_answers: Iterable[str],
    first_guess: str,
) -> PlannerValue:
    """Evaluate one H2 action from an unlabeled feedback partition."""

    words = tuple(answer_words)
    values = tuple(float(value) for value in weights)
    if len(words) != len(values) or not words:
        raise ValueError("answer_words and weights must be non-empty and aligned")
    legal_final = set(legal_final_answers)
    success = math.fsum(
        max(
            (values[index] for index in block if words[index] in legal_final),
            default=0.0,
        )
        for block in partition
    )
    immediate_mass = values[words.index(first_guess)] if first_guess in words else 0.0
    return float(success), float(2.0 - immediate_mass)


def safe_action_equivalence_key(
    partition: PartitionSignature,
    first_guess: str,
    answer_words: Sequence[str],
    weights: Sequence[float],
) -> Tuple[PartitionSignature, float]:
    """Key for exact H2 action collapse under the lexicographic objective."""

    words = tuple(answer_words)
    values = tuple(float(value) for value in weights)
    immediate_mass = values[words.index(first_guess)] if first_guess in words else 0.0
    return partition, immediate_mass


def _is_refinement(
    finer: PartitionSignature, coarser: PartitionSignature
) -> bool:
    return all(
        any(set(fine_block).issubset(coarse_block) for coarse_block in coarser)
        for fine_block in finer
    )


def dominance_from_refinement(
    finer: PartitionSignature,
    coarser: PartitionSignature,
    immediate_mass_a: float,
    immediate_mass_b: float,
) -> bool:
    """Return the sufficient exact H2 dominance condition for action A.

    A finer partition cannot lower the sum of per-block maxima.  The
    immediate-hit mass condition separately protects the expected-guesses
    secondary objective.
    """

    return _is_refinement(finer, coarser) and immediate_mass_a >= immediate_mass_b


def posterior_distance(
    first: Mapping[str, float], second: Mapping[str, float]
) -> Dict[str, Union[float, int]]:
    """Return total-variation and added/removed posterior mass diagnostics."""

    words = set(first) | set(second)
    differences = [float(second.get(word, 0.0) - first.get(word, 0.0)) for word in words]
    added_mass = math.fsum(max(0.0, difference) for difference in differences)
    removed_mass = math.fsum(max(0.0, -difference) for difference in differences)
    return {
        "total_variation": 0.5 * math.fsum(abs(difference) for difference in differences),
        "added_mass": added_mass,
        "removed_mass": removed_mass,
        "added_count": sum(
            1 for word in words if word not in first and word in second and second[word] > 0
        ),
        "removed_count": sum(
            1 for word in words if word in first and word not in second and first[word] > 0
        ),
    }


def similarity_action_bounds(
    value: PlannerValue, distance: float
) -> Tuple[PlannerValue, PlannerValue]:
    """Return the TV Lipschitz lower and upper bounds for one fixed action."""

    if distance < 0 or not math.isfinite(distance):
        raise ValueError("distance must be finite and non-negative")
    success, expected = value
    lower = (max(0.0, success - distance), max(1.0, expected - distance))
    upper = (min(1.0, success + distance), min(2.0, expected + distance))
    return lower, upper


def optimal_similarity_bounds(
    solved_values: Mapping[str, PlannerValue], distance: float
) -> Dict[str, object]:
    """Bound the H2 optimum at a nearby posterior from solved action values."""

    if not solved_values:
        raise ValueError("solved_values cannot be empty")
    if distance < 0 or not math.isfinite(distance):
        raise ValueError("distance must be finite and non-negative")
    best_success = max(value[0] for value in solved_values.values())
    candidate_actions = tuple(
        guess
        for guess, value in solved_values.items()
        if value[0] >= best_success - 2.0 * distance
    )
    lower_expected = max(
        1.0,
        min(solved_values[guess][1] for guess in candidate_actions) - distance,
    )
    upper_expected = min(
        2.0,
        max(solved_values[guess][1] for guess in candidate_actions) + distance,
    )
    return {
        "success_lower": max(0.0, best_success - distance),
        "success_upper": min(1.0, best_success + distance),
        "expected_lower": lower_expected,
        "expected_upper": upper_expected,
        "candidate_actions": candidate_actions,
    }


def _partition_refines(
    finer: PartitionSignature, coarser: PartitionSignature
) -> bool:
    """Internal partition relation used by the bounded dominance audit."""

    return all(
        any(set(block).issubset(other) for other in coarser)
        for block in finer
    )


def _feedback_code(feedback: Sequence[int], word_length: int = 5) -> int:
    return int(feedback[0]) * (word_length + 1) + int(feedback[1])


def _state_digest(words: Sequence[str]) -> str:
    return hashlib.sha256("\n".join(words).encode("utf-8")).hexdigest()[:16]


def _load_issue013_artifact() -> Dict[str, object]:
    return json.loads(ISSUE013_ARTIFACT.read_text(encoding="utf-8"))


def _case_map(artifact: Mapping[str, object]) -> Dict[str, Dict[str, object]]:
    return {str(case["name"]): case for case in artifact["cases"]}


def _control_run_map(artifact: Mapping[str, object]) -> Dict[str, Dict[str, object]]:
    rows = {}
    for row in artifact["runs"]:
        if row.get("variant") == "issue012_control":
            rows[str(row["case"])] = row
    return rows


def _child_state(
    words: Sequence[str], source: str, root_guess: str, feedback: Sequence[int]
) -> Dict[str, object]:
    ordered = tuple(words)
    return {
        "words": ordered,
        "weights": tuple(1.0 / len(ordered) for _ in ordered),
        "source": source,
        "root_guess": root_guess,
        "feedback": tuple(int(value) for value in feedback),
        "state_digest": _state_digest(ordered),
    }


def _recorded_child_states(
    matrix: object,
    support: Sequence[str],
    records: Sequence[Mapping[str, object]],
    source: str,
) -> list[Dict[str, object]]:
    """Reconstruct child supports from ISSUE-013 root-audit records."""

    answer_indices = matrix.answer_indices(support)
    states = []
    for record in records:
        guess = str(record["guess"])
        row = matrix.row_for(guess)[answer_indices]
        for branch in record["branches"]:
            feedback = tuple(int(value) for value in branch["feedback"])
            if feedback == (matrix.word_length, 0):
                continue
            code = _feedback_code(feedback, matrix.word_length)
            words = tuple(
                word for word, observed in zip(support, row) if int(observed) == code
            )
            if not words:
                continue
            expected_support = int(branch["support_size"])
            if expected_support != len(words):
                raise AssertionError(
                    f"recorded branch support mismatch for {guess}/{feedback}: "
                    f"{expected_support} != {len(words)}"
                )
            states.append(_child_state(words, source, guess, feedback))
    return states


def _bounded_child_states(
    matrix: object, support: Sequence[str], legal: Sequence[str], root_limit: int = 8
) -> list[Dict[str, object]]:
    """Collect a bounded curated frontier without running the full H3 planner."""

    answer_indices = matrix.answer_indices(support)
    states = []
    for guess in tuple(legal)[:root_limit]:
        row = matrix.row_for(guess)[answer_indices]
        seen_codes = set()
        for code in row:
            code = int(code)
            if code in seen_codes or code == _feedback_code((matrix.word_length, 0), matrix.word_length):
                continue
            seen_codes.add(code)
            words = tuple(
                word for word, observed in zip(support, row) if int(observed) == code
            )
            feedback = matrix.decode_code(code)
            if words:
                states.append(
                    _child_state(words, "curated_bounded_frontier", guess, feedback)
                )
    return states


def _unique_states(states: Sequence[Mapping[str, object]]) -> list[Dict[str, object]]:
    unique: list[Dict[str, object]] = []
    seen = set()
    for state in states:
        words = tuple(state["words"])
        if words in seen:
            continue
        seen.add(words)
        unique.append(dict(state))
    return unique


def _sample_states(
    states: Sequence[Mapping[str, object]], limit: int
) -> list[Dict[str, object]]:
    if not states:
        return []
    if len(states) <= limit:
        return [dict(state) for state in states]
    indices = sorted(
        {
            int(round(index * (len(states) - 1) / max(1, limit - 1)))
            for index in range(limit)
        }
    )
    return [dict(states[index]) for index in indices]


def collapsed_h2_values(
    matrix: object,
    legal: Sequence[str],
    answer_words: Sequence[str],
    weights: Sequence[float],
    legal_final_answers: Sequence[str],
) -> Tuple[PlannerValue, ...]:
    """Evaluate one representative per exact-safe H2 action class."""

    words = tuple(answer_words)
    values = tuple(float(value) for value in weights)
    answer_indices = matrix.answer_indices(words)
    codes = matrix.matrix[:, answer_indices]
    immediate = {word: weight for word, weight in zip(words, values)}
    representatives: Dict[Tuple[PartitionSignature, float], int] = {}
    for index, guess in enumerate(legal):
        key = (canonical_partition_signature(codes[index].tolist()), immediate.get(guess, 0.0))
        representatives.setdefault(key, index)
    representative_indices = tuple(representatives.values())
    representative_values = matrix.horizon_two_values(
        tuple(legal[index] for index in representative_indices),
        words,
        values,
        legal_final_answers,
    )
    by_index = dict(zip(representative_indices, representative_values))
    return tuple(
        by_index[representatives[
            (canonical_partition_signature(codes[index].tolist()), immediate.get(guess, 0.0))
        ]]
        for index, guess in enumerate(legal)
    )


def _partition_audit(
    matrix: object,
    legal: Sequence[str],
    state: Mapping[str, object],
) -> Dict[str, object]:
    words = tuple(state["words"])
    weights = tuple(state["weights"])
    answer_indices = matrix.answer_indices(words)
    codes = matrix.matrix[:, answer_indices]
    values = matrix.horizon_two_values(legal, words, weights, legal)
    by_signature: Dict[PartitionSignature, list[int]] = {}
    raw_rows = set()
    for index, row in enumerate(codes):
        raw_rows.add(row.tobytes())
        signature = canonical_partition_signature(row.tolist())
        by_signature.setdefault(signature, []).append(index)

    immediate_mass = {
        word: weight for word, weight in zip(words, weights)
    }
    safe_groups: Dict[Tuple[PartitionSignature, float], list[int]] = {}
    for index, guess in enumerate(legal):
        key = (canonical_partition_signature(codes[index].tolist()), immediate_mass.get(guess, 0.0))
        safe_groups.setdefault(key, []).append(index)

    class_sizes = [len(indices) for indices in by_signature.values()]
    safe_sizes = [len(indices) for indices in safe_groups.values()]
    classes_with_candidate = 0
    probe_only_classes = 0
    mixed_classes = 0
    nonconstant_success = 0
    nonconstant_expected = 0
    expected_spreads = []
    success_spreads = []
    for indices in by_signature.values():
        candidate_count = sum(legal[index] in immediate_mass for index in indices)
        if candidate_count:
            classes_with_candidate += 1
        else:
            probe_only_classes += 1
        if candidate_count and candidate_count < len(indices):
            mixed_classes += 1
        class_values = [values[index] for index in indices]
        success_spread = max(value[0] for value in class_values) - min(
            value[0] for value in class_values
        )
        expected_spread = max(value[1] for value in class_values) - min(
            value[1] for value in class_values
        )
        success_spreads.append(success_spread)
        expected_spreads.append(expected_spread)
        if success_spread > 1e-12:
            nonconstant_success += 1
        if expected_spread > 1e-12:
            nonconstant_expected += 1

    safe_action_count = len(safe_groups)
    safe_values = []
    for indices in safe_groups.values():
        safe_values.extend(values[index] for index in indices)
    best_index = max(
        range(len(legal)),
        key=lambda index: (values[index][0], -values[index][1], -index),
    )
    return {
        "state_digest": state["state_digest"],
        "root_guess": state["root_guess"],
        "feedback": list(state["feedback"]),
        "support_size": len(words),
        "legal_guess_count": len(legal),
        "distinct_raw_feedback_code_rows": len(raw_rows),
        "distinct_unlabeled_partition_signatures": len(by_signature),
        "partition_class_size_distribution": dict(
            sorted((str(size), class_sizes.count(size)) for size in set(class_sizes))
        ),
        "safe_action_equivalence_class_count": safe_action_count,
        "safe_collapsible_action_count": len(legal) - safe_action_count,
        "safe_collapse_fraction": (len(legal) - safe_action_count) / len(legal),
        "safe_action_class_size_distribution": dict(
            sorted((str(size), safe_sizes.count(size)) for size in set(safe_sizes))
        ),
        "classes_containing_remaining_candidate": classes_with_candidate,
        "classes_probe_only": probe_only_classes,
        "classes_mixing_candidate_and_probe": mixed_classes,
        "classes_with_nonconstant_success_value": nonconstant_success,
        "classes_with_nonconstant_expected_value": nonconstant_expected,
        "max_success_spread_within_partition_class": max(success_spreads, default=0.0),
        "max_expected_spread_within_partition_class": max(expected_spreads, default=0.0),
        "max_success_spread_within_safe_class": max(
            (
                max(values[index][0] for index in indices)
                - min(values[index][0] for index in indices)
                for indices in safe_groups.values()
            ),
            default=0.0,
        ),
        "max_expected_spread_within_safe_class": max(
            (
                max(values[index][1] for index in indices)
                - min(values[index][1] for index in indices)
                for indices in safe_groups.values()
            ),
            default=0.0,
        ),
        "h2_cells_before_safe_collapse": len(legal) * len(words),
        "h2_cells_after_safe_collapse": safe_action_count * len(words),
        "best_guess": legal[best_index],
        "best_value": list(values[best_index]),
    }


def _dominance_audit(
    matrix: object,
    legal: Sequence[str],
    state: Mapping[str, object],
    max_actions: int = 512,
) -> Dict[str, object]:
    words = tuple(state["words"])
    weights = tuple(state["weights"])
    answer_indices = matrix.answer_indices(words)
    codes = matrix.matrix[:, answer_indices]
    signatures = [canonical_partition_signature(row.tolist()) for row in codes]
    values = matrix.horizon_two_values(legal, words, weights, legal)
    immediate = {word: weight for word, weight in zip(words, weights)}
    if len(legal) <= max_actions:
        left_indices = tuple(range(len(legal)))
        right_indices = left_indices
        mode = "exhaustive"
    else:
        left_indices = tuple(
            sorted(
                {
                    int(round(index * (len(legal) - 1) / max(1, max_actions - 1)))
                    for index in range(max_actions)
                }
            )
        )
        right_indices = left_indices
        mode = "bounded_deterministic_sample"

    examined = 0
    candidate_pairs = 0
    violations = 0
    strict_pairs = 0
    dominated = set()
    for left in left_indices:
        for right in right_indices:
            if left == right:
                continue
            examined += 1
            mass_left = immediate.get(legal[left], 0.0)
            mass_right = immediate.get(legal[right], 0.0)
            if not _partition_refines(signatures[left], signatures[right]):
                continue
            if mass_left + 1e-15 < mass_right:
                continue
            candidate_pairs += 1
            left_value = values[left]
            right_value = values[right]
            if left_value[0] + 1e-12 < right_value[0] or (
                abs(left_value[0] - right_value[0]) <= 1e-12
                and left_value[1] > right_value[1] + 1e-12
            ):
                violations += 1
                continue
            strictly_better = left_value[0] > right_value[0] + 1e-12 or (
                abs(left_value[0] - right_value[0]) <= 1e-12
                and left_value[1] < right_value[1] - 1e-12
            )
            if strictly_better:
                strict_pairs += 1
                dominated.add(right)
    return {
        "state_digest": state["state_digest"],
        "support_size": len(words),
        "legal_guess_count": len(legal),
        "pair_audit_mode": mode,
        "pairs_examined": examined,
        "refinement_and_immediate_mass_candidate_pairs": candidate_pairs,
        "rule_violations": violations,
        "strictly_dominating_pairs": strict_pairs,
        "actions_with_strict_dominator": len(dominated),
        "dominance_rule_status": "safe_on_examined_pairs" if violations == 0 else "counterexample_found",
    }


def _best_value(values: Mapping[str, PlannerValue]) -> PlannerValue:
    best_success = max(value[0] for value in values.values())
    best_expected = min(
        value[1]
        for value in values.values()
        if abs(value[0] - best_success) <= 1e-12
    )
    return best_success, best_expected


def _cannot_beat(
    upper_success: float, lower_expected: float, incumbent: PlannerValue
) -> bool:
    if upper_success < incumbent[0] - 1e-12:
        return True
    return (
        abs(upper_success - incumbent[0]) <= 1e-12
        and lower_expected > incumbent[1] + 1e-12
    )


def _better(candidate: PlannerValue, incumbent: PlannerValue) -> bool:
    if candidate[0] > incumbent[0] + 1e-12:
        return True
    if abs(candidate[0] - incumbent[0]) > 1e-12:
        return False
    return candidate[1] < incumbent[1] - 1e-12


def _similarity_audit(
    matrix: object,
    legal: Sequence[str],
    states: Sequence[Mapping[str, object]],
    limit: int = 24,
) -> Dict[str, object]:
    sampled = _sample_states(states, limit)
    state_values: list[Dict[str, PlannerValue]] = []
    state_posteriors = []
    for state in sampled:
        words = tuple(state["words"])
        weights = tuple(state["weights"])
        values = matrix.horizon_two_values(legal, words, weights, legal)
        state_values.append(dict(zip(legal, values)))
        state_posteriors.append(dict(zip(words, weights)))

    distances = []
    bound_rows = []
    total_skips = 0
    total_actions = 0
    duplicate_neighbors = 0
    for index in range(1, len(sampled)):
        target_posterior = state_posteriors[index]
        candidates = []
        for prior in range(index):
            distance = posterior_distance(
                state_posteriors[prior], target_posterior
            )["total_variation"]
            candidates.append((float(distance), prior))
        distance, neighbor_index = min(candidates, key=lambda item: (item[0], item[1]))
        if distance <= 1e-15:
            duplicate_neighbors += 1
        distances.append(distance)
        bounds = optimal_similarity_bounds(state_values[neighbor_index], distance)
        target_best = _best_value(state_values[index])
        total_actions += len(legal)
        incumbent = None
        skipped = 0
        evaluated = 0
        for guess in legal:
            neighbor_value = state_values[neighbor_index][guess]
            _, upper = similarity_action_bounds(neighbor_value, distance)
            if incumbent is not None and _cannot_beat(
                upper[0], max(1.0, neighbor_value[1] - distance), incumbent
            ):
                skipped += 1
                continue
            evaluated += 1
            target_value = state_values[index][guess]
            if incumbent is None or _better(target_value, incumbent):
                incumbent = target_value
        if incumbent is None:
            raise AssertionError("similarity simulation evaluated no action")
        total_skips += skipped
        bound_rows.append(
            {
                "target_state_digest": sampled[index]["state_digest"],
                "neighbor_state_digest": sampled[neighbor_index]["state_digest"],
                "distance_total_variation": distance,
                "distance_added_mass": posterior_distance(
                    state_posteriors[neighbor_index], target_posterior
                )["added_mass"],
                "distance_removed_mass": posterior_distance(
                    state_posteriors[neighbor_index], target_posterior
                )["removed_mass"],
                "target_best_value": list(target_best),
                "success_lower": bounds["success_lower"],
                "success_upper": bounds["success_upper"],
                "expected_lower": bounds["expected_lower"],
                "expected_upper": bounds["expected_upper"],
                "success_lower_gap": target_best[0] - bounds["success_lower"],
                "success_upper_gap": bounds["success_upper"] - target_best[0],
                "expected_lower_gap": target_best[1] - bounds["expected_lower"],
                "expected_upper_gap": bounds["expected_upper"] - target_best[1],
                "strict_action_skips": skipped,
                "actions_evaluated_with_bound": evaluated,
                "bound_skip_preserved_exact_best": (
                    abs(incumbent[0] - target_best[0]) <= 1e-12
                    and abs(incumbent[1] - target_best[1]) <= 1e-12
                ),
            }
        )
    return {
        "sampled_state_count": len(sampled),
        "nearest_neighbor_count": len(distances),
        "nearest_neighbor_distance_min": min(distances, default=None),
        "nearest_neighbor_distance_mean": (
            statistics.fmean(distances) if distances else None
        ),
        "nearest_neighbor_distance_median": (
            statistics.median(distances) if distances else None
        ),
        "nearest_neighbor_distance_max": max(distances, default=None),
        "exact_duplicate_neighbor_count": duplicate_neighbors,
        "strict_action_skips": total_skips,
        "action_attempts": total_actions,
        "strict_action_skip_ratio": total_skips / total_actions if total_actions else 0.0,
        "bound_rows": bound_rows,
        "max_success_lower_gap": max(
            (row["success_lower_gap"] for row in bound_rows), default=0.0
        ),
        "max_success_upper_gap": max(
            (row["success_upper_gap"] for row in bound_rows), default=0.0
        ),
        "max_expected_lower_gap": max(
            (row["expected_lower_gap"] for row in bound_rows), default=0.0
        ),
        "max_expected_upper_gap": max(
            (row["expected_upper_gap"] for row in bound_rows), default=0.0
        ),
        "all_bound_simulations_preserved_exact_best": all(
            row["bound_skip_preserved_exact_best"] for row in bound_rows
        ),
    }


def _run_case(
    case: Mapping[str, object],
    control_row: Optional[Mapping[str, object]],
    partition_state_limit: int,
    similarity_state_limit: int,
) -> Dict[str, object]:
    from bayesian_hardle.accelerated import ExactFeedbackCodeMatrix

    support = tuple(case["support"])
    legal = tuple(case["legal"])
    started = time.perf_counter()
    matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, support)
    matrix_seconds = time.perf_counter() - started
    if control_row is not None and control_row.get("status") == "completed":
        records = control_row["instrumentation"]["root_action_records"]
        states = _recorded_child_states(
            matrix, support, records, "issue013_recorded_h3_child"
        )
        frontier_status = "recorded_completed_h3_run"
    else:
        states = _bounded_child_states(matrix, support, legal)
        frontier_status = "curated_bounded_frontier_only"
    unique = _unique_states(states)
    partition_states = _sample_states(unique, partition_state_limit)
    partition_reports = [
        _partition_audit(matrix, legal, state) for state in partition_states
    ]
    dominance_reports = [
        _dominance_audit(matrix, legal, state) for state in partition_states
    ]
    similarity = _similarity_audit(
        matrix, legal, unique, limit=similarity_state_limit
    )
    before_cells = sum(
        int(report["h2_cells_before_safe_collapse"])
        for report in partition_reports
    )
    after_cells = sum(
        int(report["h2_cells_after_safe_collapse"])
        for report in partition_reports
    )
    dominance_before_cells = sum(
        report["support_size"] * report["legal_guess_count"]
        for report in dominance_reports
        if report["support_size"] > 2
    )
    dominance_after_cells = sum(
        report["support_size"]
        * (
            report["legal_guess_count"]
            - report["actions_with_strict_dominator"]
        )
        for report in dominance_reports
        if report["support_size"] > 2
    )
    benchmark_state_index = max(
        range(len(partition_states)),
        key=lambda index: len(partition_states[index]["words"]),
        default=None,
    )
    collapse_benchmark = None
    if benchmark_state_index is not None:
        benchmark_state = partition_states[benchmark_state_index]
        benchmark_words = tuple(benchmark_state["words"])
        benchmark_weights = tuple(benchmark_state["weights"])
        baseline_started = time.perf_counter()
        baseline_values = matrix.horizon_two_values(
            legal, benchmark_words, benchmark_weights, legal
        )
        baseline_seconds = time.perf_counter() - baseline_started
        collapsed_started = time.perf_counter()
        collapsed_values = collapsed_h2_values(
            matrix, legal, benchmark_words, benchmark_weights, legal
        )
        collapsed_seconds = time.perf_counter() - collapsed_started
        if any(
            abs(actual[0] - expected[0]) > 1e-12
            or abs(actual[1] - expected[1]) > 1e-12
            for actual, expected in zip(collapsed_values, baseline_values)
        ):
            raise AssertionError("collapsed H2 benchmark changed an exact value")
        collapse_benchmark = {
            "state_digest": benchmark_state["state_digest"],
            "support_size": len(benchmark_words),
            "legal_guess_count": len(legal),
            "baseline_seconds": baseline_seconds,
            "collapsed_seconds": collapsed_seconds,
            "collapsed_over_baseline": (
                collapsed_seconds / baseline_seconds
                if baseline_seconds
                else None
            ),
        }
    return {
        "case": case["name"],
        "support_size": len(support),
        "legal_guess_count": len(legal),
        "matrix_memory_bytes": matrix.memory_bytes,
        "matrix_build_seconds": matrix_seconds,
        "frontier_status": frontier_status,
        "recorded_child_state_requests": len(states),
        "distinct_child_state_count": len(unique),
        "partition_audit_state_count": len(partition_reports),
        "partition_audit": partition_reports,
        "dominance_audit": dominance_reports,
        "similarity_audit": similarity,
        "collapse_benchmark": collapse_benchmark,
        "safe_collapse_aggregate": {
            "sampled_h2_cells_before": before_cells,
            "sampled_h2_cells_after": after_cells,
            "sampled_h2_cell_reduction_fraction": (
                (before_cells - after_cells) / before_cells if before_cells else 0.0
            ),
            "max_safe_collapse_fraction": max(
                (report["safe_collapse_fraction"] for report in partition_reports),
                default=0.0,
            ),
        },
        "dominance_aggregate": {
            "sampled_h2_cells_before": dominance_before_cells,
            "sampled_h2_cells_after": dominance_after_cells,
            "sampled_h2_cell_reduction_fraction": (
                (dominance_before_cells - dominance_after_cells) / dominance_before_cells
                if dominance_before_cells
                else 0.0
            ),
        },
    }


def _markdown(artifact: Mapping[str, object]) -> str:
    lines = [
        "# ISSUE-014 H2 action-space structure and similarity-bound audit",
        "",
        "This is a research-first audit. It measures exact unlabeled partition equivalence, tests the immediate-hit caveat, checks a refinement-plus-immediate-mass dominance condition, and measures total-variation bounds from previously solved H2 child states. No planner optimization is enabled by this artifact.",
        "",
        "## Decision",
        "",
        f"- Partition collapse useful: `{artifact['decision']['partition_collapse_useful']}`.",
        f"- Dominance rule useful: `{artifact['decision']['dominance_useful']}`; proof/test status: `{artifact['decision']['dominance_rule_status']}`.",
        f"- Similarity bounds useful: `{artifact['decision']['similarity_useful']}`.",
        f"- Integration status: `{artifact['decision']['integration_status']}`.",
        "",
        "## Per-case measurements",
        "",
        "| Case | Frontier | Support | Legal | Child requests | Unique children | Audit states | Raw rows range | Unlabeled classes range | Safe collapse range | Similarity NN mean d | Similarity strict skips |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for case in artifact["cases"]:
        reports = case["partition_audit"]
        raw_values = [report["distinct_raw_feedback_code_rows"] for report in reports]
        partition_values = [
            report["distinct_unlabeled_partition_signatures"] for report in reports
        ]
        collapse_values = [report["safe_collapse_fraction"] for report in reports]
        similarity = case["similarity_audit"]
        lines.append(
            "| {case} | {frontier} | {support} | {legal} | {requests} | {unique} | {states} | {raw_min}-{raw_max} | {part_min}-{part_max} | {collapse_min:.3f}-{collapse_max:.3f} | {distance} | {skips} |".format(
                case=case["case"],
                frontier=case["frontier_status"],
                support=case["support_size"],
                legal=case["legal_guess_count"],
                requests=case["recorded_child_state_requests"],
                unique=case["distinct_child_state_count"],
                states=case["partition_audit_state_count"],
                raw_min=min(raw_values, default=0),
                raw_max=max(raw_values, default=0),
                part_min=min(partition_values, default=0),
                part_max=max(partition_values, default=0),
                collapse_min=min(collapse_values, default=0.0),
                collapse_max=max(collapse_values, default=0.0),
                distance=(
                    f"{similarity['nearest_neighbor_distance_mean']:.4f}"
                    if similarity["nearest_neighbor_distance_mean"] is not None
                    else "n/a"
                ),
                skips=similarity["strict_action_skips"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A partition class is not automatically an action-equivalence class: if one member is a remaining answer candidate and another is probe-only, their expected-guesses components differ by the candidate's posterior mass even when their future partition is identical. The safe collapse key therefore includes both the unlabeled partition and immediate-hit mass.",
            "",
            "The dominance condition tested here is exact but only sufficient: if action A's partition refines action B's partition and A's immediate-hit mass is at least B's, then the sum of per-block maxima cannot decrease and the expected-guesses component cannot increase. A zero violation count on the audited pairs is evidence for the implementation of this rule, while the mathematical argument is recorded in the research note.",
            "",
            "The similarity bound uses total variation `d = 1/2 ||p-q||_1`. Every fixed H2 action's success probability and expected-guesses component move by at most `d`; the optimal success lies in `[F*(p)-d, F*(p)+d]`. The expected component is bounded using actions within `2d` of the solved state's best success. The artifact reports bound gaps and strict skip counts separately, because a valid but loose bound is not a useful planner optimization.",
            "",
            "Timeouts and bounded curated-frontier extraction are coverage boundaries, not feasibility or acceptance claims.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_artifact(artifact: Mapping[str, object]) -> None:
    """Validate the machine-readable research evidence and invariants."""

    if artifact.get("issue") != "ISSUE-014":
        raise ValueError("unexpected artifact issue")
    cases = artifact.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("artifact must contain case reports")
    for case in cases:
        partition_reports = case.get("partition_audit")
        dominance_reports = case.get("dominance_audit")
        if not isinstance(partition_reports, list) or not partition_reports:
            raise ValueError(f"missing partition audit: {case.get('case')}")
        if len(partition_reports) != len(dominance_reports):
            raise ValueError(f"audit length mismatch: {case.get('case')}")
        for report in partition_reports:
            if report["safe_collapsible_action_count"] < 0:
                raise ValueError("negative safe collapse count")
            if report["max_success_spread_within_safe_class"] > 1e-12:
                raise ValueError("safe collapse changed success value")
            if report["max_expected_spread_within_safe_class"] > 1e-12:
                raise ValueError("safe collapse changed expected value")
        for report in dominance_reports:
            if report["rule_violations"]:
                raise ValueError("dominance rule violation in artifact")
        similarity = case["similarity_audit"]
        if not similarity["all_bound_simulations_preserved_exact_best"]:
            raise ValueError("similarity simulation changed exact optimum")



def run_audit(
    partition_state_limit: int = 6, similarity_state_limit: int = 24
) -> Dict[str, object]:
    artifact013 = _load_issue013_artifact()
    cases = _case_map(artifact013)
    control_rows = _control_run_map(artifact013)
    ordered_names = [
        "sample100_h3_legal108",
        "sample200_h3_legal208",
        "sample500_h3_legal508",
        "sample750_h3_legal758",
        "sample1000_h3_legal1008",
        "curated2315_h3_fulllegal",
    ]
    case_reports = []
    for name in ordered_names:
        case_reports.append(
            _run_case(
                cases[name],
                control_rows.get(name),
                partition_state_limit,
                similarity_state_limit,
            )
        )

    partition_reports = [
        report for case in case_reports for report in case["partition_audit"]
    ]
    dominance_reports = [
        report for case in case_reports for report in case["dominance_audit"]
    ]
    similarity_reports = [case["similarity_audit"] for case in case_reports]
    partition_before_cells = sum(
        case["safe_collapse_aggregate"]["sampled_h2_cells_before"]
        for case in case_reports
    )
    partition_after_cells = sum(
        case["safe_collapse_aggregate"]["sampled_h2_cells_after"]
        for case in case_reports
    )
    partition_fraction = (
        (partition_before_cells - partition_after_cells) / partition_before_cells
        if partition_before_cells
        else 0.0
    )
    dominance_before_cells = sum(
        case["dominance_aggregate"]["sampled_h2_cells_before"]
        for case in case_reports
    )
    dominance_after_cells = sum(
        case["dominance_aggregate"]["sampled_h2_cells_after"]
        for case in case_reports
    )
    dominance_fraction = (
        (dominance_before_cells - dominance_after_cells) / dominance_before_cells
        if dominance_before_cells
        else 0.0
    )
    strict_skips = sum(report["strict_action_skips"] for report in similarity_reports)
    action_attempts = sum(report["action_attempts"] for report in similarity_reports)
    dominance_status = (
        "safe_on_examined_pairs"
        if all(report["rule_violations"] == 0 for report in dominance_reports)
        else "counterexample_found"
    )
    high_support_similarity = [
        case["similarity_audit"]
        for case in case_reports
        if case["support_size"] >= 500 and case["frontier_status"] == "recorded_completed_h3_run"
    ]
    high_support_skips = sum(
        report["strict_action_skips"] for report in high_support_similarity
    )
    high_support_attempts = sum(
        report["action_attempts"] for report in high_support_similarity
    )
    high_support_similarity_ratio = (
        high_support_skips / high_support_attempts if high_support_attempts else 0.0
    )
    collapse_benchmarks = [
        case["collapse_benchmark"]
        for case in case_reports
        if case["collapse_benchmark"] is not None
    ]
    collapse_benchmark_slow = any(
        benchmark["collapsed_over_baseline"] > 1.0
        for benchmark in collapse_benchmarks
    )
    decision = {
        "partition_collapse_useful": (
            partition_fraction >= 0.10 and not collapse_benchmark_slow
        ),
        "partition_mean_safe_collapse_fraction": partition_fraction,
        "partition_sampled_h2_cells_before": partition_before_cells,
        "partition_sampled_h2_cells_after": partition_after_cells,
        "partition_benchmark_any_slow": collapse_benchmark_slow,
        "dominance_rule_status": dominance_status,
        "dominance_useful": dominance_fraction >= 0.10,
        "dominance_sampled_h2_cell_reduction_fraction": dominance_fraction,
        "similarity_useful": (
            high_support_similarity_ratio >= 0.01
            and all(
                report["nearest_neighbor_distance_mean"] is not None
                and report["nearest_neighbor_distance_mean"] <= 0.5
                for report in high_support_similarity
            )
            if high_support_similarity
            else False
        ),
        "similarity_strict_skip_ratio": strict_skips / action_attempts if action_attempts else 0.0,
        "similarity_high_support_ladder_skip_ratio": high_support_similarity_ratio,
        "integration_status": "no planner integration; research audit only",
    }
    artifact = {
        "format": 1,
        "issue": "ISSUE-014",
        "base_commit": "b50f3ba541327264e86b63137c3f37896b576dc8",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "partition_state_limit": partition_state_limit,
        "similarity_state_limit": similarity_state_limit,
        "cases": case_reports,
        "decision": decision,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "issue_014_h2_action_similarity.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (RESULTS / "issue_014_h2_action_similarity_summary.md").write_text(
        _markdown(artifact), encoding="utf-8"
    )
    return artifact


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--partition-states", type=int, default=6)
    parser.add_argument("--similarity-states", type=int, default=24)
    parser.add_argument("--validate", type=Path)
    args = parser.parse_args()
    if args.validate:
        payload = json.loads(args.validate.read_text(encoding="utf-8"))
        validate_artifact(payload)
        print(json.dumps({"validated": str(args.validate)}))
        return
    artifact = run_audit(args.partition_states, args.similarity_states)
    print(
        json.dumps(
            {
                "artifact": str(RESULTS / "issue_014_h2_action_similarity.json"),
                "summary": str(RESULTS / "issue_014_h2_action_similarity_summary.md"),
                "cases": len(artifact["cases"]),
                "decision": artifact["decision"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
