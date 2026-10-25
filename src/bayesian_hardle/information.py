"""Contracts for partitioning outcomes and measuring information."""

from __future__ import annotations

from typing import Mapping, Protocol

from .belief import BeliefState
from .game import FeedbackEngine


class OutcomePartitioner(Protocol):
    """Partitions a belief through the shared feedback boundary."""

    def partition(
        self,
        belief: BeliefState,
        guess: str,
        feedback_engine: FeedbackEngine,
    ) -> Mapping[object, BeliefState]:
        ...


class EntropyCalculator(Protocol):
    """Calculates entropy for a supplied outcome partition."""

    def calculate(self, partition: Mapping[object, BeliefState]) -> float:
        ...


class ExpectedEntropyCalculator(Protocol):
    """Calculates expected entropy for a supplied belief and partition."""

    def calculate(
        self,
        belief: BeliefState,
        partition: Mapping[object, BeliefState],
    ) -> float:
        ...


class InformationGainCalculator(Protocol):
    """Calculates information gain through shared component contracts."""

    def calculate(
        self,
        belief: BeliefState,
        guess: str,
        feedback_engine: FeedbackEngine,
    ) -> float:
        ...
