"""Baseline policies and exact finite-horizon Bayes planning."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import random
import time
from typing import Any, Dict, Hashable, Optional, Protocol, Sequence, Tuple, runtime_checkable

from .belief import BeliefState, PosteriorUpdater
from .accelerated import ExactFeedbackCodeMatrix, MatrixInformationGainCalculator
from .game import Feedback, FeedbackEngine, HardleFeedbackEngine
from .information import (
    ExactInformationGainCalculator,
    ExactOutcomePartitioner,
    InformationGainCalculator,
    OutcomePartitioner,
)


POLICY_TIE_TOLERANCE = 1e-12
"""Absolute tolerance for policy-value ties, applied only to tie resolution."""

PlannerValue = Tuple[float, float]


@dataclass(frozen=True)
class DecisionState:
    """Belief plus the remaining decision horizon."""

    belief: BeliefState
    remaining_guesses: int

    def __post_init__(self) -> None:
        if self.remaining_guesses < 0:
            raise ValueError("remaining_guesses cannot be negative")


@runtime_checkable
class Policy(Protocol):
    """Selects a guess from legal guesses supplied by the game model."""

    def select_guess(
        self,
        state: DecisionState,
        candidate_guesses: Sequence[str],
    ) -> str:
        ...


class PolicyBudgetExceeded(RuntimeError):
    """A bounded experiment stopped before a policy could finish selection."""


class RandomPolicy:
    """Uniform random legal-guess baseline with injectable randomness."""

    def __init__(self, rng: Optional[random.Random] = None, seed: Optional[int] = None) -> None:
        if rng is not None and seed is not None:
            raise ValueError("provide rng or seed, not both")
        self.rng = rng or random.Random(seed)

    def select_guess(self, state: DecisionState, candidate_guesses: Sequence[str]) -> str:
        del state
        if not candidate_guesses:
            raise ValueError("candidate_guesses cannot be empty")
        return self.rng.choice(tuple(candidate_guesses))


class MAPPolicy:
    """Chooses the legal candidate answer with maximum posterior mass."""

    def select_guess(self, state: DecisionState, candidate_guesses: Sequence[str]) -> str:
        legal = tuple(candidate_guesses)
        if not legal:
            raise ValueError("candidate_guesses cannot be empty")
        mass = dict(state.belief.probability_mass)
        if not mass:
            uniform = 1.0 / len(state.belief.candidates)
            mass = {word: uniform for word in state.belief.candidates}
        eligible = [(guess, mass[guess]) for guess in legal if guess in mass]
        if not eligible:
            raise ValueError("candidate_guesses contain no remaining answer candidate")
        return max(eligible, key=lambda item: item[1])[0]


class MaxInformationGainPolicy:
    """Chooses maximum exact IG with a scalar reference and exact fast path."""

    def __init__(
        self,
        feedback_engine: FeedbackEngine,
        partitioner: Optional[OutcomePartitioner] = None,
        information_gain_calculator: Optional[InformationGainCalculator] = None,
        time_limit_seconds: Optional[float] = None,
        use_acceleration: bool = True,
        feedback_matrix: Optional[ExactFeedbackCodeMatrix] = None,
    ) -> None:
        if time_limit_seconds is not None and time_limit_seconds <= 0:
            raise ValueError("time_limit_seconds must be positive")
        self.feedback_engine = feedback_engine
        self.partitioner = partitioner or ExactOutcomePartitioner()
        self.information_gain_calculator = (
            information_gain_calculator or ExactInformationGainCalculator()
        )
        self.time_limit_seconds = time_limit_seconds
        self.use_acceleration = use_acceleration
        self.feedback_matrix = feedback_matrix
        self._matrix_cache: Dict[Hashable, ExactFeedbackCodeMatrix] = {}
        if feedback_matrix is not None:
            self._matrix_cache[
                (feedback_matrix.legal_guesses, feedback_matrix.candidate_answers)
            ] = feedback_matrix
        self._decision_cache: Dict[Hashable, str] = {}
        self.decision_cache_hits = 0
        self.decision_cache_misses = 0
        self._started_at = None
        self.evaluated_guesses = 0

    @staticmethod
    def _belief_cache_key(state: DecisionState, legal: Tuple[str, ...]) -> Hashable:
        if state.belief.probability_mass:
            total = state.belief.total_mass
            if total <= 0:
                raise ValueError("belief must have positive total mass")
            mass = tuple(
                sorted(
                    (word, float(value / total))
                    for word, value in state.belief.probability_mass
                )
            )
        elif state.belief.candidates:
            uniform = 1.0 / len(state.belief.candidates)
            mass = tuple(sorted((word, uniform) for word in state.belief.candidates))
        else:
            raise ValueError("belief must contain candidates")
        return state.remaining_guesses, mass, legal

    def _check_budget(self) -> None:
        if (
            self.time_limit_seconds is not None
            and self._started_at is not None
            and time.perf_counter() - self._started_at >= self.time_limit_seconds
        ):
            raise PolicyBudgetExceeded(
                f"Max-IG budget exceeded after {self.evaluated_guesses} guess evaluations"
            )

    def _can_use_acceleration(self) -> bool:
        return (
            self.use_acceleration
            and type(self.partitioner) is ExactOutcomePartitioner
            and type(self.information_gain_calculator)
            is ExactInformationGainCalculator
        )

    def _matrix_for(
        self, legal: Tuple[str, ...], belief: BeliefState
    ) -> ExactFeedbackCodeMatrix:
        candidate_answers = tuple(belief.candidates)
        key = (legal, candidate_answers)
        cached = self._matrix_cache.get(key)
        if cached is not None:
            return cached
        for matrix in self._matrix_cache.values():
            if matrix.legal_guesses == legal and matrix.contains_answers(candidate_answers):
                self._matrix_cache[key] = matrix
                return matrix
        matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, candidate_answers)
        self._matrix_cache[key] = matrix
        self.feedback_matrix = matrix
        return matrix

    def _select_reference(
        self, state: DecisionState, legal: Tuple[str, ...]
    ) -> str:
        scored = []
        for guess in legal:
            self._check_budget()
            distribution = self.partitioner.partition(
                state.belief, guess, self.feedback_engine
            )
            gain = self.information_gain_calculator.calculate(
                state.belief, guess, distribution
            )
            scored.append((gain, guess))
            self.evaluated_guesses += 1
        return self._resolve_ties(state, scored)

    def _select_accelerated(
        self, state: DecisionState, legal: Tuple[str, ...]
    ) -> str:
        matrix = self._matrix_for(legal, state.belief)
        scorer = MatrixInformationGainCalculator(matrix)
        answer_indices, weights = scorer.belief_arrays(state.belief)
        if len(answer_indices) == 1:
            # A deterministic singleton produces one outcome for every guess,
            # so every exact IG is zero.  Resolving the documented tie directly
            # is equivalent to scoring all rows and avoids redundant work.
            return self._resolve_ties(
                state, [(0.0, guess) for guess in legal]
            )
        if len(answer_indices) <= scorer.SMALL_BELIEF_BATCH_THRESHOLD:
            self._check_budget()
            entropies = scorer.entropies_for_rows(
                matrix.matrix[:, answer_indices], weights
            )
            self.evaluated_guesses += len(legal)
            return self._resolve_ties(
                state, list(zip(entropies.tolist(), legal))
            )
        scored = []
        for guess in legal:
            self._check_budget()
            gain = scorer.entropy_for_row(
                matrix.row_for(guess), answer_indices, weights
            )
            scored.append((max(0.0, gain), guess))
            self.evaluated_guesses += 1
        return self._resolve_ties(state, scored)

    @staticmethod
    def _resolve_ties(
        state: DecisionState, scored: Sequence[Tuple[float, str]]
    ) -> str:
        maximum_gain = max(gain for gain, _ in scored)
        tied = [
            (gain, guess)
            for gain, guess in scored
            if maximum_gain - gain <= POLICY_TIE_TOLERANCE
        ]
        if state.belief.probability_mass:
            total_mass = state.belief.total_mass
            if total_mass <= 0:
                raise ValueError("belief must have positive total mass")
            posterior_mass = {
                word: mass / total_mass for word, mass in state.belief.probability_mass
            }
        elif state.belief.candidates:
            uniform = 1.0 / len(state.belief.candidates)
            posterior_mass = {word: uniform for word in state.belief.candidates}
        else:
            raise ValueError("belief must contain candidates")
        answer_ties = [
            (guess, posterior_mass[guess])
            for _, guess in tied
            if guess in posterior_mass
        ]
        if answer_ties:
            return max(answer_ties, key=lambda item: item[1])[0]
        return tied[0][1]

    def select_guess(self, state: DecisionState, candidate_guesses: Sequence[str]) -> str:
        legal = tuple(candidate_guesses)
        if not legal:
            raise ValueError("candidate_guesses cannot be empty")
        if self._started_at is None:
            self._started_at = time.perf_counter()
        self._check_budget()
        key = self._belief_cache_key(state, legal)
        cached = self._decision_cache.get(key)
        if cached is not None:
            self.decision_cache_hits += 1
            return cached
        self.decision_cache_misses += 1
        if self._can_use_acceleration():
            selected = self._select_accelerated(state, legal)
        else:
            selected = self._select_reference(state, legal)
        self._decision_cache[key] = selected
        return selected


@runtime_checkable
class BayesOptimalPlanner(Protocol):
    """Plans through shared feedback and posterior semantics."""

    def select_guess(
        self,
        state: DecisionState,
        candidate_guesses: Sequence[str],
        feedback_engine: FeedbackEngine,
        posterior_updater: PosteriorUpdater,
    ) -> str:
        ...


@runtime_checkable
class PlannerCache(Protocol):
    """Stores planner results without prescribing a cache representation."""

    def get(self, key: Hashable) -> Optional[str]:
        ...

    def put(self, key: Hashable, guess: str) -> None:
        ...


class InMemoryPlannerCache:
    def __init__(self) -> None:
        self._values: Dict[Hashable, str] = {}

    def get(self, key: Hashable) -> Optional[str]:
        return self._values.get(key)

    def put(self, key: Hashable, guess: str) -> None:
        self._values[key] = guess

    def __len__(self) -> int:
        return len(self._values)


class ExactBayesOptimalPlanner:
    """Exact Bellman planner with solve probability as the primary objective.

    Action values are ``(final solve probability, expected guesses until solve
    or horizon termination)``.  The second component is considered only when
    the first component ties within ``POLICY_TIE_TOLERANCE``.
    """

    ALL_OPTIMIZATION_LAYERS = (
        "closed_forms",
        "matrix_transitions",
        "canonical_memoization",
        "action_ordering",
        "branch_ordering",
        "branch_and_bound",
        "horizon_two_closed_form",
        "horizon_two_batch",
        "horizon_two_child_batch",
        "root_horizon_two_ordering",
        "uniform_h3_branch_capacity",
    )
    HORIZON_TWO_CHILD_BATCH_SIZE = 2
    UNIFORM_H3_CODE_COUNT = 36

    _STAT_KEYS = (
        "states_evaluated",
        "actions_evaluated",
        "actions_completed",
        "actions_pruned",
        "branches_evaluated",
        "scalar_feedback_evaluations",
        "matrix_transition_calls",
        "matrix_eligibility_checks",
        "value_cache_hits",
        "value_cache_misses",
        "closed_form_singleton_hits",
        "closed_form_last_horizon_hits",
        "closed_form_two_candidate_hits",
        "horizon_two_scalar_calls",
        "horizon_two_scalar_actions",
        "horizon_two_batch_calls",
        "horizon_two_batch_actions",
        "horizon_two_batch_matrix_cells",
        "horizon_two_child_batch_blocks",
        "horizon_two_child_batch_children",
        "horizon_two_child_batch_matrix_cells",
        "horizon_two_child_batch_peak_temporary_bytes",
        "horizon_two_child_exact_solves",
        "horizon_two_bound_only_skips",
        "action_sort_calls",
        "branch_grouping_calls",
        "branch_sort_calls",
        "root_order_proxy_calls",
        "root_order_proxy_actions",
        "root_order_proxy_matrix_cells",
        "root_actions_started",
        "root_actions_completed",
        "root_actions_pruned",
        "uniform_h3_capacity_initializations",
        "uniform_h3_capacity_pruned_actions",
        "uniform_h3_capacity_pruned_before_first_child",
    )

    def __init__(
        self,
        cache: Optional[PlannerCache] = None,
        feedback_matrix: Optional[ExactFeedbackCodeMatrix] = None,
        optimization_layers: Optional[Sequence[str]] = None,
        root_audit: bool = False,
        root_audit_limit: Optional[int] = None,
    ) -> None:
        self.cache = cache if cache is not None else InMemoryPlannerCache()
        self.cache_hits = 0
        self.cache_misses = 0
        self._value_cache: Dict[Hashable, PlannerValue] = {}
        default_layers = tuple(
            layer
            for layer in self.ALL_OPTIMIZATION_LAYERS
            if layer != "horizon_two_child_batch"
        )
        requested = (
            default_layers
            if optimization_layers is None
            else tuple(optimization_layers)
        )
        unknown = set(requested) - set(self.ALL_OPTIMIZATION_LAYERS)
        if unknown:
            raise ValueError(
                "unknown exact-planner optimization layer(s): "
                + ", ".join(sorted(unknown))
            )
        self.optimization_layers = tuple(
            layer for layer in self.ALL_OPTIMIZATION_LAYERS if layer in requested
        )
        self.feedback_matrix = feedback_matrix
        self.stats: Dict[str, int] = {key: 0 for key in self._STAT_KEYS}
        self._branch_count_histogram: Dict[str, int] = {}
        self._branch_size_histogram: Dict[str, int] = {}
        self._state_support_histogram: Dict[str, int] = {}
        if root_audit_limit is not None and root_audit_limit <= 0:
            raise ValueError("root_audit_limit must be positive when supplied")
        self.root_audit = root_audit
        self.root_audit_limit = root_audit_limit
        self._root_actions_seen = 0
        self._root_action_records: list[Dict[str, Any]] = []
        self._root_audit_truncated = False
        self._active_root_action: Optional[Dict[str, Any]] = None
        self._root_child_state_key_counts: Dict[Hashable, int] = {}
        self._root_timing_seconds: Dict[str, float] = {
            "root_partition": 0.0,
            "child_h2_solve": 0.0,
            "cache_key": 0.0,
            "pruning": 0.0,
            "root_order_proxy": 0.0,
        }
        self._root_first_incumbent_seconds: Optional[float] = None
        self._root_final_incumbent_seconds: Optional[float] = None

    @staticmethod
    def _key_digest(key: Hashable) -> str:
        return hashlib.sha256(repr(key).encode("utf-8")).hexdigest()[:16]

    def _add_root_timing(self, bucket: str, elapsed: float) -> None:
        if self._active_root_action is None:
            return
        self._active_root_action["timing_seconds"][bucket] += elapsed
        self._root_timing_seconds[bucket] += elapsed

    def _new_root_action_record(self, guess: str) -> Optional[Dict[str, Any]]:
        if not self.root_audit:
            return None
        if (
            self.root_audit_limit is not None
            and len(self._root_action_records) >= self.root_audit_limit
        ):
            self._root_audit_truncated = True
            return None
        return {
            "guess": guess,
            "status": "evaluating",
            "value": None,
            "branch_count": 0,
            "branches": [],
            "child_state_solve_requests": 0,
            "distinct_child_state_keys": 0,
            "repeated_child_state_hits": 0,
            "child_cache_hits": 0,
            "horizon_two_batch_calls": 0,
            "horizon_two_batch_actions": 0,
            "horizon_two_batch_matrix_cells": 0,
            "horizon_two_child_batch_blocks": 0,
            "horizon_two_child_batch_children": 0,
            "horizon_two_child_batch_matrix_cells": 0,
            "horizon_two_child_batch_peak_temporary_bytes": 0,
            "horizon_two_child_exact_solves": 0,
            "horizon_two_bound_only_skips": 0,
            "timing_seconds": {
                "root_partition": 0.0,
                "child_h2_solve": 0.0,
                "cache_key": 0.0,
                "pruning": 0.0,
                "total": 0.0,
            },
            "pruned": False,
            "prune_after_branch_index": None,
            "prune_upper_success": None,
            "prune_lower_expected": None,
            "uniform_h3_capacity_bound_used": False,
            "uniform_h3_capacity_units_initial": None,
            "uniform_h3_capacity_units_remaining": None,
            "uniform_h3_capacity_pruned_before_first_child": False,
            "incumbent_after": None,
        }

    def _enabled(self, layer: str) -> bool:
        return layer in self.optimization_layers

    @property
    def matrix_memory_bytes(self) -> int:
        """Bytes held by the optional exact transition matrix."""

        return self.feedback_matrix.memory_bytes if self.feedback_matrix is not None else 0

    def instrumentation(self) -> Dict[str, object]:
        """Return a stable snapshot of planner counters for benchmark artifacts."""

        root_requests = sum(self._root_child_state_key_counts.values())
        return {
            **self.stats,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "value_cache_entries": len(self._value_cache),
            "planner_cache_entries": len(self.cache)
            if hasattr(self.cache, "__len__")
            else -1,
            "matrix_memory_bytes": self.matrix_memory_bytes,
            "branch_count_histogram": dict(sorted(self._branch_count_histogram.items(), key=lambda item: int(item[0]))),
            "branch_size_histogram": dict(sorted(self._branch_size_histogram.items(), key=lambda item: int(item[0]))),
            "state_support_histogram": dict(sorted(self._state_support_histogram.items(), key=lambda item: int(item[0]))),
            "root_audit_enabled": self.root_audit,
            "root_audit_limit": self.root_audit_limit,
            "root_audit_truncated": self._root_audit_truncated,
            "root_actions_seen": self._root_actions_seen,
            "root_actions_traced": len(self._root_action_records),
            "root_child_state_requests": root_requests,
            "root_distinct_child_state_keys": len(self._root_child_state_key_counts),
            "root_repeated_child_state_hits": max(
                0, root_requests - len(self._root_child_state_key_counts)
            ),
            "root_timing_seconds": dict(self._root_timing_seconds),
            "root_first_incumbent_seconds": self._root_first_incumbent_seconds,
            "root_final_incumbent_seconds": self._root_final_incumbent_seconds,
            "root_action_records": list(self._root_action_records),
        }

    @classmethod
    def _canonical_key(
        cls,
        state: DecisionState,
        candidate_guesses: Sequence[str],
        canonicalize: bool = True,
    ) -> Tuple[object, ...]:
        if canonicalize:
            mass = cls._mass_table(state.belief)
        elif state.belief.probability_mass:
            mass = tuple(state.belief.probability_mass)
        else:
            uniform = 1.0 / len(state.belief.candidates)
            mass = tuple((word, uniform) for word in state.belief.candidates)
        legal = tuple(sorted(candidate_guesses)) if canonicalize else tuple(candidate_guesses)
        return (
            state.remaining_guesses,
            tuple(sorted((word, float(value)) for word, value in mass)),
            legal,
        )

    @staticmethod
    def _mass_table(belief: BeliefState) -> Tuple[Tuple[str, float], ...]:
        if belief.probability_mass:
            total = belief.total_mass
            if total <= 0:
                raise ValueError("belief must have positive total mass")
            return tuple((word, mass / total) for word, mass in belief.probability_mass)
        if not belief.candidates:
            raise ValueError("belief must contain candidates")
        mass = 1.0 / len(belief.candidates)
        return tuple((word, mass) for word in belief.candidates)

    def _record_state_evaluation(self, state: DecisionState) -> None:
        self.stats["states_evaluated"] += 1
        support_key = str(len(state.belief.candidates))
        self._state_support_histogram[support_key] = (
            self._state_support_histogram.get(support_key, 0) + 1
        )

    @classmethod
    def _uniform_h3_capacity_units(
        cls,
        branches: Sequence[
            Tuple[Feedback, float, Tuple[Tuple[str, float], ...]]
        ],
        word_length: int,
    ) -> Tuple[int, ...]:
        """Return root-success capacity numerators for uniform H3 branches.

        The caller divides the sum of these integer units by the uniform root
        support size ``N``.  A winning branch is exact at one answer, while a
        non-winning H2 child can certify at most one answer per feedback code.
        Keeping the units integral makes the O(1) branch decrement exact;
        ``word_length`` is explicit so tests can exercise the winning marker
        without constructing a feedback engine.
        """

        code_count = cls.UNIFORM_H3_CODE_COUNT
        return tuple(
            1
            if outcome == (word_length, 0)
            else min(code_count, len(members))
            for outcome, _, members in branches
        )

    @classmethod
    def _uniform_h3_capacity_eligible(
        cls,
        state: DecisionState,
        mass_table: Tuple[Tuple[str, float], ...],
        feedback_engine: FeedbackEngine,
    ) -> bool:
        """Return whether the exact uniform-H3 branch bound may be used."""

        if (
            state.remaining_guesses != 3
            or type(feedback_engine) is not HardleFeedbackEngine
            or feedback_engine.game_spec.word_length != 5
            or not mass_table
        ):
            return False
        uniform_mass = 1.0 / len(mass_table)
        # Use strict equality.  Treating merely near-uniform weights as
        # uniform could make the capacity bound unsound for weighted beliefs.
        return all(mass == uniform_mass for _, mass in mass_table)

    def select_guess(
        self,
        state: DecisionState,
        candidate_guesses: Sequence[str],
        feedback_engine: FeedbackEngine,
        posterior_updater: PosteriorUpdater,
    ) -> str:
        legal = tuple(candidate_guesses)
        if not legal:
            raise ValueError("candidate_guesses cannot be empty")
        if state.remaining_guesses <= 0:
            raise ValueError("cannot select a guess with no remaining horizon")
        return self._best_guess(state, legal, feedback_engine, posterior_updater)

    def success_probability(
        self,
        state: DecisionState,
        candidate_guesses: Sequence[str],
        feedback_engine: FeedbackEngine,
        posterior_updater: PosteriorUpdater,
    ) -> float:
        legal = tuple(candidate_guesses)
        if state.remaining_guesses <= 0:
            return 0.0
        guess = self._best_guess(state, legal, feedback_engine, posterior_updater)
        return self._guess_value(state, guess, legal, feedback_engine, posterior_updater)[0]

    def _best_guess(
        self,
        state: DecisionState,
        candidate_guesses: Sequence[str],
        feedback_engine: FeedbackEngine,
        posterior_updater: PosteriorUpdater,
    ) -> str:
        is_root = state.remaining_guesses == 3
        key_started = time.perf_counter()
        key = self._canonical_key(
            state,
            candidate_guesses,
            canonicalize=self._enabled("canonical_memoization"),
        )
        cached = self.cache.get(key)
        if self._active_root_action is not None:
            self._add_root_timing(
                "cache_key", time.perf_counter() - key_started
            )
        if cached is not None:
            self.cache_hits += 1
            return cached
        if is_root:
            self._root_actions_seen = 0
            self._root_first_incumbent_seconds = None
            self._root_final_incumbent_seconds = None
        self.cache_misses += 1
        self._record_state_evaluation(state)

        closed_form = self._closed_form_best_guess(state, candidate_guesses)
        if closed_form is not None:
            self.cache.put(key, closed_form)
            return closed_form

        if (
            state.remaining_guesses == 2
            and self._enabled("horizon_two_closed_form")
        ):
            selected = self._horizon_two_best_guess(
                state,
                candidate_guesses,
                feedback_engine,
                posterior_updater,
            )
            self.cache.put(key, selected)
            return selected

        ordered = self._ordered_actions(
            state,
            candidate_guesses,
            feedback_engine=feedback_engine,
        )
        tie_rank = {
            guess: index
            for index, guess in enumerate(
                tuple(sorted(candidate_guesses))
                if self._enabled("canonical_memoization")
                else tuple(candidate_guesses)
            )
        }
        incumbent: Optional[PlannerValue] = None
        incumbent_guess: Optional[str] = None
        root_started = time.perf_counter() if is_root else None
        for guess in ordered:
            if is_root:
                self._root_actions_seen += 1
                self.stats["root_actions_started"] += 1
            record = (
                self._new_root_action_record(guess)
                if is_root
                else None
            )
            action_started = time.perf_counter() if record is not None else None
            batch_snapshot = {
                key: self.stats[key]
                for key in (
                    "horizon_two_batch_calls",
                    "horizon_two_batch_actions",
                    "horizon_two_batch_matrix_cells",
                    "horizon_two_child_batch_blocks",
                    "horizon_two_child_batch_children",
                    "horizon_two_child_batch_matrix_cells",
                    "horizon_two_child_batch_peak_temporary_bytes",
                    "horizon_two_child_exact_solves",
                    "horizon_two_bound_only_skips",
                )
            }
            previous_root_action = self._active_root_action
            self._active_root_action = record
            self.stats["actions_evaluated"] += 1
            try:
                value = self._guess_value(
                    state,
                    guess,
                    candidate_guesses,
                    feedback_engine,
                    posterior_updater,
                    incumbent=incumbent,
                )
            finally:
                self._active_root_action = previous_root_action
            if record is not None:
                assert action_started is not None
                record["timing_seconds"]["total"] = (
                    time.perf_counter() - action_started
                )
                for key, before in batch_snapshot.items():
                    record[key] = self.stats[key] - before
            if value is None:
                self.stats["actions_pruned"] += 1
                if is_root:
                    self.stats["root_actions_pruned"] += 1
                if record is not None:
                    record["status"] = "pruned"
                    record["pruned"] = True
                    self._root_action_records.append(record)
                continue
            self.stats["actions_completed"] += 1
            if is_root:
                self.stats["root_actions_completed"] += 1
            if incumbent is None or self._value_is_better(
                value,
                incumbent,
                guess,
                incumbent_guess,
                tie_rank,
            ):
                incumbent = value
                incumbent_guess = guess
                if record is not None:
                    record["incumbent_after"] = list(value)
                if is_root and root_started is not None:
                    elapsed = time.perf_counter() - root_started
                    if self._root_first_incumbent_seconds is None:
                        self._root_first_incumbent_seconds = elapsed
                    self._root_final_incumbent_seconds = elapsed
            if record is not None:
                record["status"] = "completed"
                record["value"] = list(value)
                self._root_action_records.append(record)
            elif is_root and self.root_audit:
                self._root_audit_truncated = True
        if incumbent_guess is None:
            raise RuntimeError("exact planner evaluated no complete action")
        self.cache.put(key, incumbent_guess)
        return incumbent_guess

    def _guess_value(
        self,
        state: DecisionState,
        guess: str,
        candidate_guesses: Sequence[str],
        feedback_engine: FeedbackEngine,
        posterior_updater: PosteriorUpdater,
        incumbent: Optional[PlannerValue] = None,
    ) -> Optional[PlannerValue]:
        key_started = time.perf_counter()
        key = (
            "value",
            self._canonical_key(
                state,
                candidate_guesses,
                canonicalize=self._enabled("canonical_memoization"),
            ),
            guess,
        )
        cached = key in self._value_cache
        if self._active_root_action is not None:
            self._add_root_timing(
                "cache_key", time.perf_counter() - key_started
            )
        if cached:
            self.stats["value_cache_hits"] += 1
            return self._value_cache[key]
        self.stats["value_cache_misses"] += 1

        closed_form = self._closed_form_guess_value(
            state,
            guess,
            candidate_guesses,
        )
        if closed_form is not None:
            self._value_cache[key] = closed_form
            return closed_form

        horizon_two = self._horizon_two_guess_value(
            state,
            guess,
            candidate_guesses,
            feedback_engine,
        )
        if horizon_two is not None:
            self._value_cache[key] = horizon_two
            return horizon_two

        mass_table = self._mass_table(state.belief)
        use_matrix = self._can_use_matrix(
            state.belief,
            guess,
            feedback_engine,
            mass_table=mass_table,
        )
        partition_started = time.perf_counter()
        branches = self._transition_branches(
            state,
            guess,
            mass_table,
            feedback_engine,
            use_matrix=use_matrix,
        )
        if self._active_root_action is not None:
            self._add_root_timing(
                "root_partition", time.perf_counter() - partition_started
            )
            self._active_root_action["branch_count"] = len(branches)
            self._active_root_action["branches"] = [
                {
                    "index": index,
                    "feedback": list(outcome),
                    "posterior_mass": probability,
                    "support_size": len(members),
                    "is_win": outcome == (len(guess), 0),
                    "processed": False,
                    "child_state_key": None,
                    "child_cache_hit": False,
                }
                for index, (outcome, probability, members) in enumerate(branches)
            ]
        success_probability = 0.0
        expected_guesses = 1.0
        processed_probability = 0.0

        uniform_h3_capacity_units: Optional[Tuple[int, ...]] = None
        remaining_capacity_units = 0
        if (
            self._enabled("uniform_h3_branch_capacity")
            and self._uniform_h3_capacity_eligible(
                state, mass_table, feedback_engine
            )
        ):
            uniform_h3_capacity_units = self._uniform_h3_capacity_units(
                branches, feedback_engine.game_spec.word_length
            )
            remaining_capacity_units = sum(uniform_h3_capacity_units)
            self.stats["uniform_h3_capacity_initializations"] += 1
            if self._active_root_action is not None:
                self._active_root_action[
                    "uniform_h3_capacity_bound_used"
                ] = True
                self._active_root_action[
                    "uniform_h3_capacity_units_initial"
                ] = remaining_capacity_units
                self._active_root_action[
                    "uniform_h3_capacity_units_remaining"
                ] = remaining_capacity_units

        use_child_batch = (
            state.remaining_guesses == 3
            and self._enabled("horizon_two_child_batch")
        )
        pending_children: list[Dict[str, Any]] = []
        child_h2_work_started = False

        def check_branch_pruning(
            branch_index: int, *, before_first_child: bool = False
        ) -> bool:
            if incumbent is None or not self._enabled("branch_and_bound"):
                return False
            if uniform_h3_capacity_units is not None:
                upper_success = math.nextafter(
                    math.fsum(
                        (
                            success_probability,
                            remaining_capacity_units / len(mass_table),
                        )
                    ),
                    math.inf,
                )
            else:
                upper_success = success_probability + max(
                    0.0, 1.0 - processed_probability
                )
            prune_started = time.perf_counter()
            cannot_beat = self._cannot_beat_incumbent(
                upper_success, expected_guesses, incumbent
            )
            if self._active_root_action is not None:
                self._add_root_timing(
                    "pruning", time.perf_counter() - prune_started
                )
            if cannot_beat:
                if uniform_h3_capacity_units is not None:
                    self.stats["uniform_h3_capacity_pruned_actions"] += 1
                    if before_first_child or not child_h2_work_started:
                        self.stats[
                            "uniform_h3_capacity_pruned_before_first_child"
                        ] += 1
                if self._active_root_action is not None:
                    self._active_root_action["pruned"] = True
                    self._active_root_action["prune_after_branch_index"] = branch_index
                    self._active_root_action["prune_upper_success"] = upper_success
                    self._active_root_action["prune_lower_expected"] = expected_guesses
                    if (
                        uniform_h3_capacity_units is not None
                        and (before_first_child or not child_h2_work_started)
                    ):
                        self._active_root_action[
                            "uniform_h3_capacity_pruned_before_first_child"
                        ] = True
                return True
            return False

        def mark_branch_processed(branch_index: int) -> None:
            nonlocal remaining_capacity_units
            if uniform_h3_capacity_units is not None:
                remaining_capacity_units -= uniform_h3_capacity_units[branch_index]
                if self._active_root_action is not None:
                    self._active_root_action[
                        "uniform_h3_capacity_units_remaining"
                    ] = remaining_capacity_units

        def flush_pending_children() -> bool:
            nonlocal success_probability
            nonlocal expected_guesses
            nonlocal processed_probability
            nonlocal child_h2_work_started
            if not pending_children:
                return False
            child_h2_work_started = True
            child_results = self._evaluate_horizon_two_child_block(
                pending_children,
                candidate_guesses,
                feedback_engine,
                posterior_updater,
            )
            for item, result in zip(pending_children, child_results):
                branch_index = int(item["branch_index"])
                probability = float(item["probability"])
                next_success, next_expected = result[1]
                if self._active_root_action is not None:
                    record = self._active_root_action
                    record["branches"][branch_index]["processed"] = True
                    child_cache_hit = result[2]
                    if child_cache_hit:
                        record["child_cache_hits"] += 1
                    record["branches"][branch_index]["child_cache_hit"] = (
                        child_cache_hit
                    )
                success_probability += probability * next_success
                expected_guesses += probability * next_expected
                processed_probability += probability
                mark_branch_processed(branch_index)
                if check_branch_pruning(branch_index):
                    pending_children.clear()
                    return True
            pending_children.clear()
            return False

        if uniform_h3_capacity_units is not None and check_branch_pruning(
            -1, before_first_child=True
        ):
            return None

        for branch_index, (outcome, probability, members) in enumerate(branches):
            self.stats["branches_evaluated"] += 1

            if use_child_batch:
                if outcome == (len(guess), 0):
                    if flush_pending_children():
                        return None
                    if self._active_root_action is not None:
                        self._active_root_action["branches"][branch_index]["processed"] = True
                    success_probability += probability
                    processed_probability += probability
                    mark_branch_processed(branch_index)
                    if check_branch_pruning(branch_index):
                        return None
                    continue
                if state.remaining_guesses > 1:
                    posterior = self._posterior_for_branch(
                        state.belief,
                        guess,
                        outcome,
                        members,
                        posterior_updater,
                        use_matrix=use_matrix,
                    )
                    next_state = DecisionState(
                        belief=posterior,
                        remaining_guesses=state.remaining_guesses - 1,
                    )
                    child_key_started = time.perf_counter()
                    child_key = self._canonical_key(
                        next_state,
                        candidate_guesses,
                        canonicalize=self._enabled("canonical_memoization"),
                    )
                    if self._active_root_action is not None:
                        self._add_root_timing(
                            "cache_key", time.perf_counter() - child_key_started
                        )
                        record = self._active_root_action
                        record["child_state_solve_requests"] += 1
                        prior_requests = self._root_child_state_key_counts.get(
                            child_key, 0
                        )
                        self._root_child_state_key_counts[child_key] = prior_requests + 1
                        if prior_requests == 0:
                            record["distinct_child_state_keys"] += 1
                        else:
                            record["repeated_child_state_hits"] += 1
                        record["branches"][branch_index]["child_state_key"] = (
                            self._key_digest(child_key)
                        )
                    pending_children.append(
                        {
                            "branch_index": branch_index,
                            "probability": probability,
                            "state": next_state,
                            "key": child_key,
                        }
                    )
                    if len(pending_children) >= self.HORIZON_TWO_CHILD_BATCH_SIZE:
                        if flush_pending_children():
                            return None
                    continue

            if self._active_root_action is not None:
                self._active_root_action["branches"][branch_index]["processed"] = True
            if outcome == (len(guess), 0):
                success_probability += probability
            elif state.remaining_guesses > 1:
                posterior = self._posterior_for_branch(
                    state.belief,
                    guess,
                    outcome,
                    members,
                    posterior_updater,
                    use_matrix=use_matrix,
                )
                next_state = DecisionState(
                    belief=posterior,
                    remaining_guesses=state.remaining_guesses - 1,
                )
                child_key_started = time.perf_counter()
                child_key = self._canonical_key(
                    next_state,
                    candidate_guesses,
                    canonicalize=self._enabled("canonical_memoization"),
                )
                if self._active_root_action is not None:
                    self._add_root_timing(
                        "cache_key", time.perf_counter() - child_key_started
                    )
                    record = self._active_root_action
                    record["child_state_solve_requests"] += 1
                    prior_requests = self._root_child_state_key_counts.get(
                        child_key, 0
                    )
                    self._root_child_state_key_counts[child_key] = prior_requests + 1
                    if prior_requests == 0:
                        record["distinct_child_state_keys"] += 1
                    else:
                        record["repeated_child_state_hits"] += 1
                    branch_record = record["branches"][branch_index]
                    branch_record["child_state_key"] = self._key_digest(child_key)
                child_cache_hits_before = self.cache_hits
                child_exact_before = (
                    self.stats["horizon_two_batch_calls"]
                    + self.stats["horizon_two_scalar_calls"]
                )
                child_started = time.perf_counter()
                child_h2_work_started = True
                next_guess = self._best_guess(
                    next_state,
                    candidate_guesses,
                    feedback_engine,
                    posterior_updater,
                )
                next_success, next_expected = self._guess_value(
                    next_state,
                    next_guess,
                    candidate_guesses,
                    feedback_engine,
                    posterior_updater,
                )
                if self._active_root_action is not None:
                    self._add_root_timing(
                        "child_h2_solve", time.perf_counter() - child_started
                    )
                    record = self._active_root_action
                    child_cache_hit = self.cache_hits > child_cache_hits_before
                    if child_cache_hit:
                        record["child_cache_hits"] += 1
                    record["branches"][branch_index]["child_cache_hit"] = (
                        child_cache_hit
                    )
                if next_success is None or next_expected is None:
                    raise RuntimeError("best child action was unexpectedly pruned")
                child_exact_after = (
                    self.stats["horizon_two_batch_calls"]
                    + self.stats["horizon_two_scalar_calls"]
                )
                if child_exact_after > child_exact_before:
                    self.stats["horizon_two_child_exact_solves"] += 1
                success_probability += probability * next_success
                expected_guesses += probability * next_expected
            processed_probability += probability
            mark_branch_processed(branch_index)
            if check_branch_pruning(branch_index):
                return None
        if use_child_batch and flush_pending_children():
            return None
        value = (success_probability, expected_guesses)
        self._value_cache[key] = value
        return value

    @staticmethod
    def _value_is_better(
        candidate: PlannerValue,
        incumbent: PlannerValue,
        candidate_guess: str,
        incumbent_guess: Optional[str],
        tie_rank: Dict[str, int],
    ) -> bool:
        if candidate[0] > incumbent[0] + POLICY_TIE_TOLERANCE:
            return True
        if abs(candidate[0] - incumbent[0]) > POLICY_TIE_TOLERANCE:
            return False
        if candidate[1] < incumbent[1] - POLICY_TIE_TOLERANCE:
            return True
        if abs(candidate[1] - incumbent[1]) > POLICY_TIE_TOLERANCE:
            return False
        if incumbent_guess is None:
            return True
        return tie_rank[candidate_guess] < tie_rank[incumbent_guess]

    @staticmethod
    def _cannot_beat_incumbent(
        upper_success: float,
        lower_expected: float,
        incumbent: PlannerValue,
    ) -> bool:
        if upper_success < incumbent[0] - POLICY_TIE_TOLERANCE:
            return True
        return (
            abs(upper_success - incumbent[0]) <= POLICY_TIE_TOLERANCE
            # Keep equality cases alive so the planner can preserve its
            # deterministic tie order.  A strict lower-bound loss is enough
            # to prove that the action cannot improve the lexicographic value.
            and lower_expected > incumbent[1] + POLICY_TIE_TOLERANCE
        )

    def _closed_form_best_guess(
        self,
        state: DecisionState,
        candidate_guesses: Sequence[str],
    ) -> Optional[str]:
        if not self._enabled("closed_forms"):
            return None
        mass = self._mass_table(state.belief)
        if len(mass) == 1:
            self.stats["closed_form_singleton_hits"] += 1
            target = mass[0][0]
            return target if target in candidate_guesses else tuple(candidate_guesses)[0]
        if state.remaining_guesses == 1:
            self.stats["closed_form_last_horizon_hits"] += 1
            return self._best_candidate_or_first(state, candidate_guesses)
        if len(mass) == 2:
            candidates = {word for word, _ in mass}
            if all(candidate in candidate_guesses for candidate in candidates):
                self.stats["closed_form_two_candidate_hits"] += 1
                return self._best_candidate_or_first(state, candidate_guesses)
        return None

    def _horizon_two_best_guess(
        self,
        state: DecisionState,
        candidate_guesses: Sequence[str],
        feedback_engine: FeedbackEngine,
        posterior_updater: PosteriorUpdater,
    ) -> str:
        del posterior_updater
        legal = tuple(candidate_guesses)
        state_key = self._canonical_key(
            state,
            legal,
            canonicalize=self._enabled("canonical_memoization"),
        )
        tie_rank = {
            guess: index
            for index, guess in enumerate(
                tuple(sorted(legal))
                if self._enabled("canonical_memoization")
                else legal
            )
        }
        incumbent: Optional[PlannerValue] = None
        incumbent_guess: Optional[str] = None
        batch_values = self._horizon_two_batch_values(
            state, legal, feedback_engine
        )
        if batch_values is not None:
            self.stats["horizon_two_batch_calls"] += 1
            self.stats["horizon_two_batch_actions"] += len(legal)
            values = batch_values
        else:
            values = tuple(
                self._horizon_two_guess_value(
                    state,
                    guess,
                    legal,
                    feedback_engine,
                )
                for guess in legal
            )
        for guess, value in zip(legal, values):
            self.stats["actions_evaluated"] += 1
            if value is None:
                raise RuntimeError("horizon-two formula unexpectedly unavailable")
            self.stats["actions_completed"] += 1
            self._value_cache[("value", state_key, guess)] = value
            if incumbent is None or self._value_is_better(
                value,
                incumbent,
                guess,
                incumbent_guess,
                tie_rank,
            ):
                incumbent = value
                incumbent_guess = guess
        if incumbent_guess is None:
            raise RuntimeError("horizon-two formula evaluated no legal action")
        return incumbent_guess

    def _horizon_two_batch_values(
        self,
        state: DecisionState,
        candidate_guesses: Sequence[str],
        feedback_engine: FeedbackEngine,
    ) -> Optional[Tuple[PlannerValue, ...]]:
        inputs = self._horizon_two_batch_inputs(
            state, candidate_guesses, feedback_engine
        )
        if inputs is None:
            return None
        legal, answer_words, weights = inputs
        assert self.feedback_matrix is not None
        values = self.feedback_matrix.horizon_two_values(
            legal,
            answer_words,
            weights,
            legal,
        )
        self.stats["horizon_two_batch_matrix_cells"] += len(legal) * len(answer_words)
        return tuple(values)

    def _horizon_two_batch_inputs(
        self,
        state: DecisionState,
        candidate_guesses: Sequence[str],
        feedback_engine: FeedbackEngine,
    ) -> Optional[Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[float, ...]]]:
        if (
            not self._enabled("horizon_two_batch")
            or self.feedback_matrix is None
            or type(feedback_engine) is not HardleFeedbackEngine
            or feedback_engine.game_spec.word_length
            != self.feedback_matrix.word_length
        ):
            return None
        legal = tuple(candidate_guesses)
        if not all(guess in self.feedback_matrix._guess_indices for guess in legal):
            return None
        mass_table = self._mass_table(state.belief)
        answer_words = tuple(word for word, _ in mass_table)
        if not self.feedback_matrix.contains_answers(answer_words):
            return None
        return (
            legal,
            answer_words,
            tuple(mass for _, mass in mass_table),
        )

    def _select_horizon_two_value_row(
        self,
        state: DecisionState,
        state_key: Hashable,
        legal: Tuple[str, ...],
        values: Sequence[Sequence[float]],
    ) -> Tuple[str, PlannerValue]:
        tie_rank = {
            guess: index
            for index, guess in enumerate(
                tuple(sorted(legal))
                if self._enabled("canonical_memoization")
                else legal
            )
        }
        incumbent: Optional[PlannerValue] = None
        incumbent_guess: Optional[str] = None
        for index, (guess, value) in enumerate(zip(legal, values)):
            planner_value = (float(value[0]), float(value[1]))
            self.stats["actions_evaluated"] += 1
            self.stats["actions_completed"] += 1
            self._value_cache[("value", state_key, guess)] = planner_value
            if incumbent is None or self._value_is_better(
                planner_value,
                incumbent,
                guess,
                incumbent_guess,
                tie_rank,
            ):
                incumbent = planner_value
                incumbent_guess = guess
        if incumbent_guess is None or incumbent is None:
            raise RuntimeError("horizon-two formula evaluated no legal action")
        return incumbent_guess, incumbent

    def _evaluate_horizon_two_child_block(
        self,
        pending: Sequence[Dict[str, Any]],
        candidate_guesses: Sequence[str],
        feedback_engine: FeedbackEngine,
        posterior_updater: PosteriorUpdater,
    ) -> Tuple[Tuple[str, PlannerValue, bool, bool], ...]:
        """Evaluate pending H2 children, sharing one exact ragged matrix pass."""

        legal = tuple(candidate_guesses)
        results: list[Optional[Tuple[str, PlannerValue, bool, bool]]] = [
            None
        ] * len(pending)
        batch_items: list[Tuple[int, Dict[str, Any], Tuple[str, ...], Tuple[float, ...]]] = []

        for index, item in enumerate(pending):
            next_state = item["state"]
            state_key = item["key"]
            assert isinstance(next_state, DecisionState)
            assert isinstance(state_key, tuple)
            cached_guess = self.cache.get(state_key)
            if cached_guess is not None:
                self.cache_hits += 1
                value = self._value_cache.get(("value", state_key, cached_guess))
                exact_solve = False
                if value is None:
                    started = time.perf_counter()
                    value = self._guess_value(
                        next_state,
                        cached_guess,
                        legal,
                        feedback_engine,
                        posterior_updater,
                    )
                    self._add_root_timing(
                        "child_h2_solve", time.perf_counter() - started
                    )
                    exact_solve = True
                if value is None:
                    raise RuntimeError("cached child action had no exact value")
                if exact_solve:
                    self.stats["horizon_two_child_exact_solves"] += 1
                results[index] = (cached_guess, value, True, exact_solve)
                continue

            self.cache_misses += 1
            self._record_state_evaluation(next_state)
            closed_form = self._closed_form_best_guess(next_state, legal)
            if closed_form is not None:
                value = self._closed_form_guess_value(
                    next_state, closed_form, legal
                )
                if value is None:
                    raise RuntimeError("closed-form child action had no value")
                self.cache.put(state_key, closed_form)
                self._value_cache[("value", state_key, closed_form)] = value
                results[index] = (closed_form, value, False, False)
                continue

            inputs = self._horizon_two_batch_inputs(
                next_state, legal, feedback_engine
            )
            if inputs is None:
                started = time.perf_counter()
                next_guess = self._horizon_two_best_guess(
                    next_state,
                    legal,
                    feedback_engine,
                    posterior_updater,
                )
                self.cache.put(state_key, next_guess)
                value = self._guess_value(
                    next_state,
                    next_guess,
                    legal,
                    feedback_engine,
                    posterior_updater,
                )
                self._add_root_timing(
                    "child_h2_solve", time.perf_counter() - started
                )
                if value is None:
                    raise RuntimeError("child action was unexpectedly pruned")
                self.stats["horizon_two_child_exact_solves"] += 1
                results[index] = (next_guess, value, False, True)
                continue
            _, answer_words, weights = inputs
            batch_items.append((index, item, answer_words, weights))

        if batch_items:
            assert self.feedback_matrix is not None
            started = time.perf_counter()
            block_values = self.feedback_matrix.horizon_two_values_block(
                legal,
                tuple(answer_words for _, _, answer_words, _ in batch_items),
                tuple(weights for _, _, _, weights in batch_items),
                legal,
            )
            self._add_root_timing(
                "child_h2_solve", time.perf_counter() - started
            )
            self.stats["horizon_two_child_batch_blocks"] += 1
            self.stats["horizon_two_child_batch_children"] += len(batch_items)
            self.stats["horizon_two_child_batch_matrix_cells"] += sum(
                len(legal) * len(answer_words)
                for _, _, answer_words, _ in batch_items
            )
            self.stats["horizon_two_child_batch_peak_temporary_bytes"] = max(
                self.stats["horizon_two_child_batch_peak_temporary_bytes"],
                self.feedback_matrix.horizon_two_block_temporary_bytes(
                    len(batch_items),
                    len(legal),
                    sum(len(answer_words) for _, _, answer_words, _ in batch_items),
                ),
            )
            self.stats["horizon_two_child_exact_solves"] += len(batch_items)
            for local_index, (index, item, answer_words, _) in enumerate(batch_items):
                next_state = item["state"]
                state_key = item["key"]
                assert isinstance(next_state, DecisionState)
                assert isinstance(state_key, tuple)
                next_guess, value = self._select_horizon_two_value_row(
                    next_state,
                    state_key,
                    legal,
                    block_values[local_index],
                )
                self.cache.put(state_key, next_guess)
                self.stats["horizon_two_batch_calls"] += 1
                self.stats["horizon_two_batch_actions"] += len(legal)
                self.stats["horizon_two_batch_matrix_cells"] += len(
                    legal
                ) * len(answer_words)
                results[index] = (next_guess, value, False, True)

        if any(result is None for result in results):
            raise RuntimeError("horizon-two child batch missed a result")
        return tuple(result for result in results if result is not None)

    def _horizon_two_guess_value(
        self,
        state: DecisionState,
        guess: str,
        candidate_guesses: Sequence[str],
        feedback_engine: FeedbackEngine,
    ) -> Optional[PlannerValue]:
        if (
            state.remaining_guesses != 2
            or not self._enabled("horizon_two_closed_form")
        ):
            return None
        self.stats["horizon_two_scalar_calls"] += 1
        mass_table = self._mass_table(state.belief)
        branches = self._transition_branches(
            state,
            guess,
            mass_table,
            feedback_engine,
        )
        legal = set(candidate_guesses)
        branch_maxima = []
        for _, _, members in branches:
            branch_maxima.append(
                max(
                    (mass for word, mass in members if word in legal),
                    default=0.0,
                )
            )
        mass_by_word = dict(mass_table)
        success_probability = math.fsum(branch_maxima)
        expected_guesses = 2.0 - mass_by_word.get(guess, 0.0)
        self.stats["horizon_two_scalar_actions"] += 1
        return success_probability, expected_guesses

    def _best_candidate_or_first(
        self,
        state: DecisionState,
        candidate_guesses: Sequence[str],
    ) -> str:
        mass = dict(self._mass_table(state.belief))
        ranked = [
            (index, guess, mass[guess])
            for index, guess in enumerate(candidate_guesses)
            if guess in mass
        ]
        if not ranked:
            return tuple(candidate_guesses)[0]
        return max(ranked, key=lambda item: (item[2], -item[0]))[1]

    def _closed_form_guess_value(
        self,
        state: DecisionState,
        guess: str,
        candidate_guesses: Sequence[str],
    ) -> Optional[PlannerValue]:
        if not self._enabled("closed_forms"):
            return None
        mass = dict(self._mass_table(state.belief))
        if state.remaining_guesses == 1:
            return (mass.get(guess, 0.0), 1.0)
        if len(mass) == 1:
            target = next(iter(mass))
            if guess == target:
                return (1.0, 1.0)
            if target in candidate_guesses:
                return (1.0, 2.0)
            return (0.0, 1.0)
        if len(mass) == 2 and guess in mass and all(
            target in candidate_guesses for target in mass
        ):
            return (1.0, 2.0 - mass[guess])
        return None

    def _ordered_actions(
        self,
        state: DecisionState,
        candidate_guesses: Sequence[str],
        feedback_engine: Optional[FeedbackEngine] = None,
    ) -> Tuple[str, ...]:
        legal = tuple(candidate_guesses)
        if not self._enabled("action_ordering"):
            return legal
        self.stats["action_sort_calls"] += 1
        mass = dict(self._mass_table(state.belief))
        candidates = sorted(
            (guess for guess in legal if guess in mass),
            key=lambda guess: (-mass[guess], guess),
        )
        probes = sorted(guess for guess in legal if guess not in mass)
        if (
            state.remaining_guesses == 3
            and feedback_engine is not None
            and self._enabled("root_horizon_two_ordering")
        ):
            proxy_scores = self._root_horizon_two_proxy(
                state,
                legal,
                feedback_engine,
            )
            if proxy_scores is not None:
                candidates = sorted(
                    candidates,
                    key=lambda guess: (
                        -proxy_scores[guess][0],
                        proxy_scores[guess][1],
                        -mass[guess],
                        guess,
                    ),
                )
                probes = sorted(
                    probes,
                    key=lambda guess: (
                        -proxy_scores[guess][0],
                        proxy_scores[guess][1],
                        guess,
                    ),
                )
        return tuple(candidates + probes)

    def _root_horizon_two_proxy(
        self,
        state: DecisionState,
        candidate_guesses: Sequence[str],
        feedback_engine: FeedbackEngine,
    ) -> Optional[Dict[str, PlannerValue]]:
        """Return exact h=2 values used only to order h=3 root actions.

        The proxy is deliberately not a bound and never removes an action.
        It uses one exact matrix batch over the current root support, so the
        ordering layer can be measured independently from recursive h=3 work.
        """

        if (
            self.feedback_matrix is None
            or not self._enabled("horizon_two_batch")
            or type(feedback_engine) is not HardleFeedbackEngine
            or feedback_engine.game_spec.word_length
            != self.feedback_matrix.word_length
        ):
            return None
        legal = tuple(candidate_guesses)
        if not all(guess in self.feedback_matrix._guess_indices for guess in legal):
            return None
        mass_table = self._mass_table(state.belief)
        answer_words = tuple(word for word, _ in mass_table)
        if not self.feedback_matrix.contains_answers(answer_words):
            return None
        started = time.perf_counter()
        values = self.feedback_matrix.horizon_two_values(
            legal,
            answer_words,
            tuple(mass for _, mass in mass_table),
            legal,
        )
        elapsed = time.perf_counter() - started
        self.stats["root_order_proxy_calls"] += 1
        self.stats["root_order_proxy_actions"] += len(legal)
        self.stats["root_order_proxy_matrix_cells"] += len(legal) * len(answer_words)
        self._root_timing_seconds["root_order_proxy"] += elapsed
        return dict(zip(legal, values))

    def _can_use_matrix(
        self,
        belief: BeliefState,
        guess: str,
        feedback_engine: FeedbackEngine,
        mass_table: Optional[Tuple[Tuple[str, float], ...]] = None,
    ) -> bool:
        self.stats["matrix_eligibility_checks"] += 1
        if not self._enabled("matrix_transitions") or self.feedback_matrix is None:
            return False
        if type(feedback_engine) is not HardleFeedbackEngine:
            return False
        if feedback_engine.game_spec.word_length != self.feedback_matrix.word_length:
            return False
        if mass_table is None:
            mass_table = self._mass_table(belief)
        return guess in self.feedback_matrix._guess_indices and self.feedback_matrix.contains_answers(
            tuple(word for word, _ in mass_table)
        )

    def _transition_branches(
        self,
        state: DecisionState,
        guess: str,
        mass_table: Tuple[Tuple[str, float], ...],
        feedback_engine: FeedbackEngine,
        use_matrix: Optional[bool] = None,
    ) -> Tuple[Tuple[Feedback, float, Tuple[Tuple[str, float], ...]], ...]:
        self.stats["branch_grouping_calls"] += 1
        if use_matrix is None:
            use_matrix = self._can_use_matrix(
                state.belief,
                guess,
                feedback_engine,
                mass_table=mass_table,
            )
        if use_matrix:
            assert self.feedback_matrix is not None
            self.stats["matrix_transition_calls"] += 1
            words = tuple(word for word, _ in mass_table)
            indices = self.feedback_matrix.answer_indices(words)
            values = self.feedback_matrix.row_for(guess)[indices]
            grouped: Dict[int, list[Tuple[str, float]]] = {}
            for (word, mass), code in zip(mass_table, values):
                grouped.setdefault(int(code), []).append((word, mass))
            branches = [
                (
                    self.feedback_matrix.decode_code(code),
                    math.fsum(mass for _, mass in members),
                    tuple(members),
                )
                for code, members in grouped.items()
            ]
        else:
            grouped_scalar: Dict[Feedback, list[Tuple[str, float]]] = {}
            for target, mass in mass_table:
                self.stats["scalar_feedback_evaluations"] += 1
                outcome = tuple(feedback_engine.evaluate(guess, target))
                grouped_scalar.setdefault(outcome, []).append((target, mass))
            branches = [
                (outcome, math.fsum(mass for _, mass in members), tuple(members))
                for outcome, members in grouped_scalar.items()
            ]
        branch_count_key = str(len(branches))
        self._branch_count_histogram[branch_count_key] = (
            self._branch_count_histogram.get(branch_count_key, 0) + 1
        )
        for _, _, members in branches:
            branch_size_key = str(len(members))
            self._branch_size_histogram[branch_size_key] = (
                self._branch_size_histogram.get(branch_size_key, 0) + 1
            )
        if self._enabled("branch_ordering"):
            self.stats["branch_sort_calls"] += 1
            branches.sort(key=lambda item: (-item[1], item[0]))
        return tuple(branches)

    @staticmethod
    def _posterior_for_branch(
        belief: BeliefState,
        guess: str,
        outcome: Feedback,
        members: Tuple[Tuple[str, float], ...],
        posterior_updater: PosteriorUpdater,
        use_matrix: bool,
    ) -> BeliefState:
        if not use_matrix:
            return posterior_updater.update(belief, guess, outcome)
        probability = math.fsum(mass for _, mass in members)
        normalized = tuple(
            (target, mass / probability) for target, mass in members
        )
        return BeliefState(
            candidates=tuple(target for target, _ in normalized),
            observations=belief.observations + ((guess, outcome),),
            probability_mass=normalized,
        )


class ExactBayesOptimalReferencePlanner(ExactBayesOptimalPlanner):
    """Scalar exhaustive planner retained as the exact regression oracle."""

    def __init__(self, cache: Optional[PlannerCache] = None) -> None:
        super().__init__(cache=cache, optimization_layers=())
