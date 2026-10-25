"""Contracts for evaluation and experiment boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable

from .decision import Policy
from .game import GameSpec


@dataclass(frozen=True)
class BenchmarkSpec:
    """Names a benchmark and its requested episode count."""

    name: str
    episodes: int

    def __post_init__(self) -> None:
        if self.episodes < 0:
            raise ValueError("episodes cannot be negative")


@dataclass(frozen=True)
class MetricsResult:
    """Stores aggregate observations without computing them."""

    episodes: int
    wins: int
    guesses: int

    def __post_init__(self) -> None:
        if self.episodes < 0 or self.wins < 0 or self.guesses < 0:
            raise ValueError("metrics counts cannot be negative")
        if self.wins > self.episodes:
            raise ValueError("wins cannot exceed episodes")


@dataclass(frozen=True)
class ExperimentConfig:
    """Carries game and benchmark configuration into an evaluation run."""

    game: GameSpec
    benchmark: BenchmarkSpec
    run_id: Optional[str] = None


@runtime_checkable
class EpisodeRunner(Protocol):
    """Runs episodes while keeping game semantics outside evaluation."""

    def run(self, config: ExperimentConfig, policy: Policy) -> MetricsResult:
        ...


@runtime_checkable
class ArtifactSink(Protocol):
    """Receives evaluation artifacts at an explicit observation boundary."""

    def write(self, name: str, artifact: object) -> None:
        ...
