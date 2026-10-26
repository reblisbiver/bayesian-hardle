"""Reusable solver and interactive session services for CLI and GUI clients."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import random
import time
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from .accelerated import ExactFeedbackCodeMatrix, MatrixPosteriorUpdater
from .belief import ExactPosteriorUpdater
from .decision import DecisionState, MAPPolicy, MaxInformationGainPolicy, Policy, RandomPolicy
from .fairness import GeneralEnglishFrequencyPrior, HypothesisMode, resolve_hypothesis_mode
from .game import (
    Feedback,
    GameSpec,
    HardleFeedbackEngine,
    HardleTerminalRules,
    VocabularyRepository,
    WordListVocabularyRepository,
)
from .information import ShannonEntropyCalculator


MODE_NAMES = ("full-uniform", "full-frequency", "curated-2315")
POLICY_NAMES = ("random", "map", "max-ig")


@dataclass(frozen=True)
class TurnResult:
    turn: int
    mode: str
    mode_label: str
    policy: str
    guess: str
    feedback: Optional[Feedback]
    remaining_candidates: int
    entropy_bits: float
    decision_ms: float
    cumulative_time_ms: float
    top_candidates: Tuple[Tuple[str, float], ...]
    status: str

    def as_dict(self) -> Dict[str, object]:
        return {
            "turn": self.turn,
            "mode": self.mode,
            "mode_label": self.mode_label,
            "policy": self.policy,
            "guess": self.guess,
            "feedback": list(self.feedback) if self.feedback is not None else None,
            "remaining_candidates": self.remaining_candidates,
            "entropy_bits": self.entropy_bits,
            "decision_ms": self.decision_ms,
            "cumulative_time_ms": self.cumulative_time_ms,
            "top_candidates": [
                {"word": word, "probability": probability}
                for word, probability in self.top_candidates
            ],
            "status": self.status,
        }


@dataclass(frozen=True)
class SimulationResult:
    mode: HypothesisMode
    policy_name: str
    target: str
    solved: bool
    turns: Tuple[TurnResult, ...]
    total_time_ms: float

    def as_dict(self) -> Dict[str, object]:
        return {
            "mode": self.mode.name,
            "mode_label": self.mode.label,
            "policy": self.policy_name,
            "target": self.target,
            "solved": self.solved,
            "total_time_ms": self.total_time_ms,
            "turns": [turn.as_dict() for turn in self.turns],
        }


@dataclass
class SolverContext:
    vocabulary: VocabularyRepository
    mode: HypothesisMode
    feedback: HardleFeedbackEngine
    terminal: HardleTerminalRules
    policy: Policy
    posterior_updater: object
    legal_guesses: Tuple[str, ...]
    policy_name: str
    matrix: Optional[ExactFeedbackCodeMatrix] = None


@dataclass(frozen=True)
class HumanTurn:
    turn: int
    guess: str
    feedback: Feedback
    status: str


@dataclass(frozen=True)
class BattlePublicState:
    """The only state the UI is allowed to render for a battle."""

    mode: str
    mode_label: str
    policy_name: str
    max_guesses: int
    human_turns: Tuple[HumanTurn, ...]
    finished: bool
    human_solved: bool
    gave_up: bool
    target: Optional[str]
    solver_turns: Tuple[TurnResult, ...]
    solver_solved: Optional[bool]


@dataclass(frozen=True)
class HumanTurnResult:
    turn: int
    feedback: Feedback
    finished: bool
    public_state: BattlePublicState


@dataclass(frozen=True)
class BattleOutcome(BattlePublicState):
    """Finished battle view; fields are inherited for a stable public shape."""


def _default_repository_root() -> Path:
    candidates = [Path.cwd(), Path(__file__).parents[2]]
    for candidate in candidates:
        if (candidate / "data" / "wordlists").is_dir():
            return candidate
    raise RuntimeError(
        "cannot find repository root; run the client from the repository root "
        "or pass --repository-root"
    )


def _top_candidates(belief, count: int = 5) -> Tuple[Tuple[str, float], ...]:
    if belief.probability_mass:
        total = belief.total_mass
        masses = [(word, mass / total) for word, mass in belief.probability_mass]
    else:
        mass = 1.0 / len(belief.candidates)
        masses = [(word, mass) for word in belief.candidates]
    ranked = sorted(enumerate(masses), key=lambda item: (-item[1][1], item[0]))
    return tuple(item[1] for item in ranked[:count])


def make_solver_context(
    mode_name: str,
    policy_name: str,
    cache_dir: Path = Path(".cache/bayesian_hardle"),
    seed: int = 0,
    use_cache: bool = True,
    frequency_prior: Optional[GeneralEnglishFrequencyPrior] = None,
    repository_root: Optional[Path] = None,
    vocabulary: Optional[VocabularyRepository] = None,
    max_guesses: int = 10,
) -> SolverContext:
    if max_guesses <= 0:
        raise ValueError("max_guesses must be positive")
    root = repository_root or _default_repository_root()
    resolved_vocabulary = vocabulary or WordListVocabularyRepository.from_repository_root(root)
    mode = resolve_hypothesis_mode(
        mode_name,
        resolved_vocabulary,
        frequency_prior=frequency_prior,
    )
    feedback = HardleFeedbackEngine(GameSpec(word_length=5, max_guesses=max_guesses))
    legal = tuple(resolved_vocabulary.legal_guesses())
    matrix = None
    if policy_name == "max-ig":
        if use_cache:
            matrix = ExactFeedbackCodeMatrix.load_or_build(
                legal,
                mode.support,
                cache_dir=cache_dir,
            )
        else:
            matrix = ExactFeedbackCodeMatrix.from_vocabulary(legal, mode.support)
        policy = MaxInformationGainPolicy(feedback, feedback_matrix=matrix)
        updater = MatrixPosteriorUpdater(matrix)
    elif policy_name == "map":
        policy = MAPPolicy()
        updater = ExactPosteriorUpdater(feedback)
    elif policy_name == "random":
        policy = RandomPolicy(seed=seed)
        updater = ExactPosteriorUpdater(feedback)
    else:
        raise ValueError(f"unknown policy: {policy_name}")
    return SolverContext(
        vocabulary=resolved_vocabulary,
        mode=mode,
        feedback=feedback,
        terminal=HardleTerminalRules(),
        policy=policy,
        posterior_updater=updater,
        legal_guesses=legal,
        policy_name=policy_name,
        matrix=matrix,
    )


def _build_turn(
    context: SolverContext,
    state: DecisionState,
    turn_number: int,
    guess: str,
    feedback: Optional[Feedback],
    decision_ms: float,
    cumulative_time_ms: float,
    status: str,
) -> TurnResult:
    return TurnResult(
        turn=turn_number,
        mode=context.mode.name,
        mode_label=context.mode.label,
        policy=context.policy_name,
        guess=guess,
        feedback=feedback,
        remaining_candidates=len(state.belief.candidates),
        entropy_bits=ShannonEntropyCalculator().calculate(state.belief),
        decision_ms=decision_ms,
        cumulative_time_ms=cumulative_time_ms,
        top_candidates=_top_candidates(state.belief),
        status=status,
    )


class SolverSession:
    """One exact, stepwise solver run against a known hidden target."""

    def __init__(
        self,
        context: SolverContext,
        target: str,
        max_guesses: int = 10,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        if max_guesses <= 0:
            raise ValueError("max_guesses must be positive")
        normalised = target.strip().lower()
        if normalised not in context.legal_guesses:
            raise ValueError(
                f"target {normalised!r} is not in the legal 12,974-word vocabulary"
            )
        if normalised not in context.mode.support:
            raise ValueError(
                f"target {normalised!r} is outside {context.mode.label}; "
                "use a full-support mode for this target"
            )
        self._context = context
        self._target = normalised
        self._max_guesses = max_guesses
        self._clock = clock
        self._state = DecisionState(
            context.mode.prior.initial_belief(context.mode.support),
            max_guesses,
        )
        self._turns: List[TurnResult] = []
        self._solved = False
        self._finished = False
        self._cumulative_time_ms = 0.0

    @property
    def turns(self) -> Tuple[TurnResult, ...]:
        return tuple(self._turns)

    @property
    def solved(self) -> bool:
        return self._solved

    @property
    def finished(self) -> bool:
        return self._finished

    def step(self) -> TurnResult:
        if self._finished:
            raise RuntimeError("solver session is already finished")
        turn_number = len(self._turns) + 1
        decision_started = self._clock()
        guess = self._context.policy.select_guess(
            self._state,
            self._context.legal_guesses,
        )
        decision_ms = (self._clock() - decision_started) * 1000.0
        observed = self._context.feedback.evaluate(guess, self._target)
        self._solved = observed == (5, 0)
        belief = self._context.posterior_updater.update(
            self._state.belief,
            guess,
            observed,
        )
        current_state = DecisionState(belief, self._max_guesses - turn_number)
        if self._solved:
            status = "SOLVED"
        elif turn_number >= self._max_guesses:
            status = "HORIZON_REACHED"
        else:
            status = "CONTINUE"
        self._cumulative_time_ms += decision_ms
        result = _build_turn(
            self._context,
            current_state,
            turn_number,
            guess,
            observed,
            decision_ms,
            self._cumulative_time_ms,
            status,
        )
        self._turns.append(result)
        self._state = current_state
        self._finished = self._solved or status == "HORIZON_REACHED"
        return result

    def run(
        self,
        on_turn: Optional[Callable[[TurnResult], None]] = None,
    ) -> SimulationResult:
        started = self._clock()
        while not self._finished:
            result = self.step()
            if on_turn is not None:
                on_turn(result)
        return SimulationResult(
            mode=self._context.mode,
            policy_name=self._context.policy_name,
            target=self._target,
            solved=self._solved,
            turns=self.turns,
            total_time_ms=(self._clock() - started) * 1000.0,
        )


def run_simulation(
    target: str,
    mode_name: str,
    policy_name: str,
    max_guesses: int = 10,
    seed: int = 0,
    cache_dir: Path = Path(".cache/bayesian_hardle"),
    use_cache: bool = True,
    on_turn: Optional[Callable[[TurnResult], None]] = None,
    frequency_prior: Optional[GeneralEnglishFrequencyPrior] = None,
    repository_root: Optional[Path] = None,
    vocabulary: Optional[VocabularyRepository] = None,
) -> SimulationResult:
    context = make_solver_context(
        mode_name,
        policy_name,
        cache_dir=cache_dir,
        seed=seed,
        use_cache=use_cache,
        frequency_prior=frequency_prior,
        repository_root=repository_root,
        vocabulary=vocabulary,
        max_guesses=max_guesses,
    )
    return SolverSession(context, target, max_guesses=max_guesses).run(on_turn=on_turn)


class BattleSession:
    """Human game plus a hidden parallel solver, with explicit redaction."""

    def __init__(
        self,
        mode_name: str,
        policy_name: str,
        max_guesses: int = 10,
        seed: int = 0,
        cache_dir: Path = Path(".cache/bayesian_hardle"),
        use_cache: bool = True,
        frequency_prior: Optional[GeneralEnglishFrequencyPrior] = None,
        repository_root: Optional[Path] = None,
        vocabulary: Optional[VocabularyRepository] = None,
        rng: Optional[random.Random] = None,
        target: Optional[str] = None,
    ) -> None:
        context = make_solver_context(
            mode_name,
            policy_name,
            cache_dir=cache_dir,
            seed=seed,
            use_cache=use_cache,
            frequency_prior=frequency_prior,
            repository_root=repository_root,
            vocabulary=vocabulary,
            max_guesses=max_guesses,
        )
        chooser = rng or random.Random()
        selected_target = (target or chooser.choice(tuple(context.mode.support))).strip().lower()
        if selected_target not in context.mode.support:
            raise ValueError(
                f"target {selected_target!r} is outside {context.mode.label}; "
                "battle targets must come from the selected support"
            )
        self._context = context
        self._max_guesses = max_guesses
        self._target = selected_target
        self._solver = SolverSession(context, selected_target, max_guesses=max_guesses)
        self._human_turns: List[HumanTurn] = []
        self._finished = False
        self._human_solved = False
        self._gave_up = False

    def _complete_solver(self) -> None:
        while not self._solver.finished:
            self._solver.step()

    def _finish(self, human_solved: bool = False, gave_up: bool = False) -> None:
        self._human_solved = human_solved
        self._gave_up = gave_up
        self._finished = True
        self._complete_solver()

    def public_state(self) -> BattlePublicState:
        if self._finished:
            return BattleOutcome(
                mode=self._context.mode.name,
                mode_label=self._context.mode.label,
                policy_name=self._context.policy_name,
                max_guesses=self._max_guesses,
                human_turns=tuple(self._human_turns),
                finished=True,
                human_solved=self._human_solved,
                gave_up=self._gave_up,
                target=self._target,
                solver_turns=self._solver.turns,
                solver_solved=self._solver.solved,
            )
        return BattlePublicState(
            mode=self._context.mode.name,
            mode_label=self._context.mode.label,
            policy_name=self._context.policy_name,
            max_guesses=self._max_guesses,
            human_turns=tuple(self._human_turns),
            finished=False,
            human_solved=False,
            gave_up=False,
            target=None,
            solver_turns=(),
            solver_solved=None,
        )

    def submit_human_guess(self, guess: str) -> HumanTurnResult:
        if self._finished:
            raise RuntimeError("battle is already finished")
        if not isinstance(guess, str):
            raise TypeError("guess must be a string")
        normalised = guess.strip().lower()
        if normalised not in self._context.legal_guesses:
            raise ValueError(f"guess {normalised!r} is not a legal five-letter word")
        turn_number = len(self._human_turns) + 1
        feedback = self._context.feedback.evaluate(normalised, self._target)
        human_solved = feedback == (5, 0)
        if human_solved:
            status = "SOLVED"
        elif turn_number >= self._max_guesses:
            status = "HORIZON_REACHED"
        else:
            status = "CONTINUE"
        self._human_turns.append(HumanTurn(turn_number, normalised, feedback, status))
        if not self._solver.finished:
            self._solver.step()
        if human_solved or status == "HORIZON_REACHED":
            self._finish(human_solved=human_solved)
        public_state = self.public_state()
        return HumanTurnResult(
            turn=turn_number,
            feedback=feedback,
            finished=public_state.finished,
            public_state=public_state,
        )

    def give_up(self) -> BattleOutcome:
        if not self._finished:
            self._finish(gave_up=True)
        return self.public_state()  # type: ignore[return-value]


__all__ = [
    "MODE_NAMES",
    "POLICY_NAMES",
    "BattleOutcome",
    "BattlePublicState",
    "BattleSession",
    "HumanTurn",
    "HumanTurnResult",
    "SimulationResult",
    "SolverContext",
    "SolverSession",
    "TurnResult",
    "make_solver_context",
    "run_simulation",
]
