from __future__ import annotations

import json
import math
from dataclasses import replace
from datetime import date, datetime, timezone
from itertools import product
from pathlib import Path
from typing import Any

import pandas as pd

from mqre_v2.automation.auto_research import AutoResearchConfig, run_auto_research
from mqre_v2.decision.audit_log import read_decision_audit
from mqre_v2.decision.promotion_pipeline import (
    AutoPromotionConfig,
    run_auto_promotion_pipeline,
)
from mqre_v2.decision.recommendation import export_recommendation_report
from mqre_v2.forward.forward_evaluator import (
    ForwardEvaluationConfig,
    run_forward_evaluation,
)
from mqre_v2.forward.forward_log import (
    ForwardTestRecord,
    append_forward_record,
    read_forward_records,
    update_forward_status,
)
from mqre_v2.optimizer.parameter_grid import expand_parameter_grid, load_parameter_grid
from mqre_v2.optimizer.xs_batch import generate_xs_batch
from mqre_v2.pipeline.txt_wfo_pipeline import (
    export_pipeline_result,
    run_txt_wfo_pipeline,
)
from mqre_v2.reporting.wfo_report import decision_result_to_dict, wfo_run_result_to_dict
from mqre_v2.runs.run_manager import RunManifest, create_run_directory, write_manifest
from mqre_v2.runs.run_pipeline import run_pipeline_from_run
from mqre_v2.runs.run_txt_validator import validate_run_txt
from mqre_v2.runs.run_xs_batch import generate_xs_into_run
from mqre_v2.strategy.registry import (
    promote_from_forward_log,
    read_strategy_registry,
    retire_strategy,
)
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


def create_run_manifest_from_config(config: dict) -> dict:
    parameter_grid_path = str(config["parameter_grid_path"])
    template_path = str(config["template_path"])
    strategy_name = str(config["strategy_name"])

    grid = load_parameter_grid(parameter_grid_path)
    total_combinations = len(expand_parameter_grid(grid))
    run_path = create_run_directory(
        base_dir=str(config.get("base_dir", "runs")),
        strategy_name=strategy_name,
    )
    run_id = Path(run_path).name
    manifest = RunManifest(
        run_id=run_id,
        strategy_name=strategy_name,
        created_at=_generated_at(),
        parameter_grid_path=parameter_grid_path,
        template_path=template_path,
        total_param_combinations=total_combinations,
        notes=str(config.get("notes", "")),
    )
    write_manifest(run_path, manifest)

    return {
        "run_id": run_id,
        "run_path": run_path,
        "total_param_combinations": total_combinations,
        "manifest": manifest.__dict__,
    }


def generate_xs_into_run_from_config(config: dict) -> dict:
    run_path = str(config["run_path"])
    output_paths = generate_xs_into_run(
        run_path=run_path,
        overwrite=bool(config.get("overwrite", False)),
    )
    return {
        "run_path": run_path,
        "xs_count": len(output_paths),
        "paths": output_paths,
        "filenames": [Path(path).name for path in output_paths],
    }


def validate_run_txt_from_config(config: dict) -> dict:
    result = validate_run_txt(str(config["run_path"]))
    return {
        "run_id": result.run_id,
        "total_xs": result.total_xs,
        "total_txt": result.total_txt,
        "matched": result.matched,
        "missing_txt": result.missing_txt,
        "extra_txt": result.extra_txt,
        "parse_failed": result.parse_failed,
        "valid_txt": result.valid_txt,
    }


def run_pipeline_from_run_config(config: dict) -> dict:
    result = run_pipeline_from_run(
        run_path=str(config["run_path"]),
        start_date=_coerce_date(config["start_date"]),
        end_date=_coerce_date(config["end_date"]),
        output_filename=str(config.get("output_filename", "ranking.json")),
    )
    return {
        "run_id": result.run_id,
        "total_strategies": result.total_strategies,
        "valid_txt": result.valid_txt,
        "ranking": result.ranking,
        "output_json_path": result.output_json_path,
    }


def generate_promotion_recommendation_from_config(config: dict) -> dict:
    return export_recommendation_report(
        ranking_report_path=str(config["ranking_report_path"]),
        output_path=str(config["output_recommendation_path"]),
        min_score=_get_float(config, "min_score", 100.0),
        min_pass_rate=_get_float(config, "min_pass_rate", 0.6),
        max_mdd=_get_float(config, "max_mdd", 15000.0),
        audit_log_path=(
            str(config["audit_log_path"]) if config.get("audit_log_path") else None
        ),
    )


def run_auto_promotion_from_config(config: dict) -> dict:
    return run_auto_promotion_pipeline(
        AutoPromotionConfig(
            ranking_report_path=str(config["ranking_report_path"]),
            recommendation_output_path=str(config["recommendation_output_path"]),
            audit_log_path=str(config["audit_log_path"]),
            min_score=_get_float(config, "min_score", 100.0),
            min_pass_rate=_get_float(config, "min_pass_rate", 0.6),
            max_mdd=_get_float(config, "max_mdd", 15000.0),
        )
    )


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


def manage_forward_status_from_config(config: dict) -> list[dict]:
    forward_log_path = str(config["forward_log_path"])
    update_forward_status(
        csv_path=forward_log_path,
        strategy_name=str(config["strategy_name"]),
        new_status=str(config["new_status"]),
        notes=str(config.get("notes", "")),
    )
    return [record.__dict__ for record in read_forward_records(forward_log_path)]


def promote_registry_from_config(config: dict) -> list[dict]:
    registry_csv_path = str(config["registry_csv_path"])
    promote_from_forward_log(
        forward_log_path=str(config["forward_log_path"]),
        registry_csv_path=registry_csv_path,
    )
    return [record.__dict__ for record in read_strategy_registry(registry_csv_path)]


def retire_strategy_from_config(config: dict) -> list[dict]:
    registry_csv_path = str(config["registry_csv_path"])
    retire_strategy(
        csv_path=registry_csv_path,
        strategy_name=str(config["strategy_name"]),
        notes=str(config.get("notes", "")),
    )
    return [record.__dict__ for record in read_strategy_registry(registry_csv_path)]


def run_auto_research_from_config(config: dict) -> dict:
    return run_auto_research(
        AutoResearchConfig(
            txt_folder=str(config["txt_folder"]),
            start_date=_coerce_date(config["start_date"]),
            end_date=_coerce_date(config["end_date"]),
            output_json_path=str(config["output_json_path"]),
            forward_log_path=str(config["forward_log_path"]),
            top_n=_get_int(config, "top_n", 10),
            auto_add_top1_to_forward=bool(
                config.get("auto_add_top1_to_forward", True)
            ),
            min_score_to_forward=_get_float(config, "min_score_to_forward", 0.0),
        )
    )


def run_forward_evaluation_from_config(config: dict) -> dict:
    return run_forward_evaluation(
        ForwardEvaluationConfig(
            txt_folder=str(config["txt_folder"]),
            start_date=_coerce_date(config["start_date"]),
            end_date=_coerce_date(config["end_date"]),
            forward_log_path=str(config["forward_log_path"]),
            promote_threshold_score=_get_float(
                config,
                "promote_threshold_score",
                100.0,
            ),
            reject_threshold_score=_get_float(
                config,
                "reject_threshold_score",
                50.0,
            ),
        )
    )


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
    forward_mode = "Forward Test 管理"
    auto_research_mode = "Auto Research Pipeline"
    forward_evaluation_mode = "Forward Evaluation"
    strategy_registry_mode = "Strategy Registry"
    promotion_recommendation_mode = "Promotion Recommendation"
    auto_promotion_mode = "Auto Promotion Pipeline"
    with st.sidebar:
        mode = st.selectbox(
            "mode",
            [
                single_mode,
                comparison_mode,
                optimizer_mode,
                batch_mode,
                forward_mode,
                auto_research_mode,
                forward_evaluation_mode,
                strategy_registry_mode,
                promotion_recommendation_mode,
                auto_promotion_mode,
            ],
        )

    if mode == single_mode:
        _render_single_wfo_mode(st)
    elif mode == comparison_mode:
        _render_baseline_challenger_mode(st)
    elif mode == optimizer_mode:
        _render_optimizer_mode(st)
    elif mode == batch_mode:
        _render_batch_ranking_mode(st)
    elif mode == forward_mode:
        _render_forward_management_mode(st)
    elif mode == auto_research_mode:
        _render_auto_research_mode(st)
    elif mode == forward_evaluation_mode:
        _render_forward_evaluation_mode(st)
    elif mode == strategy_registry_mode:
        _render_strategy_registry_mode(st)
    elif mode == promotion_recommendation_mode:
        _render_promotion_recommendation_mode(st)
    else:
        _render_auto_promotion_mode(st)


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
        st.subheader("建立 Run 批次")
        base_dir = st.text_input("base_dir", value="runs")
        create_run_clicked = st.button("建立 Run")
        run_path = st.text_input("run_path")
        generate_run_xs_clicked = st.button("產生 XS 到 Run")
        validate_run_txt_clicked = st.button("驗證 TXT 完整性")
        run_pipeline_clicked = st.button("執行 Run Pipeline")
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

    if create_run_clicked:
        try:
            run_result = create_run_manifest_from_config(
                {
                    "base_dir": base_dir,
                    "strategy_name": strategy_name,
                    "parameter_grid_path": parameter_grid_path,
                    "template_path": template_path,
                }
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            _set_session_value(st, "last_run_path", run_result["run_path"])
            _render_run_manifest_result(st, run_result)

    if generate_run_xs_clicked:
        target_run_path = run_path or _get_session_value(st, "last_run_path", "")
        try:
            xs_result = generate_xs_into_run_from_config(
                {
                    "run_path": target_run_path,
                }
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            _render_run_xs_batch_result(st, xs_result)

    if validate_run_txt_clicked:
        target_run_path = run_path or _get_session_value(st, "last_run_path", "")
        try:
            validation_result = validate_run_txt_from_config(
                {
                    "run_path": target_run_path,
                }
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            _render_run_txt_validation_result(st, validation_result)

    if run_pipeline_clicked:
        target_run_path = run_path or _get_session_value(st, "last_run_path", "")
        try:
            pipeline_result = run_pipeline_from_run_config(
                {
                    "run_path": target_run_path,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            _render_run_pipeline_result(st, pipeline_result)

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
        forward_log_path = st.text_input(
            "forward_log_path",
            value="reports/forward_test_log.csv",
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
            _set_session_value(st, "txt_wfo_pipeline_results", pipeline_results)
            _set_session_value(st, "txt_wfo_pipeline_output_json_path", output_json_path)

    pipeline_results = _get_session_value(st, "txt_wfo_pipeline_results")
    pipeline_output_json_path = _get_session_value(
        st,
        "txt_wfo_pipeline_output_json_path",
        output_json_path,
    )
    if pipeline_results is not None:
        _render_txt_wfo_pipeline_result(
            st,
            pipeline_results,
            pipeline_output_json_path,
            forward_log_path,
        )

    if not run_clicked:
        return

    try:
        results = run_batch_txt_ranking_from_config(config)
    except Exception as exc:
        st.error(str(exc))
        return

    _render_batch_ranking_result(st, results)


def _render_forward_management_mode(st: Any) -> None:
    with st.sidebar:
        forward_log_path = st.text_input(
            "forward_log_path",
            value="reports/forward_test_log.csv",
        )
        strategy_name = st.text_input("strategy_name")
        new_status = st.selectbox(
            "new_status",
            ["candidate", "forward_testing", "promoted", "rejected"],
        )
        notes = st.text_area("notes")
        update_clicked = st.button("更新策略狀態")

    if update_clicked:
        try:
            records = manage_forward_status_from_config(
                {
                    "forward_log_path": forward_log_path,
                    "strategy_name": strategy_name,
                    "new_status": new_status,
                    "notes": notes,
                }
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            st.success(f"Updated {strategy_name} to {new_status}.")
            _render_forward_records_table(st, forward_log_path, records)
        return

    records = [record.__dict__ for record in read_forward_records(forward_log_path)]
    _render_forward_records_table(st, forward_log_path, records)


def _render_auto_research_mode(st: Any) -> None:
    with st.sidebar:
        txt_folder = st.text_input("txt_folder")
        start_date = st.date_input("start_date", value=date(2020, 1, 1))
        end_date = st.date_input("end_date", value=date.today())
        output_json_path = st.text_input(
            "output_json_path",
            value="outputs/auto_research_ranking.json",
        )
        forward_log_path = st.text_input(
            "forward_log_path",
            value="reports/forward_test_log.csv",
        )
        top_n = st.number_input("top_n", min_value=1, value=10, step=1)
        min_score_to_forward = st.number_input(
            "min_score_to_forward",
            value=0.0,
        )
        auto_add_top1_to_forward = st.checkbox(
            "auto_add_top1_to_forward",
            value=True,
        )
        run_clicked = st.button("執行 Auto Research")

    if not run_clicked:
        return

    try:
        summary = run_auto_research_from_config(
            {
                "txt_folder": txt_folder,
                "start_date": start_date,
                "end_date": end_date,
                "output_json_path": output_json_path,
                "forward_log_path": forward_log_path,
                "top_n": top_n,
                "min_score_to_forward": min_score_to_forward,
                "auto_add_top1_to_forward": auto_add_top1_to_forward,
            }
        )
    except Exception as exc:
        st.error(str(exc))
        return

    _render_auto_research_result(st, summary)


def _render_forward_evaluation_mode(st: Any) -> None:
    with st.sidebar:
        txt_folder = st.text_input("txt_folder")
        start_date = st.date_input("start_date", value=date(2020, 1, 1))
        end_date = st.date_input("end_date", value=date.today())
        forward_log_path = st.text_input(
            "forward_log_path",
            value="reports/forward_test_log.csv",
        )
        promote_threshold_score = st.number_input(
            "promote_threshold_score",
            value=100.0,
        )
        reject_threshold_score = st.number_input(
            "reject_threshold_score",
            value=50.0,
        )
        run_clicked = st.button("執行 Forward Evaluation")

    if not run_clicked:
        return

    try:
        result = run_forward_evaluation_from_config(
            {
                "txt_folder": txt_folder,
                "start_date": start_date,
                "end_date": end_date,
                "forward_log_path": forward_log_path,
                "promote_threshold_score": promote_threshold_score,
                "reject_threshold_score": reject_threshold_score,
            }
        )
    except Exception as exc:
        st.error(str(exc))
        return

    _render_forward_evaluation_result(st, result)


def _render_strategy_registry_mode(st: Any) -> None:
    with st.sidebar:
        forward_log_path = st.text_input(
            "forward_log_path",
            value="reports/forward_test_log.csv",
        )
        registry_csv_path = st.text_input(
            "registry_csv_path",
            value="reports/strategy_registry.csv",
        )
        import_clicked = st.button("從 Forward Log 匯入 promoted 策略")
        strategy_name = st.text_input("strategy_name")
        notes = st.text_area("notes")
        retire_clicked = st.button("退役策略")

    if import_clicked:
        try:
            records = promote_registry_from_config(
                {
                    "forward_log_path": forward_log_path,
                    "registry_csv_path": registry_csv_path,
                }
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            st.success("Imported promoted strategies from forward log.")
            _render_strategy_registry_table(st, registry_csv_path, records)
        return

    if retire_clicked:
        try:
            records = retire_strategy_from_config(
                {
                    "registry_csv_path": registry_csv_path,
                    "strategy_name": strategy_name,
                    "notes": notes,
                }
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            st.success(f"Retired {strategy_name}.")
            _render_strategy_registry_table(st, registry_csv_path, records)
        return

    records = [record.__dict__ for record in read_strategy_registry(registry_csv_path)]
    _render_strategy_registry_table(st, registry_csv_path, records)


def _render_promotion_recommendation_mode(st: Any) -> None:
    with st.sidebar:
        ranking_report_path = st.text_input(
            "ranking_report_path",
            value="dashboard/sample_ranking.json",
        )
        output_recommendation_path = st.text_input(
            "output_recommendation_path",
            value="reports/promotion_recommendation.json",
        )
        audit_log_path = st.text_input(
            "audit_log_path",
            value="reports/decision_audit_log.csv",
        )
        min_score = st.number_input("min_score", value=100.0)
        min_pass_rate = st.number_input(
            "min_pass_rate",
            min_value=0.0,
            max_value=1.0,
            value=0.6,
        )
        max_mdd = st.number_input("max_mdd", min_value=0.0, value=15000.0)
        run_clicked = st.button("產生升級建議")

    if not run_clicked:
        return

    try:
        payload = generate_promotion_recommendation_from_config(
            {
                "ranking_report_path": ranking_report_path,
                "output_recommendation_path": output_recommendation_path,
                "audit_log_path": audit_log_path,
                "min_score": min_score,
                "min_pass_rate": min_pass_rate,
                "max_mdd": max_mdd,
            }
        )
    except Exception as exc:
        st.error(str(exc))
        return

    _render_promotion_recommendation_result(st, payload)
    _render_decision_audit_table(st, audit_log_path)


def _render_auto_promotion_mode(st: Any) -> None:
    with st.sidebar:
        ranking_report_path = st.text_input(
            "ranking_report_path",
            value="dashboard/sample_ranking.json",
        )
        recommendation_output_path = st.text_input(
            "recommendation_output_path",
            value="reports/auto_promotion_recommendation.json",
        )
        audit_log_path = st.text_input(
            "audit_log_path",
            value="reports/decision_audit_log.csv",
        )
        min_score = st.number_input("min_score", value=100.0)
        min_pass_rate = st.number_input(
            "min_pass_rate",
            value=0.6,
            min_value=0.0,
            max_value=1.0,
            step=0.05,
        )
        max_mdd = st.number_input("max_mdd", value=15000.0)
        run_button = st.button("執行 Auto Promotion")

    if not run_button:
        st.info("設定 ranking report 與門檻後，按下執行 Auto Promotion。")
        _render_decision_audit_table(st, audit_log_path)
        return

    try:
        payload = run_auto_promotion_from_config(
            {
                "ranking_report_path": ranking_report_path,
                "recommendation_output_path": recommendation_output_path,
                "audit_log_path": audit_log_path,
                "min_score": min_score,
                "min_pass_rate": min_pass_rate,
                "max_mdd": max_mdd,
            }
        )
    except Exception as exc:
        st.error(str(exc))
        return

    _render_auto_promotion_result(st, payload)
    _render_decision_audit_table(st, audit_log_path)


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


def _render_run_manifest_result(st: Any, result: dict) -> None:
    st.subheader("建立 Run 批次")
    st.write(
        {
            "run_id": result["run_id"],
            "run_path": result["run_path"],
            "total_param_combinations": result["total_param_combinations"],
        }
    )
    st.json(result["manifest"])


def _render_run_xs_batch_result(st: Any, result: dict) -> None:
    st.subheader("產生 XS 到 Run")
    st.write(
        {
            "run_path": result["run_path"],
            "xs_count": result["xs_count"],
        }
    )
    st.dataframe(
        pd.DataFrame({"filename": result["filenames"][:5]}),
        use_container_width=True,
    )


def _render_run_txt_validation_result(st: Any, result: dict) -> None:
    st.subheader("驗證 TXT 完整性")
    st.write(
        {
            "total_xs": result["total_xs"],
            "total_txt": result["total_txt"],
            "matched": result["matched"],
            "missing_txt_count": len(result["missing_txt"]),
            "parse_failed_count": len(result["parse_failed"]),
        }
    )
    st.subheader("Missing TXT")
    st.dataframe(
        pd.DataFrame({"filename": result["missing_txt"][:5]}),
        use_container_width=True,
    )
    st.subheader("Parse Failed TXT")
    st.dataframe(
        pd.DataFrame({"filename": result["parse_failed"][:5]}),
        use_container_width=True,
    )


def _render_run_pipeline_result(st: Any, result: dict) -> None:
    st.subheader("執行 Run Pipeline")
    st.write(
        {
            "total_strategies": result["total_strategies"],
            "valid_txt": result["valid_txt"],
            "output_json_path": result["output_json_path"],
        }
    )
    st.subheader("Top 10")
    st.dataframe(pd.DataFrame(result["ranking"][:10]), use_container_width=True)


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
    forward_log_path: str,
) -> None:
    if not results:
        st.warning("No TXT files matched the pipeline input.")
        st.write({"output_json_path": output_json_path})
        _render_forward_log_table(st, forward_log_path)
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
    _render_forward_test_controls(st, results, forward_log_path)


def _render_auto_research_result(st: Any, summary: dict) -> None:
    st.subheader("Auto Research Summary")
    st.write(
        {
            "total_strategies": summary["total_strategies"],
            "added_to_forward": summary["added_to_forward"],
            "output_json_path": summary["output_json_path"],
            "forward_log_path": summary["forward_log_path"],
            "notes": summary["notes"],
        }
    )

    st.subheader("Top 1")
    st.write(summary["top1"])

    st.subheader("Top N")
    st.dataframe(pd.DataFrame(summary["top_n"]), use_container_width=True)


def _render_forward_evaluation_result(st: Any, result: dict) -> None:
    st.subheader("Forward Evaluation Summary")
    st.write({"total_checked": result["total_checked"]})

    st.subheader("Promoted")
    st.dataframe(pd.DataFrame(result["promoted"]), use_container_width=True)

    st.subheader("Rejected")
    st.dataframe(pd.DataFrame(result["rejected"]), use_container_width=True)

    st.subheader("Still Testing")
    st.dataframe(pd.DataFrame(result["still_testing"]), use_container_width=True)


def _render_forward_test_controls(
    st: Any,
    results: list[dict],
    forward_log_path: str,
) -> None:
    st.subheader("Forward Test")
    top_result = results[0]
    st.write(
        {
            "top1_strategy_name": top_result["strategy_name"],
            "top1_txt_path": top_result["txt_path"],
            "top1_score": top_result["score"],
        }
    )

    if st.button("加入 Forward Test 觀察"):
        record = _build_forward_record_from_pipeline_result(top_result)
        try:
            append_forward_record(forward_log_path, record)
        except Exception as exc:
            st.error(str(exc))
        else:
            st.success(f"Added {record.strategy_name} to forward test log.")

    _render_forward_log_table(st, forward_log_path)


def _render_forward_log_table(st: Any, forward_log_path: str) -> None:
    records = read_forward_records(forward_log_path)
    _render_forward_records_table(
        st,
        forward_log_path,
        [record.__dict__ for record in records],
    )


def _render_forward_records_table(
    st: Any,
    forward_log_path: str,
    records: list[dict],
) -> None:
    st.subheader("Forward Test Log")
    st.write({"forward_log_path": forward_log_path})
    st.dataframe(pd.DataFrame(records), use_container_width=True)


def _render_strategy_registry_table(
    st: Any,
    registry_csv_path: str,
    records: list[dict],
) -> None:
    st.subheader("Strategy Registry")
    st.write({"registry_csv_path": registry_csv_path})
    st.dataframe(pd.DataFrame(records), use_container_width=True)


def _render_promotion_recommendation_result(st: Any, payload: dict) -> None:
    recommendation = payload["recommendation"]
    st.subheader("Promotion Recommendation")
    st.write(
        {
            "recommend_promote": recommendation["recommend_promote"],
            "strategy_name": recommendation["strategy_name"],
            "score": recommendation["score"],
            "reason": recommendation["reason"],
            "requires_human_review": recommendation["requires_human_review"],
        }
    )
    st.subheader("Risk Warnings")
    st.dataframe(
        pd.DataFrame({"warning": recommendation["risk_warnings"]}),
        use_container_width=True,
    )


def _render_auto_promotion_result(st: Any, payload: dict) -> None:
    st.subheader("Auto Promotion Pipeline")
    st.write(
        {
            "recommend_promote": payload["recommend_promote"],
            "strategy_name": payload["strategy_name"],
            "score": payload["score"],
            "reason": payload["reason"],
            "risk_warnings": payload["risk_warnings"],
            "requires_human_review": payload["requires_human_review"],
            "recommendation_output_path": payload["recommendation_output_path"],
            "audit_log_path": payload["audit_log_path"],
        }
    )


def _render_decision_audit_table(st: Any, audit_log_path: str) -> None:
    records = read_decision_audit(audit_log_path)
    st.subheader("Decision Audit Log")
    st.write({"audit_log_path": audit_log_path})
    st.dataframe(
        pd.DataFrame([record.__dict__ for record in records]),
        use_container_width=True,
    )


def _build_forward_record_from_pipeline_result(result: dict) -> ForwardTestRecord:
    timestamp = _generated_at()
    return ForwardTestRecord(
        strategy_name=str(result["strategy_name"]),
        txt_path=str(result["txt_path"]),
        status="candidate",
        created_at=timestamp,
        updated_at=timestamp,
        source_score=float(result["score"]),
        source_pass_rate=float(result["pass_rate"]),
        source_total_test_net_profit=float(result["total_test_net_profit"]),
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


def _set_session_value(st: Any, key: str, value: Any) -> None:
    session_state = getattr(st, "session_state", None)
    if session_state is not None:
        session_state[key] = value


def _get_session_value(st: Any, key: str, default: Any = None) -> Any:
    session_state = getattr(st, "session_state", None)
    if session_state is None:
        return default
    return session_state.get(key, default)


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
