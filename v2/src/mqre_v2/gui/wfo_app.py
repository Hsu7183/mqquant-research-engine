from __future__ import annotations

import json
import math
from dataclasses import replace
from datetime import date, datetime, timezone
from itertools import product
from pathlib import Path
from typing import Any

import pandas as pd

from mqre_v2.optimizer.parameter_grid import expand_parameter_grid, load_parameter_grid
from mqre_v2.optimizer.xs_batch import generate_xs_batch
from mqre_v2.pipeline.txt_wfo_pipeline import (
    export_pipeline_result,
    run_txt_wfo_pipeline,
)
from mqre_v2.reporting.wfo_report import decision_result_to_dict, wfo_run_result_to_dict
from mqre_v2.validation.decision import compare_baseline_challenger, score_wfo_summary
from mqre_v2.validation.wfo import (
    TxtWfoInput,
    WfoGateConfig,
    WfoRoundResult,
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

OPTIMIZER_TABLE_COLUMNS = [
    "rank",
    "slippage",
    "fee",
    "min_pf",
    "total_test_net_profit",
    "pass_rate",
    "max_test_mdd",
    "average_test_pf",
    "score",
]

BATCH_RANKING_COLUMNS = [
    "rank",
    "strategy_name",
    "txt_path",
    "total_rounds",
    "passed_rounds",
    "failed_rounds",
    "pass_rate",
    "total_test_net_profit",
    "average_test_net_profit",
    "max_test_mdd",
    "average_test_pf",
    "total_test_trade_count",
    "passed",
    "fail_reason",
    "score",
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


def run_simple_optimizer(config: dict) -> list[dict]:
    strategy_name = str(config.get("strategy_name", "optimizer-strategy"))
    slippage_values = _parse_float_range(config.get("slippage_points_range", "1,2,3,4"))
    fee_values = _parse_float_range(config.get("fee_points_range", "0,1,2"))
    min_pf_values = _parse_float_range(config.get("min_test_pf_range", "1.0,1.1,1.2"))

    results: list[dict] = []
    for slippage, fee, min_pf in product(slippage_values, fee_values, min_pf_values):
        run_config = dict(config)
        run_config["slippage_points"] = slippage
        run_config["fee_points"] = fee
        run_config["min_test_pf"] = min_pf

        wfo_result = _run_wfo_for_txt(
            txt_path=str(config["base_txt_path"]),
            strategy_name=strategy_name,
            config=run_config,
        )
        summary = wfo_result.summary
        payload = wfo_run_result_to_dict(wfo_result)

        results.append(
            {
                "rank": 0,
                "slippage": slippage,
                "fee": fee,
                "min_pf": min_pf,
                "total_test_net_profit": _safe_number(summary.total_test_net_profit),
                "pass_rate": _safe_number(summary.pass_rate),
                "max_test_mdd": _safe_number(summary.max_test_mdd),
                "average_test_pf": _safe_number(summary.average_test_pf),
                "score": _safe_number(score_wfo_summary(summary)),
                "summary": payload["summary"],
                "round_results": payload["round_results"],
                "passed": payload["passed"],
                "fail_reason": payload["fail_reason"],
            }
        )

    results.sort(key=lambda item: float(item["score"]), reverse=True)
    for rank, result in enumerate(results, start=1):
        result["rank"] = rank
    return results


def load_parameter_grid_preview(path: str) -> dict:
    grid = load_parameter_grid(path)
    combinations = expand_parameter_grid(grid)
    return {
        "strategy_name": grid.strategy_name,
        "parameters": [
            {
                "name": name,
                "candidate_count": len(values),
            }
            for name, values in grid.parameters.items()
        ],
        "total_combinations": len(combinations),
    }


def generate_xs_batch_from_config(config: dict) -> dict:
    paths = generate_xs_batch(
        template_path=str(config["template_path"]),
        parameter_grid_path=str(config["parameter_grid_path"]),
        output_dir=str(config["output_dir"]),
    )
    return {
        "generated_at": _generated_at(),
        "generated_count": len(paths),
        "paths": paths,
        "filenames": [Path(path).name for path in paths],
    }


def run_batch_txt_ranking_from_config(config: dict) -> list[dict]:
    folder = Path(str(config["txt_folder_path"]))
    if not folder.is_dir():
        raise NotADirectoryError(f"txt_folder_path is not a directory: {folder}")

    file_pattern = str(config.get("file_pattern", "*.txt"))
    txt_paths = sorted(path for path in folder.glob(file_pattern) if path.is_file())

    results: list[dict] = []
    for txt_path in txt_paths:
        strategy_name = txt_path.stem
        try:
            wfo_result = _run_wfo_for_txt(
                txt_path=str(txt_path),
                strategy_name=strategy_name,
                config=config,
            )
            payload = wfo_run_result_to_dict(wfo_result)
            summary = wfo_result.summary
            score = score_wfo_summary(summary)

            result = {
                "rank": 0,
                "strategy_name": strategy_name,
                "txt_path": str(txt_path),
                "total_rounds": summary.total_rounds,
                "passed_rounds": summary.passed_rounds,
                "failed_rounds": summary.failed_rounds,
                "pass_rate": _safe_number(summary.pass_rate),
                "total_test_net_profit": _safe_number(summary.total_test_net_profit),
                "average_test_net_profit": _safe_number(summary.average_test_net_profit),
                "max_test_mdd": _safe_number(summary.max_test_mdd),
                "average_test_pf": _safe_number(summary.average_test_pf),
                "total_test_trade_count": summary.total_test_trade_count,
                "passed": wfo_result.passed,
                "fail_reason": wfo_result.fail_reason,
                "score": _safe_number(score),
                "summary": payload["summary"],
                "round_results": payload["round_results"],
            }
        except Exception as exc:
            result = _failed_batch_result(
                strategy_name=strategy_name,
                txt_path=txt_path,
                fail_reason=str(exc),
            )

        results.append(result)

    results.sort(key=lambda item: float(item["score"]), reverse=True)
    for rank, result in enumerate(results, start=1):
        result["rank"] = rank
    return results


def build_optimizer_dataframe(results: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(results)
    if df.empty:
        return pd.DataFrame(columns=OPTIMIZER_TABLE_COLUMNS)

    df = df[OPTIMIZER_TABLE_COLUMNS].copy()
    for column in OPTIMIZER_TABLE_COLUMNS:
        df[column] = pd.to_numeric(
            df[column].replace({"Infinity": float("inf"), "-Infinity": -float("inf")}),
            errors="coerce",
        )
    return df


def build_batch_ranking_dataframe(results: list[dict]) -> pd.DataFrame:
    if not results:
        return pd.DataFrame(columns=BATCH_RANKING_COLUMNS)
    return pd.DataFrame(results)[BATCH_RANKING_COLUMNS]


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

    single_mode = "單一策略 WFO"
    comparison_mode = "Baseline vs Challenger"
    optimizer_mode = "⭐ Optimizer（新增）"
    batch_mode = "批量 TXT 排名"
    with st.sidebar:
        mode = st.selectbox("mode", [single_mode, comparison_mode, optimizer_mode, batch_mode])

    if mode == single_mode:
        _render_single_wfo_mode(st)
    elif mode == comparison_mode:
        _render_baseline_challenger_mode(st)
    elif mode == optimizer_mode:
        _render_optimizer_mode(st)
    else:
        _render_batch_ranking_mode(st)


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


def _render_optimizer_mode(st: Any) -> None:
    with st.sidebar:
        base_txt_path = st.text_input("base_txt_path")
        strategy_name = st.text_input("strategy_name", value="optimizer-strategy")
        start_date = st.date_input("start_date", value=date(2020, 1, 1))
        end_date = st.date_input("end_date", value=date.today())
        slippage_points_range = st.text_input("slippage_points_range", value="1,2,3,4")
        fee_points_range = st.text_input("fee_points_range", value="0,1,2")
        min_test_pf_range = st.text_input("min_test_pf_range", value="1.0,1.1,1.2")
        st.subheader("策略參數空間")
        parameter_grid_path = st.text_input(
            "parameter_grid_path",
            value="configs/parameter_grid_0313.yaml",
        )
        st.subheader("XS 批次產生")
        template_path = st.text_input(
            "template_path",
            value="templates/xs/0313plus_template.xs",
        )
        output_dir = st.text_input("output_dir", value="outputs/xs_batch")
        generate_xs_clicked = st.button("產生 XS 批次")
        load_grid_clicked = st.button("載入參數空間")
        run_clicked = st.button("執行 Optimizer")

    if load_grid_clicked:
        try:
            preview = load_parameter_grid_preview(parameter_grid_path)
        except Exception as exc:
            st.error(str(exc))
        else:
            _render_parameter_grid_preview(st, preview)

    if generate_xs_clicked:
        try:
            xs_batch = generate_xs_batch_from_config(
                {
                    "template_path": template_path,
                    "parameter_grid_path": parameter_grid_path,
                    "output_dir": output_dir,
                }
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            _render_xs_batch_result(st, xs_batch)

    if not run_clicked:
        return

    try:
        results = run_simple_optimizer(
            {
                "base_txt_path": base_txt_path,
                "strategy_name": strategy_name,
                "start_date": start_date,
                "end_date": end_date,
                "slippage_points_range": slippage_points_range,
                "fee_points_range": fee_points_range,
                "min_test_pf_range": min_test_pf_range,
            }
        )
    except Exception as exc:
        st.error(str(exc))
        return

    _render_optimizer_result(st, results)


def _render_batch_ranking_mode(st: Any) -> None:
    with st.sidebar:
        txt_folder_path = st.text_input("txt_folder_path")
        file_pattern = st.text_input("file_pattern", value="*.txt")
        output_json_path = st.text_input(
            "output_json_path",
            value="outputs/txt_wfo_pipeline.json",
        )
        config = {
            "txt_folder_path": txt_folder_path,
            "file_pattern": file_pattern,
            **_wfo_parameter_inputs(st),
        }
        run_clicked = st.button("執行批量排名")
        pipeline_clicked = st.button("執行完整 Pipeline")

    if pipeline_clicked:
        try:
            pipeline_results = run_txt_wfo_pipeline(
                txt_folder=txt_folder_path,
                start_date=_coerce_date(config["start_date"]),
                end_date=_coerce_date(config["end_date"]),
                gate_config=config,
            )
            export_pipeline_result(pipeline_results, output_json_path)
        except Exception as exc:
            st.error(str(exc))
        else:
            _render_txt_wfo_pipeline_result(st, pipeline_results, output_json_path)

    if not run_clicked:
        return

    try:
        results = run_batch_txt_ranking_from_config(config)
    except Exception as exc:
        st.error(str(exc))
        return

    _render_batch_ranking_result(st, results)


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


def _render_optimizer_result(st: Any, results: list[dict]) -> None:
    if not results:
        st.warning("No optimizer results.")
        return

    optimizer_payload = {
        "generated_at": _generated_at(),
        "results": results,
    }
    table = build_optimizer_dataframe(results)

    st.subheader("Top 10")
    st.dataframe(table.head(10), use_container_width=True)

    top_result = results[0]
    st.subheader("Top 1 Strategy")
    st.write(
        {
            "slippage": top_result["slippage"],
            "fee": top_result["fee"],
            "min_pf": top_result["min_pf"],
            "score": top_result["score"],
            "total_test_net_profit": top_result["total_test_net_profit"],
            "pass_rate": top_result["pass_rate"],
        }
    )

    _render_summary(st, "Top 1 Summary", top_result["summary"])
    _render_round_charts(st, top_result["round_results"])

    st.download_button(
        "下載 Optimizer JSON",
        data=json.dumps(optimizer_payload, ensure_ascii=False, indent=2, allow_nan=False),
        file_name="optimizer_report.json",
        mime="application/json",
    )


def _render_parameter_grid_preview(st: Any, preview: dict) -> None:
    st.subheader("策略參數空間")
    st.write(
        {
            "strategy_name": preview["strategy_name"],
            "total_combinations": preview["total_combinations"],
        }
    )
    st.dataframe(pd.DataFrame(preview["parameters"]), use_container_width=True)


def _render_xs_batch_result(st: Any, result: dict) -> None:
    st.subheader("XS 批次產生結果")
    st.write({"generated_count": result["generated_count"]})
    st.dataframe(
        pd.DataFrame({"filename": result["filenames"][:5]}),
        use_container_width=True,
    )


def _render_batch_ranking_result(st: Any, results: list[dict]) -> None:
    if not results:
        st.warning("No TXT files matched the selected pattern.")
        return

    payload = {
        "generated_at": _generated_at(),
        "results": results,
    }
    table = build_batch_ranking_dataframe(results)

    st.subheader("策略排行榜")
    st.dataframe(table, use_container_width=True)

    st.subheader("Top 10")
    st.dataframe(table.head(10), use_container_width=True)

    top_result = results[0]
    st.subheader("第一名策略")
    st.write(
        {
            "strategy_name": top_result["strategy_name"],
            "txt_path": top_result["txt_path"],
            "score": top_result["score"],
            "total_test_net_profit": top_result["total_test_net_profit"],
            "pass_rate": top_result["pass_rate"],
            "passed": top_result["passed"],
            "fail_reason": top_result["fail_reason"],
        }
    )

    if top_result["round_results"]:
        _render_round_charts(st, top_result["round_results"])
    else:
        st.warning("第一名策略沒有可顯示的 WFO round results。")

    st.download_button(
        "下載批量排名 JSON",
        data=json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False),
        file_name="batch_txt_ranking_report.json",
        mime="application/json",
    )


def _render_txt_wfo_pipeline_result(
    st: Any,
    results: list[dict],
    output_json_path: str,
) -> None:
    if not results:
        st.warning("No TXT files matched the pipeline input.")
        st.write({"output_json_path": output_json_path})
        return

    payload = {
        "generated_at": _generated_at(),
        "total_strategies": len(results),
        "top_10": results[:10],
        "all_results": results,
    }
    table = pd.DataFrame(results)

    st.subheader("Pipeline Top 10")
    st.dataframe(table.head(10), use_container_width=True)
    st.write({"output_json_path": output_json_path})
    st.download_button(
        "下載 Pipeline JSON",
        data=json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False),
        file_name=Path(output_json_path).name,
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
    evaluate_fn = build_txt_evaluate_fn(txt_input)
    slippage_points = _get_float(config, "slippage_points", 0.0)
    fee_points = _get_float(config, "fee_points", 0.0)
    if slippage_points or fee_points:
        evaluate_fn = _build_cost_adjusted_evaluate_fn(
            evaluate_fn,
            slippage_points=slippage_points,
            fee_points=fee_points,
        )

    return run_wfo(
        start_date=_coerce_date(config["start_date"]),
        end_date=_coerce_date(config["end_date"]),
        strategy_name=strategy_name,
        optimize_fn=default_optimize_fn,
        evaluate_fn=evaluate_fn,
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


def _build_cost_adjusted_evaluate_fn(
    evaluate_fn: Any,
    *,
    slippage_points: float,
    fee_points: float,
) -> Any:
    per_trade_cost = slippage_points + fee_points

    def wrapped(window: Any, optimizer_result: Any) -> WfoRoundResult:
        round_result = evaluate_fn(window, optimizer_result)
        total_cost = per_trade_cost * round_result.test_trade_count
        return replace(
            round_result,
            test_net_profit=round_result.test_net_profit - total_cost,
            test_mdd=round_result.test_mdd + max(total_cost, 0.0),
        )

    return wrapped


def _failed_batch_result(strategy_name: str, txt_path: Path, fail_reason: str) -> dict:
    summary = _empty_summary_dict()
    return {
        "rank": 0,
        "strategy_name": strategy_name,
        "txt_path": str(txt_path),
        "total_rounds": 0,
        "passed_rounds": 0,
        "failed_rounds": 0,
        "pass_rate": 0.0,
        "total_test_net_profit": 0.0,
        "average_test_net_profit": 0.0,
        "max_test_mdd": 0.0,
        "average_test_pf": 0.0,
        "total_test_trade_count": 0,
        "passed": False,
        "fail_reason": fail_reason,
        "score": 0.0,
        "summary": summary,
        "round_results": [],
    }


def _empty_summary_dict() -> dict[str, float | int]:
    return {
        "total_rounds": 0,
        "passed_rounds": 0,
        "failed_rounds": 0,
        "pass_rate": 0.0,
        "total_test_net_profit": 0.0,
        "average_test_net_profit": 0.0,
        "max_test_mdd": 0.0,
        "average_test_pf": 0.0,
        "total_test_trade_count": 0,
    }


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


def _parse_float_range(value: Any) -> list[float]:
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",") if part.strip()]
    else:
        parts = list(value)

    if not parts:
        raise ValueError("range cannot be empty")

    return [float(part) for part in parts]


def _safe_number(value: float | int) -> float | str:
    number = float(value)
    if math.isnan(number):
        return "NaN"
    if math.isinf(number):
        return "Infinity" if number > 0 else "-Infinity"
    return number


def _get_round_value(round_result: Any, key: str) -> Any:
    if isinstance(round_result, dict):
        return round_result[key]
    return getattr(round_result, key)


if __name__ == "__main__":
    main()
