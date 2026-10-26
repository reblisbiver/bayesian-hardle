"""Command-line adapter for the shared Bayesian Hardle application services."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Optional, Sequence

from .application import (
    MODE_NAMES,
    POLICY_NAMES,
    _build_turn,
    make_solver_context,
    run_simulation,
)
from .belief import ImpossibleObservationError
from .decision import DecisionState


def _format_turn(turn) -> str:
    feedback = "unknown" if turn.feedback is None else str(turn.feedback)
    top = ", ".join(
        f"{word}:{probability:.6g}" for word, probability in turn.top_candidates
    )
    return (
        f"TURN {turn.turn} | mode={turn.mode_label} | policy={turn.policy}\n"
        f"  guess={turn.guess} feedback={feedback} "
        f"remaining_candidates={turn.remaining_candidates} "
        f"entropy_bits={turn.entropy_bits:.6f} decision_ms={turn.decision_ms:.3f} "
        f"cumulative_ms={turn.cumulative_time_ms:.3f}\n"
        f"  top_candidates={top}\n"
        f"  status={turn.status}"
    )


def _parse_feedback(value: str):
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
    context = make_solver_context(
        mode_name,
        policy_name,
        cache_dir=cache_dir,
        seed=seed,
        use_cache=use_cache,
        repository_root=repository_root,
        max_guesses=max_guesses,
    )
    belief = context.mode.prior.initial_belief(context.mode.support)
    state = DecisionState(belief, max_guesses)
    cumulative_ms = 0.0
    output_function(
        f"MODE: {context.mode.label} | support={len(context.mode.support)} | "
        f"policy={policy_name} | max_guesses={max_guesses}"
    )
    for turn_number in range(1, max_guesses + 1):
        decision_started = time.perf_counter()
        guess = context.policy.select_guess(state, context.legal_guesses)
        decision_ms = (time.perf_counter() - decision_started) * 1000.0
        cumulative_ms += decision_ms
        preview = _build_turn(
            context,
            state,
            turn_number,
            guess,
            None,
            decision_ms,
            cumulative_ms,
            "AWAITING_FEEDBACK",
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
                        state.belief,
                        guess,
                        observed,
                    )
                    solved_state = DecisionState(
                        solved_belief,
                        max_guesses - turn_number,
                    )
                except (ImpossibleObservationError, ValueError):
                    # A website win is definitive even if a diagnostic support
                    # did not contain the hidden target.
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
                            cumulative_ms,
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
                        context,
                        state,
                        turn_number,
                        guess,
                        observed,
                        decision_ms,
                        cumulative_ms,
                        status,
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
            "--no-cache",
            action="store_true",
            help="build the exact matrix in memory",
        )
        subparser.add_argument(
            "--repository-root",
            type=Path,
            default=None,
            help="repository containing data/wordlists (default: current directory)",
        )

    simulate = subparsers.add_parser(
        "simulate",
        help="play against a target entered on the command line",
    )
    simulate.add_argument("--target", help="any legal five-letter target word")
    common(simulate)
    simulate.add_argument("--json", action="store_true", help="emit a JSON result")

    live = subparsers.add_parser(
        "live",
        help="recommend guesses while you enter website feedback",
    )
    common(live)

    compare = subparsers.add_parser(
        "compare",
        help="run independent simulations for several modes/policies",
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
            print(f"MODE: {result.mode.label} | support={len(result.mode.support)}")
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
