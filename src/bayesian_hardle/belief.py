"""Contracts and state for the Bayesian belief boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence, Tuple, runtime_checkable


@dataclass(frozen=True)
class BeliefState:
    """Immutable belief boundary with no posterior representation chosen yet."""

    candidates: Tuple[str, ...] = ()
    observations: Tuple[object, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidates", tuple(self.candidates))
        object.__setattr__(self, "observations", tuple(self.observations))


@runtime_checkable
class PriorModel(Protocol):
    """Constructs an initial belief from the target vocabulary."""

    def initial_belief(self, target_vocabulary: Sequence[str]) -> BeliefState:
        ...


@runtime_checkable
class LikelihoodModel(Protocol):
    """Provides a likelihood contract without choosing a numeric model."""

    def likelihood(
        self,
        target: str,
        guess: str,
        feedback: Sequence[str],
    ) -> float:
        ...


@runtime_checkable
class PosteriorUpdater(Protocol):
    """Updates a belief after one observed guess and feedback value."""

    def update(
        self,
        belief: BeliefState,
        guess: str,
        feedback: Sequence[str],
    ) -> BeliefState:
        ...
