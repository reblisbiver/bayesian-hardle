"""Interactive acceptance client for the fair full-support Hardle solver."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import random
import sys
import time
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from .accelerated import ExactFeedbackCodeMatrix, MatrixPosteriorUpdater
from .belief import ExactPosteriorUpdater, ImpossibleObservationError
from .decision import DecisionState, MAPPolicy, MaxInformationGainPolicy, Policy, RandomPolicy
from .fairness import (
    GeneralEnglishFrequencyPrior,
    HypothesisMode,
    resolve_hypothesis_mode,
)
from .game import (
    Feedback,
    GameSpec,
    HardleFeedbackEngine,
    HardleTerminalRules,
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
    vocabulary: WordListVocabularyRepository
    mode: HypothesisMode
    feedback: HardleFeedbackEngine
    terminal: HardleTerminalRules
    policy: Policy
    posterior_updater: object
    legal_guesses: Tuple[str, ...]
    policy_name: str
    matrix: Optional[ExactFeedbackCodeMatrix] = None


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
    return tuple(
        sorted(enumerate(masses), key=lambda item: (-item[1][1], item[0]))[index][1]
        for index in range(min(count, len(masses)))
    )


def _format_turn(turn: TurnResult) -> str:
    feedback = "unknown" if turn.feedback is None else str(turn.feedback)
    top = ", ".join(
        f"{word}:{probability:.6g}" for word, probability in turn.top_candidates
    )
    return (
        f"TURN {turn.turn} | mode={turn.mode_label} | policy={turn.policy}\n"
        f"  guess={turn.guess} feedback={feedback} "
        f"remaining_candidates={turn.remaining_candidates} "
        f"entropy_bits={turn.entropy_bits:.6f} decision_ms={turn.decision_ms:.3f}\n"
        f"  top_candidates={top}\n"
        f"  status={turn.status}"
    )


def _make_context(
    mode_name: str,
    policy_name: str,
    cache_dir: Path,
    seed: int,
    use_cache: bool = True,
    frequency_prior: Optional[GeneralEnglishFrequencyPrior] = None,
    repository_root: Optional[Path] = None,
) -> SolverContext:
    root = repository_root or _default_repository_root()
    vocabulary = WordListVocabularyRepository.from_repository_root(root)
    mode = resolve_hypothesis_mode(mode_name, vocabulary, frequency_prior=frequency_prior)
    feedback = HardleFeedbackEngine(GameSpec(word_length=5, max_guesses=10))
    legal = tuple(vocabulary.legal_guesses())
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
        vocabulary=vocabulary,
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
        top_candidates=_top_candidates(state.belief),
        status=status,
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
) -> SimulationResult:
    context = _make_context(
        mode_name,
        policy_name,
        cache_dir,
        seed,
        use_cache,
        frequency_prior=frequency_prior,
        repository_root=repository_root,
    )
    target = target.strip().lower()
    if target not in context.legal_guesses:
        raise ValueError(f"target {target!r} is not in the legal 12,974-word vocabulary")
    if target not in context.mode.support:
        raise ValueError(
            f"target {target!r} is outside {context.mode.label}; "
            "use a full-support mode for this target"
        )
    if max_guesses <= 0:
        raise ValueError("max_guesses must be positive")
    initial = context.mode.prior.initial_belief(context.mode.support)
    state = DecisionState(initial, max_guesses)
    turns: List[TurnResult] = []
    solved = False
    started = time.perf_counter()
    for turn_number in range(1, max_guesses + 1):
        decision_started = time.perf_counter()
        guess = context.policy.select_guess(state, context.legal_guesses)
        decision_ms = (time.perf_counter() - decision_started) * 1000.0
        observed = context.feedback.evaluate(guess, target)
        solved = observed == (5, 0)
        belief = context.posterior_updater.update(state.belief, guess, observed)
        current_state = DecisionState(belief, max_guesses - turn_number)
        if solved:
            status = "SOLVED"
        elif turn_number >= max_guesses:
            status = "HORIZON_REACHED"
        else:
            status = "CONTINUE"
        result = _build_turn(
            context,
            current_state,
            turn_number,
            guess,
            observed,
            decision_ms,
            status,
        )
        turns.append(result)
        if on_turn is not None:
            on_turn(result)
        if solved or status == "HORIZON_REACHED":
            break
        state = current_state
    return SimulationResult(
        mode=context.mode,
        policy_name=policy_name,
        target=target,
        solved=solved,
        turns=tuple(turns),
        total_time_ms=(time.perf_counter() - started) * 1000.0,
    )


def _parse_feedback(value: str) -> Feedback:
    cleaned = value.replace(",", " ").strip()
    fields = cleaned.split()
    if len(fields) != 2:
        raise ValueError("feedback must contain exactly two integers: exact misplaced")
    try:
        exact, misplaced = (int(field) for field in fields)
    except ValueError as exc:
        raise ValueError("feedback must contain exactly two integers: exact misplaced") from exc
    if exact < 0 or misplaced < 0 or exact > 5 or misplaced > 5 - exact:
        raise ValueError("feedback must satisfy 0 <= exact, misplaced and exact + misplaced <= 5")
    return exact, misplaced


def run_live(
    mode_name: str,
    policy_name: str,
    max_guesses: int,
    seed: int,
    cache_dir: Path,
    use_cache: bool,
    repository_root: Optional[Path] = None,
    input_function=input,
    output_function=print,
) -> int:
    context = _make_context(
        mode_name,
        policy_name,
        cache_dir,
        seed,
        use_cache,
        repository_root=repository_root,
    )
    belief = context.mode.prior.initial_belief(context.mode.support)
    state = DecisionState(belief, max_guesses)
    entropy = ShannonEntropyCalculator()
    output_function(
        f"MODE: {context.mode.label} | support={len(context.mode.support)} | "
        f"policy={policy_name} | max_guesses={max_guesses}"
    )
    for turn_number in range(1, max_guesses + 1):
        decision_started = time.perf_counter()
        guess = context.policy.select_guess(state, context.legal_guesses)
        decision_ms = (time.perf_counter() - decision_started) * 1000.0
        preview = _build_turn(
            context, state, turn_number, guess, None, decision_ms, "AWAITING_FEEDBACK"
        )
        output_function(_format_turn(preview))
        while True:
            try:
                raw = input_function("Enter Hardle feedback (exact misplaced), or q: ")
            except (EOFError, KeyboardInterrupt):
                output_function("status=QUIT")
                return 0
            if raw.strip().lower() in {"q", "quit", "exit"}:
                output_function("status=QUIT")
                return 0
            try:
                observed = _parse_feedback(raw)
            except ValueError as exc:
                output_function(f"REJECTED feedback: {exc}")
                continue
            if observed == (5, 0):
                solved_state = state
                try:
                    solved_belief = context.posterior_updater.update(
                        state.belief, guess, observed
                    )
                    solved_state = DecisionState(
                        solved_belief, max_guesses - turn_number
                    )
                except (ImpossibleObservationError, ValueError):
                    # An exact website win is definitive even if the selected
                    # diagnostic support did not contain that hidden target.
                    pass
                output_function(
                    _format_turn(
                        _build_turn(
                            context,
                            solved_state,
                            turn_number,
                            guess,
                            observed,
                            decision_ms,
                            "SOLVED",
                        )
                    )
                )
                return 0
            try:
                belief = context.posterior_updater.update(state.belief, guess, observed)
            except (ImpossibleObservationError, ValueError) as exc:
                output_function(f"REJECTED feedback: {exc}")
                continue
            remaining = max_guesses - turn_number
            state = DecisionState(belief, remaining)
            status = "CONTINUE" if remaining else "HORIZON_REACHED"
            output_function(
                _format_turn(
                    _build_turn(
                        context, state, turn_number, guess, observed, decision_ms, status
                    )
                )
            )
            if status == "HORIZON_REACHED":
                return 0
            break
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bayesian-hardle",
        description="Interactive fair full-support Bayesian Hardle acceptance client.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  bayesian-hardle simulate --target aahed --mode full-uniform --policy max-ig\n"
            "  python3 -m bayesian_hardle.cli live --mode full-frequency --policy map\n"
            "  bayesian-hardle compare --target aahed --modes full-uniform full-frequency "
            "--policies map max-ig"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def common(subparser):
        subparser.add_argument("--mode", choices=MODE_NAMES, default="full-uniform")
        subparser.add_argument("--policy", choices=POLICY_NAMES, default="max-ig")
        subparser.add_argument("--max-guesses", type=int, default=10)
        subparser.add_argument("--seed", type=int, default=0)
        subparser.add_argument(
            "--cache-dir",
            type=Path,
            default=Path(".cache/bayesian_hardle"),
            help="disk cache for exact feedback matrices (default: .cache/bayesian_hardle)",
        )
        subparser.add_argument(
            "--no-cache", action="store_true", help="build the exact matrix in memory"
        )
        subparser.add_argument(
            "--repository-root",
            type=Path,
            default=None,
            help="repository containing data/wordlists (default: current directory)",
        )

    simulate = subparsers.add_parser(
        "simulate", help="play against a target entered on the command line"
    )
    simulate.add_argument("--target", help="any legal five-letter target word")
    common(simulate)
    simulate.add_argument("--json", action="store_true", help="emit a JSON result")

    live = subparsers.add_parser(
        "live", help="recommend guesses while you enter website feedback"
    )
    common(live)

    compare = subparsers.add_parser(
        "compare", help="run independent simulations for several modes/policies"
    )
    compare.add_argument("--target", required=True)
    compare.add_argument("--modes", nargs="+", choices=MODE_NAMES, default=["full-uniform"])
    compare.add_argument("--policies", nargs="+", choices=POLICY_NAMES, default=["map", "max-ig"])
    compare.add_argument("--max-guesses", type=int, default=10)
    compare.add_argument("--seed", type=int, default=0)
    compare.add_argument("--cache-dir", type=Path, default=Path(".cache/bayesian_hardle"))
    compare.add_argument("--no-cache", action="store_true")
    compare.add_argument("--repository-root", type=Path, default=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "simulate":
            target = args.target
            if target is None:
                target = input("Enter legal five-letter target: ")
            print(
                f"MODE: {args.mode} | policy={args.policy} | "
                "support is resolved by the selected mode"
            )
            result = run_simulation(
                target,
                args.mode,
                args.policy,
                max_guesses=args.max_guesses,
                seed=args.seed,
                cache_dir=args.cache_dir,
                use_cache=not args.no_cache,
                repository_root=args.repository_root,
                on_turn=lambda turn: print(_format_turn(turn)),
            )
            print(
                f"MODE: {result.mode.label} | support={len(result.mode.support)}"
            )
            print(
                f"RESULT solved={result.solved} turns={len(result.turns)} "
                f"total_time_ms={result.total_time_ms:.3f}"
            )
            if args.json:
                print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
            return 0
        if args.command == "live":
            return run_live(
                args.mode,
                args.policy,
                args.max_guesses,
                args.seed,
                args.cache_dir,
                not args.no_cache,
                repository_root=args.repository_root,
            )
        if args.command == "compare":
            for mode_name in args.modes:
                for policy_name in args.policies:
                    print(f"=== independent run mode={mode_name} policy={policy_name} ===")
                    result = run_simulation(
                        args.target,
                        mode_name,
                        policy_name,
                        max_guesses=args.max_guesses,
                        seed=args.seed,
                        cache_dir=args.cache_dir,
                        use_cache=not args.no_cache,
                        repository_root=args.repository_root,
                        on_turn=lambda turn: print(_format_turn(turn)),
                    )
                    print(
                        f"COMPARE solved={result.solved} turns={len(result.turns)} "
                        f"total_time_ms={result.total_time_ms:.3f}"
                    )
            return 0
    except (ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
