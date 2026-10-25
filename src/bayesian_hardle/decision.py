"""Baseline policies and exact finite-horizon Bayes planning."""

from __future__ import annotations

from dataclasses import dataclass
import random
import time
from typing import Dict, Hashable, Optional, Protocol, Sequence, Tuple, runtime_checkable

from .belief import BeliefState, PosteriorUpdater
from .game import Feedback, FeedbackEngine
from .information import (
    ExactInformationGainCalculator,
    ExactOutcomePartitioner,
    InformationGainCalculator,
    OutcomePartitioner,
)


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
    """Chooses the legal guess with maximum exact expected information gain."""

    def __init__(
        self,
        feedback_engine: FeedbackEngine,
        partitioner: Optional[OutcomePartitioner] = None,
        information_gain_calculator: Optional[InformationGainCalculator] = None,
        time_limit_seconds: Optional[float] = None,
    ) -> None:
        if time_limit_seconds is not None and time_limit_seconds <= 0:
            raise ValueError("time_limit_seconds must be positive")
        self.feedback_engine = feedback_engine
        self.partitioner = partitioner or ExactOutcomePartitioner()
        self.information_gain_calculator = (
            information_gain_calculator or ExactInformationGainCalculator()
        )
        self.time_limit_seconds = time_limit_seconds
        self._started_at = None
        self.evaluated_guesses = 0

    def select_guess(self, state: DecisionState, candidate_guesses: Sequence[str]) -> str:
        legal = tuple(candidate_guesses)
        if not legal:
            raise ValueError("candidate_guesses cannot be empty")
        if self._started_at is None:
            self._started_at = time.perf_counter()
        scored = []
        for guess in legal:
            if (
                self.time_limit_seconds is not None
                and time.perf_counter() - self._started_at >= self.time_limit_seconds
            ):
                raise PolicyBudgetExceeded(
                    f"Max-IG budget exceeded after {self.evaluated_guesses} guess evaluations"
                )
            distribution = self.partitioner.partition(
                state.belief, guess, self.feedback_engine
            )
            gain = self.information_gain_calculator.calculate(
                state.belief, guess, distribution
            )
            scored.append((gain, guess))
            self.evaluated_guesses += 1
        return max(scored, key=lambda item: item[0])[1]


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
    """Exact Bellman planner intended for deliberately small vocabularies."""

    def __init__(self, cache: Optional[PlannerCache] = None) -> None:
        self.cache = cache if cache is not None else InMemoryPlannerCache()
        self.cache_hits = 0
        self.cache_misses = 0
        self._value_cache: Dict[Hashable, float] = {}

    @staticmethod
    def _canonical_key(
        state: DecisionState,
        candidate_guesses: Sequence[str],
    ) -> Tuple[object, ...]:
        mass = state.belief.probability_mass
        if not mass:
            uniform = 1.0 / len(state.belief.candidates)
            mass = tuple((word, uniform) for word in state.belief.candidates)
        return (
            state.remaining_guesses,
            tuple(sorted((word, value) for word, value in mass)),
            tuple(candidate_guesses),
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
        return self._guess_value(state, guess, legal, feedback_engine, posterior_updater)

    def _best_guess(
        self,
        state: DecisionState,
        candidate_guesses: Sequence[str],
        feedback_engine: FeedbackEngine,
        posterior_updater: PosteriorUpdater,
    ) -> str:
        key = self._canonical_key(state, candidate_guesses)
        cached = self.cache.get(key)
        if cached is not None:
            self.cache_hits += 1
            return cached
        self.cache_misses += 1
        best_guess = None
        best_value = float("-inf")
        for guess in candidate_guesses:
            value = self._guess_value(
                state, guess, candidate_guesses, feedback_engine, posterior_updater
            )
            if value > best_value + 1e-15:
                best_value = value
                best_guess = guess
        assert best_guess is not None
        self.cache.put(key, best_guess)
        return best_guess

    def _guess_value(
        self,
        state: DecisionState,
        guess: str,
        candidate_guesses: Sequence[str],
        feedback_engine: FeedbackEngine,
        posterior_updater: PosteriorUpdater,
    ) -> float:
        key = ("value", self._canonical_key(state, candidate_guesses), guess)
        if key in self._value_cache:
            return self._value_cache[key]
        mass_table = self._mass_table(state.belief)
        grouped: Dict[Feedback, float] = {}
        for target, mass in mass_table:
            outcome = tuple(feedback_engine.evaluate(guess, target))
            grouped[outcome] = grouped.get(outcome, 0.0) + mass
        value = 0.0
        for outcome, probability in grouped.items():
            if outcome == (len(guess), 0):
                value += probability
            elif state.remaining_guesses > 1:
                posterior = posterior_updater.update(state.belief, guess, outcome)
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
                value += probability * self._guess_value(
                    next_state,
                    next_guess,
                    candidate_guesses,
                    feedback_engine,
                    posterior_updater,
                )
        self._value_cache[key] = value
        return value
