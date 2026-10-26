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
    "random": "随机基线（Random）",
    "map": "最大后验（MAP）",
    "max-ig": "最大信息增益（Max-IG）",
}
EXACT_POLICY_LABEL = "精确贝叶斯最优（Exact Bayes-optimal）"
MODE_LABELS = {
    "full-uniform": "全支持均匀先验（full-uniform）— 严格公平",
    "full-frequency": "全支持频率先验（full-frequency）— 类人先验",
    "curated-2315": "精选 2,315（curated-2315）— 诊断模式",
}
MODE_EXPLANATIONS = {
    "full-uniform": "严格公平：12,974 个合法词都可能是目标，且先验概率相同。",
    "full-frequency": (
        "宽泛的类人先验：12,974 个合法词仍都可能是目标，仅按通用英语词频加权。"
    ),
    "curated-2315": (
        "仅用于诊断：使用历史 2,315 个候选答案列表，知道答案列表边界，不代表主要公平模式。"
    ),
}
STATUS_LABELS = {
    "SOLVED": "已解决",
    "HORIZON_REACHED": "已达猜测上限",
    "CONTINUE": "进行中",
}


def _rerun() -> None:
    rerun = getattr(st, "rerun", None) or st.experimental_rerun
    rerun()


def _feedback_text(feedback) -> str:
    return "—" if feedback is None else f"（{feedback[0]}，{feedback[1]}）"


def _status_text(status: str) -> str:
    return STATUS_LABELS.get(status, "未知状态")


def _show_error(exc: Exception) -> None:
    message = str(exc)
    if "not in the legal 12,974-word vocabulary" in message:
        detail = "目标词不在 12,974 个合法词组成的词表中。"
    elif "outside" in message and "support" in message:
        detail = "目标词不属于当前模式的支持集，请切换到全支持模式。"
    elif "not a legal five-letter word" in message:
        detail = "请输入合法的五字母单词。"
    elif "guess must be a string" in message:
        detail = "请输入五字母单词。"
    elif "cannot find repository root" in message:
        detail = "找不到项目根目录，请从项目目录启动应用。"
    else:
        detail = "请检查输入后重试。"
    st.error(f"操作失败：{detail}")


def _solver_rows(turns: Iterable) -> List[Dict[str, object]]:
    return [
        {
            "回合": turn.turn,
            "猜词": turn.guess,
            "反馈（命中、错位）": _feedback_text(turn.feedback),
            "剩余候选数": turn.remaining_candidates,
            "熵（比特）": round(turn.entropy_bits, 4),
            "单步决策时间（毫秒）": round(turn.decision_ms, 3),
            "累计时间（毫秒）": round(turn.cumulative_time_ms, 3),
            "状态": _status_text(turn.status),
        }
        for turn in turns
    ]


def _human_rows(state: BattlePublicState) -> List[Dict[str, object]]:
    return [
        {
            "回合": turn.turn,
            "你的猜词": turn.guess,
            "反馈（命中、错位）": _feedback_text(turn.feedback),
            "状态": _status_text(turn.status),
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


def _render_exact_policy_status() -> None:
    st.info(
        f"策略状态：{EXACT_POLICY_LABEL} 当前不支持 12,974 词的全支持模式。\n\n"
        "已接受的精确规划目前仅在较小词表上可计算并已完成验证。"
    )


def _render_comparison() -> None:
    st.header("策略比较")
    st.write("输入一个已知的合法目标词，在同一目标上独立比较各策略。")
    target = st.text_input(
        "已知目标词",
        placeholder="例如 aahed",
        max_chars=5,
        key="comparison_target",
    )
    mode_name = st.selectbox(
        "求解模式",
        MODE_NAMES,
        format_func=lambda value: MODE_LABELS[value],
        key="comparison_mode",
    )
    _render_mode_help(mode_name)
    _render_exact_policy_status()
    policies = st.multiselect(
        "要运行的策略",
        POLICY_NAMES,
        default=["map", "max-ig"],
        format_func=lambda value: POLICY_LABELS[value],
        key="comparison_policies",
    )
    st.caption("默认选择最大后验与最大信息增益；随机基线可直接加入比较。")
    if st.button("运行策略比较", type="primary", key="run_comparison"):
        if not target.strip():
            st.error("请输入一个合法的五字母目标词。")
            return
        if not policies:
            st.error("请至少选择一个策略。")
            return
        results: List[SimulationResult] = []
        progress = st.progress(0.0, text="正在准备独立运行…")
        for index, policy_name in enumerate(policies):
            try:
                with st.spinner(f"正在运行 {POLICY_LABELS[policy_name]}…"):
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
                _show_error(exc)
                return
            progress.progress(
                (index + 1) / len(policies),
                text=f"已完成 {index + 1}/{len(policies)} 个策略",
            )
        st.session_state["comparison_results"] = results

    results = st.session_state.get("comparison_results", ())
    if not results:
        return
    st.subheader("结果")
    columns = st.columns(len(results))
    for column, result in zip(columns, results):
        with column:
            decision_total = sum(turn.decision_ms for turn in result.turns)
            st.markdown(f"#### {POLICY_LABELS[result.policy_name]}")
            st.metric("结果", "已解决" if result.solved else "未解决")
            st.metric("回合数", len(result.turns))
            st.metric("决策总耗时", f"{decision_total:.2f} 毫秒")
            st.caption(
                f"支持集：{len(result.mode.support):,} 个词 · "
                f"总耗时：{result.total_time_ms:.2f} 毫秒"
            )
            _render_dataframe(_solver_rows(result.turns))


def _start_battle(mode_name: str, policy_name: str) -> None:
    try:
        with st.spinner("正在准备隐藏目标和求解器…"):
            st.session_state["battle"] = BattleSession(
                mode_name=mode_name,
                policy_name=policy_name,
                cache_dir=CACHE_DIR,
                repository_root=PROJECT_ROOT,
            )
    except (ValueError, RuntimeError) as exc:
        _show_error(exc)
        return
    st.session_state.pop("battle_message", None)
    _rerun()


def _render_battle() -> None:
    st.header("人类对战求解器")
    battle = st.session_state.get("battle")
    active = battle is not None and not battle.public_state().finished
    mode_name = st.selectbox(
        "求解器先验 / 支持集模式",
        MODE_NAMES,
        format_func=lambda value: MODE_LABELS[value],
        disabled=active,
        key="battle_mode",
    )
    policy_name = st.selectbox(
        "求解器策略",
        POLICY_NAMES,
        index=1,
        format_func=lambda value: POLICY_LABELS[value],
        disabled=active,
        key="battle_policy",
    )
    _render_mode_help(mode_name)
    _render_exact_policy_status()
    st.caption(
        "点击“开始新对战”后，系统会从所选支持集中均匀抽取隐藏目标；频率模式仅对求解器先验加权。"
    )

    if battle is None:
        if st.button("开始新对战", type="primary", key="start_battle"):
            _start_battle(mode_name, policy_name)
        return

    state = battle.public_state()
    if not state.finished:
        st.info("隐藏目标已启用。完成对战或主动放弃前，不会显示求解器猜词和反馈。")
        if state.human_turns:
            _render_dataframe(_human_rows(state))
        with st.form("human_guess_form", clear_on_submit=True):
            guess = st.text_input(
                "你的合法猜词",
                placeholder="请输入五字母合法单词",
                max_chars=5,
            )
            submitted = st.form_submit_button("提交猜词", type="primary")
        if submitted:
            try:
                result = battle.submit_human_guess(guess)
                if not result.finished:
                    st.session_state["battle_message"] = (
                        f"{guess.strip().lower()} 的反馈："
                        f"{_feedback_text(result.feedback)}"
                    )
                _rerun()
            except (TypeError, ValueError, RuntimeError) as exc:
                _show_error(exc)
        if st.button("放弃本局", key="give_up_battle"):
            battle.give_up()
            _rerun()
    else:
        st.success("对战已结束——现在显示目标词和求解器轨迹。")
        st.metric("隐藏目标", state.target or "未知")
        comparison_columns = st.columns(3)
        with comparison_columns[0]:
            st.metric("人类结果", "已解决" if state.human_solved else "未解决")
        with comparison_columns[1]:
            st.metric("人类回合数", len(state.human_turns))
        with comparison_columns[2]:
            st.metric("求解器回合数", len(state.solver_turns))
        st.subheader("人类轨迹")
        _render_dataframe(_human_rows(state))
        st.subheader("求解器轨迹")
        _render_dataframe(_solver_rows(state.solver_turns))

    if st.button("重置 / 新对战", key="reset_battle"):
        st.session_state.pop("battle", None)
        st.session_state.pop("battle_message", None)
        _rerun()


def main() -> None:
    st.set_page_config(
        page_title="贝叶斯 Hardle — 交互式验收",
        page_icon="🎯",
        layout="wide",
    )
    st.title("贝叶斯 Hardle — 交互式验收")
    st.caption("本地可视化验收界面，使用 ISSUE-006 的精确求解器；执行证据仍待监督者复核。")
    comparison_tab, battle_tab = st.tabs(["策略比较", "人类对战求解器"])
    with comparison_tab:
        _render_comparison()
    with battle_tab:
        _render_battle()


if __name__ == "__main__":
    main()
