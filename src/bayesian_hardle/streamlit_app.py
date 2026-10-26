"""Local Streamlit acceptance UI for the exact Bayesian Hardle services."""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Dict, Iterable, List

import streamlit as st

from bayesian_hardle.application import (
    MODE_NAMES,
    POLICY_NAMES,
    BattleSession,
    BattlePublicState,
    SimulationResult,
    run_simulation,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT_ROOT / ".cache" / "bayesian_hardle"
POLICY_LABELS = {
    "random": "Random",
    "map": "MAP — highest posterior candidate",
    "max-ig": "Max-IG — exact information gain",
}
MODE_LABELS = {
    "full-uniform": "full-uniform — strict fairness",
    "full-frequency": "full-frequency — broad human-like prior",
    "curated-2315": "curated-2315 — diagnostic / answer-list-aware",
}
MODE_EXPLANATIONS = {
    "full-uniform": (
        "Strict fairness: every one of the 12,974 legal words is a possible "
        "target with equal prior mass."
    ),
    "full-frequency": (
        "Broad non-leaking human-like prior: all 12,974 legal words remain "
        "possible, weighted only by general-English frequency."
    ),
    "curated-2315": (
        "Diagnostic only: uses the historical curated answer list and is "
        "answer-list-aware, not the primary fairness mode."
    ),
}


def _rerun() -> None:
    rerun = getattr(st, "rerun", None) or st.experimental_rerun
    rerun()


def _feedback_text(feedback) -> str:
    return "—" if feedback is None else f"({feedback[0]}, {feedback[1]})"


def _solver_rows(turns: Iterable) -> List[Dict[str, object]]:
    return [
        {
            "Turn": turn.turn,
            "Guess": turn.guess,
            "Feedback (exact, misplaced)": _feedback_text(turn.feedback),
            "Candidates left": turn.remaining_candidates,
            "Entropy (bits)": round(turn.entropy_bits, 4),
            "Decision (ms)": round(turn.decision_ms, 3),
            "Cumulative (ms)": round(turn.cumulative_time_ms, 3),
            "Status": turn.status,
        }
        for turn in turns
    ]


def _human_rows(state: BattlePublicState) -> List[Dict[str, object]]:
    return [
        {
            "Turn": turn.turn,
            "Your guess": turn.guess,
            "Feedback (exact, misplaced)": _feedback_text(turn.feedback),
            "Status": turn.status,
        }
        for turn in state.human_turns
    ]


def _render_dataframe(rows: List[Dict[str, object]]) -> None:
    kwargs = {"hide_index": True}
    if "width" in inspect.signature(st.dataframe).parameters:
        kwargs["width"] = "stretch"
    else:
        kwargs["use_container_width"] = True
    st.dataframe(rows, **kwargs)


def _render_mode_help(mode_name: str) -> None:
    st.caption(MODE_EXPLANATIONS[mode_name])


def _render_comparison() -> None:
    st.header("Strategy comparison")
    st.write("Enter a known legal target and compare independent policy runs on the same target.")
    target = st.text_input(
        "Known target word",
        placeholder="aahed",
        max_chars=5,
        key="comparison_target",
    )
    mode_name = st.selectbox(
        "Solver mode",
        MODE_NAMES,
        format_func=lambda value: MODE_LABELS[value],
        key="comparison_mode",
    )
    _render_mode_help(mode_name)
    policies = st.multiselect(
        "Policies to run",
        POLICY_NAMES,
        default=["map", "max-ig"],
        format_func=lambda value: POLICY_LABELS[value],
        key="comparison_policies",
    )
    st.caption(
        "Exact Bayes-optimal is not offered here because the accepted exact "
        "planner is intentionally limited to tractable small vocabularies."
    )
    if st.button("Run comparison", type="primary", key="run_comparison"):
        if not target.strip():
            st.error("Enter a legal five-letter target first.")
            return
        if not policies:
            st.error("Select at least one policy.")
            return
        results: List[SimulationResult] = []
        progress = st.progress(0.0, text="Preparing independent runs…")
        for index, policy_name in enumerate(policies):
            try:
                with st.spinner(f"Running {POLICY_LABELS[policy_name]}…"):
                    results.append(
                        run_simulation(
                            target,
                            mode_name,
                            policy_name,
                            cache_dir=CACHE_DIR,
                            repository_root=PROJECT_ROOT,
                        )
                    )
            except (ValueError, RuntimeError) as exc:
                st.error(str(exc))
                return
            progress.progress(
                (index + 1) / len(policies),
                text=f"Completed {index + 1} of {len(policies)} policies",
            )
        st.session_state["comparison_results"] = results

    results = st.session_state.get("comparison_results", ())
    if not results:
        return
    st.subheader("Results")
    columns = st.columns(len(results))
    for column, result in zip(columns, results):
        with column:
            decision_total = sum(turn.decision_ms for turn in result.turns)
            st.markdown(f"#### {POLICY_LABELS[result.policy_name]}")
            st.metric("Outcome", "Solved" if result.solved else "Not solved")
            st.metric("Turns", len(result.turns))
            st.metric("Total decision time", f"{decision_total:.2f} ms")
            st.caption(
                f"Support: {len(result.mode.support):,} words · "
                f"wall time: {result.total_time_ms:.2f} ms"
            )
            _render_dataframe(_solver_rows(result.turns))


def _start_battle(mode_name: str, policy_name: str) -> None:
    try:
        with st.spinner("Preparing the hidden target and solver…"):
            st.session_state["battle"] = BattleSession(
                mode_name=mode_name,
                policy_name=policy_name,
                cache_dir=CACHE_DIR,
                repository_root=PROJECT_ROOT,
            )
    except (ValueError, RuntimeError) as exc:
        st.error(str(exc))
        return
    st.session_state.pop("battle_message", None)
    _rerun()


def _render_battle() -> None:
    st.header("Human vs Solver")
    battle = st.session_state.get("battle")
    active = battle is not None and not battle.public_state().finished
    mode_name = st.selectbox(
        "Solver prior / support mode",
        MODE_NAMES,
        format_func=lambda value: MODE_LABELS[value],
        disabled=active,
        key="battle_mode",
    )
    policy_name = st.selectbox(
        "Solver policy",
        POLICY_NAMES,
        index=1,
        format_func=lambda value: POLICY_LABELS[value],
        disabled=active,
        key="battle_policy",
    )
    _render_mode_help(mode_name)
    st.caption(
        "Start New Battle samples the hidden target uniformly from the selected "
        "support. In full-frequency, only the solver prior is frequency-weighted."
    )

    if battle is None:
        if st.button("Start New Battle", type="primary", key="start_battle"):
            _start_battle(mode_name, policy_name)
        return

    state = battle.public_state()
    if not state.finished:
        st.info("The hidden target is active. Solver guesses and solver feedback stay hidden until you finish or give up.")
        if state.human_turns:
            _render_dataframe(_human_rows(state))
        with st.form("human_guess_form", clear_on_submit=True):
            guess = st.text_input(
                "Your legal guess",
                placeholder="type a five-letter legal word",
                max_chars=5,
            )
            submitted = st.form_submit_button("Submit guess", type="primary")
        if submitted:
            try:
                result = battle.submit_human_guess(guess)
                if not result.finished:
                    st.session_state["battle_message"] = (
                        f"Feedback for {guess.strip().lower()}: "
                        f"{_feedback_text(result.feedback)}"
                    )
                _rerun()
            except (TypeError, ValueError, RuntimeError) as exc:
                st.error(str(exc))
        if st.button("Give up", key="give_up_battle"):
            battle.give_up()
            _rerun()
    else:
        st.success("Battle finished — the target and solver trajectory are now revealed.")
        st.metric("Hidden target", state.target or "unknown")
        comparison_columns = st.columns(3)
        with comparison_columns[0]:
            st.metric("Human outcome", "Solved" if state.human_solved else "Not solved")
        with comparison_columns[1]:
            st.metric("Human turns", len(state.human_turns))
        with comparison_columns[2]:
            st.metric("Solver turns", len(state.solver_turns))
        st.subheader("Human trajectory")
        _render_dataframe(_human_rows(state))
        st.subheader("Solver trajectory")
        _render_dataframe(_solver_rows(state.solver_turns))

    if st.button("Reset / New Battle", key="reset_battle"):
        st.session_state.pop("battle", None)
        st.session_state.pop("battle_message", None)
        _rerun()


def main() -> None:
    st.set_page_config(
        page_title="Bayesian Hardle acceptance",
        page_icon="🎯",
        layout="wide",
    )
    st.title("Bayesian Hardle — interactive acceptance")
    st.caption("Local visual client for the exact ISSUE-006 solver; executor evidence remains pending supervisor review.")
    comparison_tab, battle_tab = st.tabs(["Strategy comparison", "Human vs Solver"])
    with comparison_tab:
        _render_comparison()
    with battle_tab:
        _render_battle()


if __name__ == "__main__":
    main()
