"""Contracts for partitioning outcomes and measuring information."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Tuple, runtime_checkable

from .belief import BeliefState
from .game import FeedbackEngine


@dataclass(frozen=True)
class OutcomeBranch:
    """Opaque feedback outcome with its probability and resulting belief."""

    outcome: object
    probability: float
    posterior: BeliefState


@dataclass(frozen=True)
class OutcomeDistribution:
    """Immutable collection of possible feedback/posterior branches."""

    outcomes: Tuple[OutcomeBranch, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "outcomes", tuple(self.outcomes))


@runtime_checkable
class OutcomePartitioner(Protocol):
    """Partitions a belief through the shared feedback boundary."""

    def partition(
        self,
        belief: BeliefState,
        guess: str,
        feedback_engine: FeedbackEngine,
    ) -> OutcomeDistribution:
        ...


@runtime_checkable
class EntropyCalculator(Protocol):
    """Calculates entropy for the supplied belief state."""

    def calculate(self, belief: BeliefState) -> float:
        ...


@runtime_checkable
class ExpectedEntropyCalculator(Protocol):
    """Calculates expected posterior entropy for an outcome distribution."""

    def calculate(self, distribution: OutcomeDistribution) -> float:
        ...


@runtime_checkable
class InformationGainCalculator(Protocol):
    """Calculates information gain through shared component contracts."""

    def calculate(
        self,
        belief: BeliefState,
        guess: str,
        outcome_distribution: OutcomeDistribution,
    ) -> float:
        ...
