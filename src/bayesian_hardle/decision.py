"""Baseline policies and exact finite-horizon Bayes planning."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
import time
from typing import Dict, Hashable, Optional, Protocol, Sequence, Tuple, runtime_checkable

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
    )

    _STAT_KEYS = (
        "states_evaluated",
        "actions_evaluated",
        "actions_completed",
        "actions_pruned",
        "branches_evaluated",
        "scalar_feedback_evaluations",
        "matrix_transition_calls",
        "value_cache_hits",
        "value_cache_misses",
        "closed_form_singleton_hits",
        "closed_form_last_horizon_hits",
        "closed_form_two_candidate_hits",
        "horizon_two_scalar_calls",
        "horizon_two_scalar_actions",
        "horizon_two_batch_calls",
        "horizon_two_batch_actions",
    )

    def __init__(
        self,
        cache: Optional[PlannerCache] = None,
        feedback_matrix: Optional[ExactFeedbackCodeMatrix] = None,
        optimization_layers: Optional[Sequence[str]] = None,
    ) -> None:
        self.cache = cache if cache is not None else InMemoryPlannerCache()
        self.cache_hits = 0
        self.cache_misses = 0
        self._value_cache: Dict[Hashable, PlannerValue] = {}
        requested = (
            self.ALL_OPTIMIZATION_LAYERS
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

    def _enabled(self, layer: str) -> bool:
        return layer in self.optimization_layers

    @property
    def matrix_memory_bytes(self) -> int:
        """Bytes held by the optional exact transition matrix."""

        return self.feedback_matrix.memory_bytes if self.feedback_matrix is not None else 0

    def instrumentation(self) -> Dict[str, int]:
        """Return a stable snapshot of planner counters for benchmark artifacts."""

        return {
            **self.stats,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "value_cache_entries": len(self._value_cache),
            "planner_cache_entries": len(self.cache)
            if hasattr(self.cache, "__len__")
            else -1,
            "matrix_memory_bytes": self.matrix_memory_bytes,
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
        key = self._canonical_key(
            state,
            candidate_guesses,
            canonicalize=self._enabled("canonical_memoization"),
        )
        cached = self.cache.get(key)
        if cached is not None:
            self.cache_hits += 1
            return cached
        self.cache_misses += 1
        self.stats["states_evaluated"] += 1

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

        ordered = self._ordered_actions(state, candidate_guesses)
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
        for guess in ordered:
            self.stats["actions_evaluated"] += 1
            value = self._guess_value(
                state,
                guess,
                candidate_guesses,
                feedback_engine,
                posterior_updater,
                incumbent=incumbent,
            )
            if value is None:
                self.stats["actions_pruned"] += 1
                continue
            self.stats["actions_completed"] += 1
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
        key = (
            "value",
            self._canonical_key(
                state,
                candidate_guesses,
                canonicalize=self._enabled("canonical_memoization"),
            ),
            guess,
        )
        if key in self._value_cache:
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
        branches = self._transition_branches(
            state,
            guess,
            mass_table,
            feedback_engine,
        )
        success_probability = 0.0
        expected_guesses = 1.0
        processed_probability = 0.0
        for outcome, probability, members in branches:
            self.stats["branches_evaluated"] += 1
            if outcome == (len(guess), 0):
                success_probability += probability
            elif state.remaining_guesses > 1:
                posterior = self._posterior_for_branch(
                    state.belief,
                    guess,
                    outcome,
                    members,
                    posterior_updater,
                    use_matrix=self._can_use_matrix(
                        state.belief, guess, feedback_engine
                    ),
                )
                next_state = DecisionState(
                    belief=posterior,
                    remaining_guesses=state.remaining_guesses - 1,
                )
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
                if next_success is None or next_expected is None:
                    raise RuntimeError("best child action was unexpectedly pruned")
                success_probability += probability * next_success
                expected_guesses += probability * next_expected
            processed_probability += probability
            if incumbent is not None and self._enabled("branch_and_bound"):
                upper_success = success_probability + max(
                    0.0, 1.0 - processed_probability
                )
                if self._cannot_beat_incumbent(
                    upper_success, expected_guesses, incumbent
                ):
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
        values = self.feedback_matrix.horizon_two_values(
            legal,
            answer_words,
            tuple(mass for _, mass in mass_table),
            legal,
        )
        return tuple(values)

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
    ) -> Tuple[str, ...]:
        legal = tuple(candidate_guesses)
        if not self._enabled("action_ordering"):
            return legal
        mass = dict(self._mass_table(state.belief))
        candidates = sorted(
            (guess for guess in legal if guess in mass),
            key=lambda guess: (-mass[guess], guess),
        )
        probes = sorted(guess for guess in legal if guess not in mass)
        return tuple(candidates + probes)

    def _can_use_matrix(
        self,
        belief: BeliefState,
        guess: str,
        feedback_engine: FeedbackEngine,
    ) -> bool:
        if not self._enabled("matrix_transitions") or self.feedback_matrix is None:
            return False
        if type(feedback_engine) is not HardleFeedbackEngine:
            return False
        if feedback_engine.game_spec.word_length != self.feedback_matrix.word_length:
            return False
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
    ) -> Tuple[Tuple[Feedback, float, Tuple[Tuple[str, float], ...]], ...]:
        if self._can_use_matrix(state.belief, guess, feedback_engine):
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
        if self._enabled("branch_ordering"):
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
