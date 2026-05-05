from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any

import pandas as pd

from mqre_v2.reporting.wfo_report import decision_result_to_dict, wfo_run_result_to_dict
from mqre_v2.validation.decision import compare_baseline_challenger
from mqre_v2.validation.wfo import (
    TxtWfoInput,
    WfoGateConfig,
    WfoRunResult,
    build_txt_evaluate_fn,
    default_optimize_fn,
    run_wfo,
)

ROUND_DATAFRAME_COLUMNS = [
    "round_id",
    "test_net_profit",
    "test_mdd",
    "test_pf",
    "test_trade_count",
]


def run_txt_wfo_from_config(config: dict) -> dict:
    strategy_name = str(config.get("strategy_name", "txt-strategy"))
    result = _run_wfo_for_txt(
        txt_path=str(config["txt_path"]),
        strategy_name=strategy_name,
        config=config,
    )

    payload = wfo_run_result_to_dict(result)
    payload["strategy_name"] = strategy_name
    return payload


def run_baseline_challenger_from_config(config: dict) -> dict:
    baseline_name = str(config.get("baseline_name", "baseline"))
    challenger_name = str(config.get("challenger_name", "challenger"))

    baseline = _run_wfo_for_txt(
        txt_path=str(config["baseline_txt_path"]),
        strategy_name=baseline_name,
        config=config,
    )
    challenger = _run_wfo_for_txt(
        txt_path=str(config["challenger_txt_path"]),
        strategy_name=challenger_name,
        config=config,
    )
    decision = compare_baseline_challenger(
        baseline.summary,
        challenger.summary,
        min_improvement=_get_float(config, "min_improvement", 5.0),
    )

    baseline_payload = wfo_run_result_to_dict(baseline)
    baseline_payload["strategy_name"] = baseline_name
    challenger_payload = wfo_run_result_to_dict(challenger)
    challenger_payload["strategy_name"] = challenger_name

    return {
        "generated_at": _generated_at(),
        "baseline": baseline_payload,
        "challenger": challenger_payload,
        "decision": decision_result_to_dict(decision),
    }


def build_round_dataframe(round_results: list | tuple) -> pd.DataFrame:
    rows = [
        {column: _get_round_value(result, column) for column in ROUND_DATAFRAME_COLUMNS}
        for result in round_results
    ]
    df = pd.DataFrame(rows, columns=ROUND_DATAFRAME_COLUMNS)

    for column in ROUND_DATAFRAME_COLUMNS:
        df[column] = pd.to_numeric(
            df[column].replace({"Infinity": float("inf"), "-Infinity": -float("inf")}),
            errors="coerce",
        )

    df["cum_pnl"] = df["test_net_profit"].cumsum()
    return df


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="mqquant 策略研究工作台", layout="wide")
    st.title("mqquant 策略研究工作台")

    with st.sidebar:
        mode = st.selectbox("mode", ["單一策略 WFO", "Baseline vs Challenger"])

    if mode == "單一策略 WFO":
        _render_single_wfo_mode(st)
    else:
        _render_baseline_challenger_mode(st)


def _render_single_wfo_mode(st: Any) -> None:
    with st.sidebar:
        txt_path = st.text_input("txt_path")
        strategy_name = st.text_input("strategy_name", value="txt-strategy")
        config = {
            "txt_path": txt_path,
            "strategy_name": strategy_name,
            **_wfo_parameter_inputs(st),
        }
        run_clicked = st.button("執行 WFO")

    if not run_clicked:
        return

    try:
        payload = run_txt_wfo_from_config(config)
    except Exception as exc:
        st.error(str(exc))
        return

    _render_single_wfo_result(st, payload)


def _render_baseline_challenger_mode(st: Any) -> None:
    with st.sidebar:
        baseline_txt_path = st.text_input("baseline_txt_path")
        baseline_name = st.text_input("baseline_name", value="baseline")
        challenger_txt_path = st.text_input("challenger_txt_path")
        challenger_name = st.text_input("challenger_name", value="challenger")
        config = {
            "baseline_txt_path": baseline_txt_path,
            "baseline_name": baseline_name,
            "challenger_txt_path": challenger_txt_path,
            "challenger_name": challenger_name,
            **_wfo_parameter_inputs(st),
            "min_improvement": st.number_input(
                "min_improvement",
                min_value=0.0,
                value=5.0,
            ),
        }
        run_clicked = st.button("執行比較")

    if not run_clicked:
        return

    try:
        payload = run_baseline_challenger_from_config(config)
    except Exception as exc:
        st.error(str(exc))
        return

    _render_baseline_challenger_result(st, payload)


def _wfo_parameter_inputs(st: Any) -> dict[str, Any]:
    return {
        "start_date": st.date_input("start_date", value=date(2020, 1, 1)),
        "end_date": st.date_input("end_date", value=date.today()),
        "train_months": st.number_input("train_months", min_value=1, value=36, step=1),
        "gap_months": st.number_input("gap_months", min_value=1, value=1, step=1),
        "test_months": st.number_input("test_months", min_value=1, value=6, step=1),
        "step_months": st.number_input("step_months", min_value=1, value=6, step=1),
        "min_test_trade_count": st.number_input(
            "min_test_trade_count",
            min_value=1,
            value=20,
            step=1,
        ),
        "max_test_mdd": st.number_input("max_test_mdd", min_value=0.0, value=15000.0),
        "min_test_pf": st.number_input("min_test_pf", min_value=0.0, value=1.05),
        "min_pass_rate": st.number_input(
            "min_pass_rate",
            min_value=0.0,
            max_value=1.0,
            value=0.6,
        ),
    }


def _render_single_wfo_result(st: Any, payload: dict) -> None:
    _render_pass_status(st, payload)
    _render_summary(st, "Summary", payload["summary"])
    _render_round_charts(st, payload["round_results"])

    st.subheader("Round Results")
    _render_round_results_table(st, payload["round_results"])

    st.download_button(
        "下載 JSON",
        data=json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False),
        file_name="wfo_report.json",
        mime="application/json",
    )


def _render_baseline_challenger_result(st: Any, payload: dict) -> None:
    decision = payload["decision"]
    if decision["upgrade"]:
        st.success("upgrade: True")
    else:
        st.warning("upgrade: False")

    st.write(
        {
            "reason": decision["reason"],
            "baseline_score": decision["baseline_score"],
            "challenger_score": decision["challenger_score"],
        }
    )

    _render_summary(st, "Baseline Summary", payload["baseline"]["summary"])
    _render_summary(st, "Challenger Summary", payload["challenger"]["summary"])

    st.subheader("Baseline 圖表")
    _render_round_charts(st, payload["baseline"]["round_results"])
    st.subheader("Challenger 圖表")
    _render_round_charts(st, payload["challenger"]["round_results"])

    st.subheader("Baseline Round Results")
    _render_round_results_table(st, payload["baseline"]["round_results"])
    st.subheader("Challenger Round Results")
    _render_round_results_table(st, payload["challenger"]["round_results"])

    st.download_button(
        "下載比較 JSON",
        data=json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False),
        file_name="baseline_challenger_report.json",
        mime="application/json",
    )


def _render_pass_status(st: Any, payload: dict) -> None:
    if payload["passed"]:
        st.success("passed: True")
    else:
        st.error("passed: False")

    st.write({"fail_reason": payload["fail_reason"]})


def _render_summary(st: Any, title: str, summary: dict) -> None:
    st.subheader(title)
    if summary["pass_rate"] < 0.6:
        st.warning(f"{title} pass_rate below 0.6: {summary['pass_rate']}")

    columns = st.columns(3)
    summary_items = [
        ("total_rounds", summary["total_rounds"]),
        ("passed_rounds", summary["passed_rounds"]),
        ("failed_rounds", summary["failed_rounds"]),
        ("pass_rate", summary["pass_rate"]),
        ("total_test_net_profit", summary["total_test_net_profit"]),
        ("average_test_net_profit", summary["average_test_net_profit"]),
        ("max_test_mdd", summary["max_test_mdd"]),
        ("average_test_pf", summary["average_test_pf"]),
        ("total_test_trade_count", summary["total_test_trade_count"]),
    ]
    for index, (label, value) in enumerate(summary_items):
        columns[index % len(columns)].metric(label, value)


def _render_round_charts(st: Any, round_results: list) -> None:
    df = build_round_dataframe(round_results)
    if df.empty:
        st.info("No WFO round results to chart.")
        return

    chart_df = df.replace([float("inf"), -float("inf")], pd.NA)
    indexed_df = chart_df.set_index("round_id")

    st.subheader("WFO 每輪淨利")
    st.bar_chart(indexed_df["test_net_profit"])

    st.subheader("WFO 每輪 MDD")
    st.bar_chart(indexed_df["test_mdd"])

    st.subheader("WFO 每輪 PF")
    st.bar_chart(indexed_df["test_pf"])

    st.subheader("累積損益曲線")
    st.line_chart(indexed_df["cum_pnl"])


def _render_round_results_table(st: Any, round_results: list) -> None:
    table = pd.DataFrame(round_results)
    if table.empty:
        st.dataframe(table, use_container_width=True)
        return

    if "pass_flag" in table.columns:
        table = table.copy()
        table["pass_marker"] = table["pass_flag"].map(
            lambda passed: "" if bool(passed) else "FAIL"
        )
        styled = table.style.apply(_highlight_failed_rounds, axis=1)
        st.dataframe(styled, use_container_width=True)
        return

    st.dataframe(table, use_container_width=True)


def _highlight_failed_rounds(row: pd.Series) -> list[str]:
    if not bool(row.get("pass_flag", True)):
        return ["background-color: #ffd6d6"] * len(row)
    return [""] * len(row)


def _run_wfo_for_txt(txt_path: str, strategy_name: str, config: dict) -> WfoRunResult:
    txt_input = TxtWfoInput(
        strategy_name=strategy_name,
        txt_path=txt_path,
    )

    return run_wfo(
        start_date=_coerce_date(config["start_date"]),
        end_date=_coerce_date(config["end_date"]),
        strategy_name=strategy_name,
        optimize_fn=default_optimize_fn,
        evaluate_fn=build_txt_evaluate_fn(txt_input),
        window_kwargs={
            "train_months": _get_int(config, "train_months", 36),
            "gap_months": _get_int(config, "gap_months", 1),
            "test_months": _get_int(config, "test_months", 6),
            "step_months": _get_int(config, "step_months", 6),
        },
        gate_config=WfoGateConfig(
            min_test_trade_count=_get_int(config, "min_test_trade_count", 20),
            max_test_mdd=_get_float(config, "max_test_mdd", 15000.0),
            min_test_pf=_get_float(config, "min_test_pf", 1.05),
            min_pass_rate=_get_float(config, "min_pass_rate", 0.6),
        ),
    )


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat()


def _coerce_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _get_int(config: dict, key: str, default: int) -> int:
    return int(config.get(key, default))


def _get_float(config: dict, key: str, default: float) -> float:
    return float(config.get(key, default))


def _get_round_value(round_result: Any, key: str) -> Any:
    if isinstance(round_result, dict):
        return round_result[key]
    return getattr(round_result, key)


if __name__ == "__main__":
    main()
