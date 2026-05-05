from __future__ import annotations

import json
from datetime import date
from typing import Any

from mqre_v2.reporting.wfo_report import wfo_run_result_to_dict
from mqre_v2.validation.wfo import (
    TxtWfoInput,
    WfoGateConfig,
    build_txt_evaluate_fn,
    default_optimize_fn,
    run_wfo,
)


def run_txt_wfo_from_config(config: dict) -> dict:
    strategy_name = str(config.get("strategy_name", "txt-strategy"))
    txt_input = TxtWfoInput(
        strategy_name=strategy_name,
        txt_path=str(config["txt_path"]),
    )

    result = run_wfo(
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

    payload = wfo_run_result_to_dict(result)
    payload["strategy_name"] = strategy_name
    return payload


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="mqquant 策略研究工作台", layout="wide")
    st.title("mqquant 策略研究工作台")

    with st.sidebar:
        txt_path = st.text_input("txt_path")
        strategy_name = st.text_input("strategy_name", value="txt-strategy")
        start_date = st.date_input("start_date", value=date(2020, 1, 1))
        end_date = st.date_input("end_date", value=date.today())
        train_months = st.number_input("train_months", min_value=1, value=36, step=1)
        gap_months = st.number_input("gap_months", min_value=1, value=1, step=1)
        test_months = st.number_input("test_months", min_value=1, value=6, step=1)
        step_months = st.number_input("step_months", min_value=1, value=6, step=1)
        min_test_trade_count = st.number_input(
            "min_test_trade_count",
            min_value=1,
            value=20,
            step=1,
        )
        max_test_mdd = st.number_input("max_test_mdd", min_value=0.0, value=15000.0)
        min_test_pf = st.number_input("min_test_pf", min_value=0.0, value=1.05)
        min_pass_rate = st.number_input(
            "min_pass_rate",
            min_value=0.0,
            max_value=1.0,
            value=0.6,
        )
        run_clicked = st.button("執行 WFO")

    if not run_clicked:
        return

    try:
        payload = run_txt_wfo_from_config(
            {
                "txt_path": txt_path,
                "strategy_name": strategy_name,
                "start_date": start_date,
                "end_date": end_date,
                "train_months": train_months,
                "gap_months": gap_months,
                "test_months": test_months,
                "step_months": step_months,
                "min_test_trade_count": min_test_trade_count,
                "max_test_mdd": max_test_mdd,
                "min_test_pf": min_test_pf,
                "min_pass_rate": min_pass_rate,
            }
        )
    except Exception as exc:
        st.error(str(exc))
        return

    _render_result(st, payload)


def _render_result(st: Any, payload: dict) -> None:
    if payload["passed"]:
        st.success("passed: True")
    else:
        st.error("passed: False")

    st.write({"fail_reason": payload["fail_reason"]})

    summary = payload["summary"]
    st.subheader("Summary")
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

    st.subheader("Round Results")
    st.dataframe(payload["round_results"], use_container_width=True)

    st.download_button(
        "下載 JSON",
        data=json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False),
        file_name="wfo_report.json",
        mime="application/json",
    )


def _coerce_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _get_int(config: dict, key: str, default: int) -> int:
    return int(config.get(key, default))


def _get_float(config: dict, key: str, default: float) -> float:
    return float(config.get(key, default))


if __name__ == "__main__":
    main()
