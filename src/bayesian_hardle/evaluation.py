"""Leakage-safe episode evaluation and machine-readable result boundaries."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Any, Optional, Protocol, Sequence, Tuple, runtime_checkable

from .belief import PosteriorUpdater, PriorModel
from .decision import BayesOptimalPlanner, DecisionState, Policy, PolicyBudgetExceeded
from .game import FeedbackEngine, GameSpec, TerminalRules, VocabularyRepository


@dataclass(frozen=True)
class BenchmarkSpec:
    """Names a benchmark and its requested number of hidden-target episodes."""

    name: str
    episodes: int
    seed: int = 0

    def __post_init__(self) -> None:
        if self.episodes < 0:
            raise ValueError("episodes cannot be negative")


@dataclass(frozen=True)
class MetricsResult:
    """Aggregate episode observations with explicit secondary metrics."""

    episodes: int
    wins: int
    guesses: int
    per_episode_guesses: Tuple[int, ...] = ()
    runtime_seconds: float = 0.0
    scope: str = ""
    seed: Optional[int] = None
    requested_episodes: Optional[int] = None
    stopped_reason: Optional[str] = None

    def __post_init__(self) -> None:
        if self.episodes < 0 or self.wins < 0 or self.guesses < 0:
            raise ValueError("metrics counts cannot be negative")
        if self.wins > self.episodes:
            raise ValueError("wins cannot exceed episodes")
        if self.requested_episodes is not None and self.requested_episodes < self.episodes:
            raise ValueError("requested_episodes cannot be below completed episodes")
        if self.per_episode_guesses and len(self.per_episode_guesses) != self.episodes:
            raise ValueError("per_episode_guesses must have one value per episode")
        if any(value < 0 for value in self.per_episode_guesses):
            raise ValueError("per-episode guesses cannot be negative")

    @property
    def solve_rate(self) -> float:
        return self.wins / self.episodes if self.episodes else 0.0

    @property
    def mean_guesses(self) -> float:
        return self.guesses / self.episodes if self.episodes else 0.0

    @property
    def mean_guesses_solved(self) -> Optional[float]:
        if not self.per_episode_guesses or not self.wins:
            return None
        return sum(self.per_episode_guesses[: self.wins]) / self.wins

    def as_dict(self) -> dict[str, Any]:
        return {
            "episodes": self.episodes,
            "wins": self.wins,
            "solve_rate": self.solve_rate,
            "total_guesses": self.guesses,
            "mean_guesses": self.mean_guesses,
            "per_episode_guesses": list(self.per_episode_guesses),
            "runtime_seconds": self.runtime_seconds,
            "scope": self.scope,
            "seed": self.seed,
            "requested_episodes": self.requested_episodes,
            "completed_episodes": self.episodes,
            "stopped_reason": self.stopped_reason,
        }


@dataclass(frozen=True)
class ExperimentConfig:
    """Carries game and benchmark configuration into an evaluation run."""

    game: GameSpec
    benchmark: BenchmarkSpec
    run_id: Optional[str] = None


@runtime_checkable
class EpisodeRunner(Protocol):
    """Runs episodes while keeping hidden targets outside policy state."""

    def run(self, config: ExperimentConfig, policy: Policy) -> MetricsResult:
        ...


class PlannerPolicyAdapter:
    """Adapts the planner contract to the ordinary episode policy contract."""

    def __init__(
        self,
        planner: BayesOptimalPlanner,
        feedback_engine: FeedbackEngine,
        posterior_updater: PosteriorUpdater,
    ) -> None:
        self.planner = planner
        self.feedback_engine = feedback_engine
        self.posterior_updater = posterior_updater

    def select_guess(self, state: DecisionState, candidate_guesses: Sequence[str]) -> str:
        return self.planner.select_guess(
            state,
            candidate_guesses,
            self.feedback_engine,
            self.posterior_updater,
        )


class ExactEpisodeRunner:
    """Runs deterministic target episodes with target membership hidden from policies."""

    def __init__(
        self,
        vocabulary: VocabularyRepository,
        feedback_engine: FeedbackEngine,
        prior_model: PriorModel,
        posterior_updater: PosteriorUpdater,
        terminal_rules: TerminalRules,
        hidden_targets: Optional[Sequence[str]] = None,
    ) -> None:
        self.vocabulary = vocabulary
        self.feedback_engine = feedback_engine
        self.prior_model = prior_model
        self.posterior_updater = posterior_updater
        self.terminal_rules = terminal_rules
        candidate_answers = tuple(vocabulary.target_vocabulary())
        targets = tuple(hidden_targets) if hidden_targets is not None else candidate_answers
        if not targets:
            raise ValueError("hidden target pool cannot be empty")
        if not set(targets).issubset(set(candidate_answers)):
            raise ValueError("hidden targets must be drawn from the evaluation vocabulary")
        self._hidden_targets = targets

    def run(self, config: ExperimentConfig, policy: Policy) -> MetricsResult:
        start = time.perf_counter()
        legal_guesses = tuple(self.vocabulary.legal_guesses())
        candidate_answers = tuple(self.vocabulary.target_vocabulary())
        target_pool = self._hidden_targets
        per_episode = []
        wins = 0
        stopped_reason = None
        for episode_index in range(config.benchmark.episodes):
            hidden_target = target_pool[episode_index % len(target_pool)]
            belief = self.prior_model.initial_belief(candidate_answers)
            state = DecisionState(belief=belief, remaining_guesses=config.game.max_guesses)
            episode_guesses = 0
            solved = False
            while state.remaining_guesses > 0:
                try:
                    guess = policy.select_guess(state, legal_guesses)
                except PolicyBudgetExceeded as exc:
                    stopped_reason = str(exc)
                    break
                if stopped_reason is not None:
                    break
                episode_guesses += 1
                feedback = self.feedback_engine.evaluate(guess, hidden_target)
                if self.terminal_rules.is_terminal(
                    guess, feedback, episode_guesses, config.game
                ):
                    solved = feedback == (config.game.word_length, 0)
                    break
                belief = self.posterior_updater.update(belief, guess, feedback)
                state = DecisionState(
                    belief=belief,
                    remaining_guesses=config.game.max_guesses - episode_guesses,
                )
            if stopped_reason is not None:
                break
            per_episode.append(episode_guesses)
            wins += int(solved)
        return MetricsResult(
            episodes=len(per_episode),
            wins=wins,
            guesses=sum(per_episode),
            per_episode_guesses=tuple(per_episode),
            runtime_seconds=time.perf_counter() - start,
            scope=config.benchmark.name,
            seed=config.benchmark.seed,
            requested_episodes=config.benchmark.episodes,
            stopped_reason=stopped_reason,
        )


@runtime_checkable
class ArtifactSink(Protocol):
    """Receives evaluation artifacts at an explicit observation boundary."""

    def write(self, name: str, artifact: object) -> None:
        ...


class JsonArtifactSink:
    """Writes named JSON artifacts below one explicit result directory."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def write(self, name: str, artifact: object) -> None:
        path = self.directory / name
        if path.suffix != ".json":
            path = path.with_suffix(".json")
        if hasattr(artifact, "as_dict"):
            artifact = artifact.as_dict()
        path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
