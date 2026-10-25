"""Contracts for decision policies and planner caching."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Optional, Protocol, Sequence, runtime_checkable

from .belief import BeliefState


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
    """Selects a guess from candidates supplied by the game model."""

    def select_guess(
        self,
        state: DecisionState,
        candidate_guesses: Sequence[str],
    ) -> str:
        ...


class RandomPolicy:
    """Placeholder for a future random baseline."""

    def select_guess(
        self,
        state: DecisionState,
        candidate_guesses: Sequence[str],
    ) -> str:
        raise NotImplementedError("RandomPolicy is scaffold-only")


class MAPPolicy:
    """Placeholder for a future maximum-a-posteriori policy."""

    def select_guess(
        self,
        state: DecisionState,
        candidate_guesses: Sequence[str],
    ) -> str:
        raise NotImplementedError("MAPPolicy is scaffold-only")


class MaxInformationGainPolicy:
    """Placeholder for a future information-gain policy."""

    def select_guess(
        self,
        state: DecisionState,
        candidate_guesses: Sequence[str],
    ) -> str:
        raise NotImplementedError("MaxInformationGainPolicy is scaffold-only")


@runtime_checkable
class BayesOptimalPlanner(Protocol):
    """Plans through the shared decision state and candidate boundary."""

    def select_guess(
        self,
        state: DecisionState,
        candidate_guesses: Sequence[str],
    ) -> str:
        ...


@runtime_checkable
class PlannerCache(Protocol):
    """Stores planner results without prescribing a cache representation."""

    def get(self, key: Hashable) -> Optional[str]:
        ...

    def put(self, key: Hashable, guess: str) -> None:
        ...
