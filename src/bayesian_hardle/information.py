"""Exact outcome partitions, Shannon entropy, and information gain."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Dict, Iterable, Protocol, Tuple, runtime_checkable

from .belief import BeliefState, ExactPosteriorUpdater, PosteriorUpdater
from .game import Feedback, FeedbackEngine


@dataclass(frozen=True)
class OutcomeBranch:
    """A feedback outcome, its prior probability, and its posterior belief."""

    outcome: Feedback
    probability: float
    posterior: BeliefState


@dataclass(frozen=True)
class OutcomeDistribution:
    """Immutable collection of possible feedback/posterior branches."""

    outcomes: Tuple[OutcomeBranch, ...] = ()

    def __post_init__(self) -> None:
        outcomes = tuple(self.outcomes)
        if any(branch.probability < 0 for branch in outcomes):
            raise ValueError("outcome probabilities must be non-negative")
        object.__setattr__(self, "outcomes", outcomes)

    @property
    def total_probability(self) -> float:
        return sum(branch.probability for branch in self.outcomes)


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


class ExactOutcomePartitioner:
    """Groups all candidate answers by exact deterministic feedback."""

    def __init__(self, posterior_updater: PosteriorUpdater | None = None) -> None:
        self.posterior_updater = posterior_updater

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

    def partition(
        self,
        belief: BeliefState,
        guess: str,
        feedback_engine: FeedbackEngine,
    ) -> OutcomeDistribution:
        mass_table = self._mass_table(belief)
        grouped: Dict[Feedback, list[Tuple[str, float]]] = {}
        for target, mass in mass_table:
            outcome = tuple(feedback_engine.evaluate(guess, target))
            grouped.setdefault(outcome, []).append((target, mass))
        branches = []
        for outcome, members in grouped.items():
            probability = sum(mass for _, mass in members)
            if self.posterior_updater is not None:
                posterior = self.posterior_updater.update(belief, guess, outcome)
            else:
                normalized = tuple(
                    (target, mass / probability) for target, mass in members
                )
                posterior = BeliefState(
                    candidates=tuple(target for target, _ in normalized),
                    observations=belief.observations + ((guess, outcome),),
                    probability_mass=normalized,
                )
            branches.append(OutcomeBranch(outcome, probability, posterior))
        return OutcomeDistribution(tuple(branches))


@runtime_checkable
class EntropyCalculator(Protocol):
    """Calculates Shannon entropy for the supplied belief state."""

    def calculate(self, belief: BeliefState) -> float:
        ...


class ShannonEntropyCalculator:
    """Computes ``H(b) = -sum_w b(w) log2 b(w)``."""

    def calculate(self, belief: BeliefState) -> float:
        if belief.probability_mass:
            total = belief.total_mass
            if total <= 0:
                raise ValueError("belief must have positive total mass")
            probabilities = (mass / total for _, mass in belief.probability_mass)
        elif belief.candidates:
            uniform = 1.0 / len(belief.candidates)
            probabilities = (uniform for _ in belief.candidates)
        else:
            raise ValueError("belief must contain candidates")
        return -sum(
            probability * math.log2(probability)
            for probability in probabilities
            if probability > 0
        )


@runtime_checkable
class ExpectedEntropyCalculator(Protocol):
    """Calculates expected posterior entropy for an outcome distribution."""

    def calculate(self, distribution: OutcomeDistribution) -> float:
        ...


class ExpectedPosteriorEntropyCalculator:
    """Computes the probability-weighted entropy of all feedback branches."""

    def __init__(self, entropy_calculator: EntropyCalculator | None = None) -> None:
        self.entropy_calculator = entropy_calculator or ShannonEntropyCalculator()

    def calculate(self, distribution: OutcomeDistribution) -> float:
        total = distribution.total_probability
        if not distribution.outcomes:
            raise ValueError("outcome distribution cannot be empty")
        if not math.isclose(total, 1.0, rel_tol=1e-10, abs_tol=1e-10):
            raise ValueError("outcome probabilities must sum to one")
        return sum(
            branch.probability * self.entropy_calculator.calculate(branch.posterior)
            for branch in distribution.outcomes
        )


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


class ExactInformationGainCalculator:
    """Computes current entropy minus expected posterior entropy."""

    def __init__(
        self,
        entropy_calculator: EntropyCalculator | None = None,
        expected_entropy_calculator: ExpectedEntropyCalculator | None = None,
    ) -> None:
        self.entropy_calculator = entropy_calculator or ShannonEntropyCalculator()
        self.expected_entropy_calculator = (
            expected_entropy_calculator or ExpectedPosteriorEntropyCalculator(self.entropy_calculator)
        )

    def calculate(
        self,
        belief: BeliefState,
        guess: str,
        outcome_distribution: OutcomeDistribution,
    ) -> float:
        del guess
        gain = self.entropy_calculator.calculate(belief) - self.expected_entropy_calculator.calculate(
            outcome_distribution
        )
        return max(0.0, gain)
