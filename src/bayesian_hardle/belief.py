"""Exact uniform prior and deterministic posterior filtering."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Protocol, Sequence, Tuple, runtime_checkable

from .game import Feedback, FeedbackEngine


ProbabilityMass = Tuple[Tuple[str, float], ...]


@dataclass(frozen=True)
class BeliefState:
    """Immutable posterior mass over the candidate-answer hypothesis space."""

    candidates: Tuple[str, ...] = ()
    observations: Tuple[object, ...] = ()
    probability_mass: ProbabilityMass = ()

    def __post_init__(self) -> None:
        candidates = tuple(self.candidates)
        observations = tuple(self.observations)
        mass = tuple((word, float(value)) for word, value in self.probability_mass)
        if mass and not candidates:
            candidates = tuple(word for word, _ in mass)
        if len(set(candidates)) != len(candidates):
            raise ValueError("belief candidates must be unique")
        if mass:
            if len({word for word, _ in mass}) != len(mass):
                raise ValueError("belief probability-mass keys must be unique")
            if set(candidates) != {word for word, _ in mass}:
                raise ValueError("belief candidates and probability mass must agree")
            if any(value < 0 or not math.isfinite(value) for _, value in mass):
                raise ValueError("belief masses must be finite and non-negative")
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "observations", observations)
        object.__setattr__(self, "probability_mass", mass)

    @property
    def total_mass(self) -> float:
        return math.fsum(value for _, value in self.probability_mass)

    def mass_for(self, word: str) -> float:
        for candidate, value in self.probability_mass:
            if candidate == word:
                return value
        return 0.0


@runtime_checkable
class PriorModel(Protocol):
    """Constructs an initial belief from the target vocabulary."""

    def initial_belief(self, target_vocabulary: Sequence[str]) -> BeliefState:
        ...


class UniformPrior:
    """Uniform prior over exactly the supplied candidate answers."""

    def initial_belief(self, target_vocabulary: Sequence[str]) -> BeliefState:
        candidates = tuple(target_vocabulary)
        if not candidates:
            raise ValueError("target vocabulary cannot be empty")
        if len(set(candidates)) != len(candidates):
            raise ValueError("target vocabulary must not contain duplicates")
        mass = 1.0 / len(candidates)
        return BeliefState(
            candidates=candidates,
            probability_mass=tuple((word, mass) for word in candidates),
        )


@runtime_checkable
class LikelihoodModel(Protocol):
    """Provides a likelihood contract for an observed feedback value."""

    def likelihood(
        self,
        target: str,
        guess: str,
        feedback: Feedback,
    ) -> float:
        ...


class DeterministicLikelihoodModel:
    """Likelihood 1 for exact feedback and 0 for every other observation."""

    def __init__(self, feedback_engine: FeedbackEngine) -> None:
        self.feedback_engine = feedback_engine

    def likelihood(self, target: str, guess: str, feedback: Feedback) -> float:
        return 1.0 if self.feedback_engine.evaluate(guess, target) == tuple(feedback) else 0.0


class ImpossibleObservationError(ValueError):
    """Raised when an observation has zero posterior probability."""


@runtime_checkable
class PosteriorUpdater(Protocol):
    """Updates a belief after one observed guess and feedback value."""

    def update(
        self,
        belief: BeliefState,
        guess: str,
        feedback: Feedback,
    ) -> BeliefState:
        ...


class ExactPosteriorUpdater:
    """Filters candidate answers by shared deterministic feedback semantics."""

    def __init__(self, feedback_engine: FeedbackEngine) -> None:
        self.feedback_engine = feedback_engine

    @staticmethod
    def _mass_table(belief: BeliefState) -> ProbabilityMass:
        if belief.probability_mass:
            total = belief.total_mass
            if total <= 0:
                raise ValueError("belief must have positive total mass")
            return belief.probability_mass
        if not belief.candidates:
            raise ValueError("belief must contain candidates")
        uniform = 1.0 / len(belief.candidates)
        return tuple((word, uniform) for word in belief.candidates)

    def update(
        self,
        belief: BeliefState,
        guess: str,
        feedback: Feedback,
    ) -> BeliefState:
        observed = tuple(feedback)
        mass_table = self._mass_table(belief)
        retained = [
            (target, mass)
            for target, mass in mass_table
            if self.feedback_engine.evaluate(guess, target) == observed
        ]
        retained_mass = sum(mass for _, mass in retained)
        if retained_mass <= 0:
            raise ImpossibleObservationError(
                "observation has zero posterior mass: " + repr(observed)
            )
        normalized = tuple(
            (target, mass / retained_mass) for target, mass in retained
        )
        return BeliefState(
            candidates=tuple(target for target, _ in normalized),
            observations=belief.observations + ((guess, observed),),
            probability_mass=normalized,
        )
