"""Read partial root progress for the bounded ISSUE-022 curated probe."""

from __future__ import annotations

import json
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))

from bayesian_hardle.belief import ExactPosteriorUpdater, UniformPrior  # noqa: E402
from bayesian_hardle.decision import DecisionState  # noqa: E402
from bayesian_hardle.game import HardleFeedbackEngine  # noqa: E402
from issue_022_uniform_h3_capacity import (  # noqa: E402
    AFTER_LAYERS,
    CONTROL_LAYERS,
    _cases,
    _make_planner,
    _root_summary,
)


class PartialDeadline(Exception):
    pass


def _handler(signum, frame):
    del signum, frame
    raise PartialDeadline


def _run(case, layers, timeout_seconds):
    support = tuple(case["support"])
    legal = tuple(case["legal"])
    feedback = HardleFeedbackEngine()
    updater = ExactPosteriorUpdater(feedback)
    state = DecisionState(UniformPrior().initial_belief(support), 3)
    planner, matrix_build_seconds = _make_planner(
        layers, legal, support, case.get("root_audit_limit")
    )
    previous = signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, timeout_seconds)
    started = time.perf_counter()
    try:
        selected = planner.select_guess(state, legal, feedback, updater)
        value = planner._guess_value(state, selected, legal, feedback, updater)
        status = "completed"
    except PartialDeadline:
        selected = None
        value = None
        status = "timed_out_partial"
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    instrumentation = planner.instrumentation()
    summary = _root_summary(instrumentation)
    return {
        "status": status,
        "variant": "after" if "uniform_h3_branch_capacity" in layers else "control",
        "support_size": len(support),
        "legal_size": len(legal),
        "timeout_seconds": timeout_seconds,
        "elapsed_seconds": time.perf_counter() - started,
        "matrix_build_seconds": matrix_build_seconds,
        "selected_guess": selected,
        "value": list(value) if value is not None else None,
        "root_summary": summary,
    }


def main():
    case = next(item for item in _cases() if item["name"] == "curated2315_h3_fulllegal")
    result = {
        "issue": "ISSUE-022",
        "case": case["name"],
        "runs": [
            _run(case, CONTROL_LAYERS, 44.0),
            _run(case, AFTER_LAYERS, 44.0),
        ],
    }
    output = ROOT / "experiments" / "results" / "issue_022_curated_progress.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
