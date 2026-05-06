from __future__ import annotations

import json
import math
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from mqre_v2.backtest.costs import CostConfig, trade_cost_breakdown
from mqre_v2.io.txt_parser import parse_xs_txt
from mqre_v2.jobs.job_manager import JobStopped, is_stop_requested, update_progress
from mqre_v2.validation.decision import score_wfo_summary
from mqre_v2.validation.wfo import (
    TxtWfoInput,
    WfoGateConfig,
    build_txt_evaluate_fn,
    default_optimize_fn,
    run_wfo,
)

WINDOW_CONFIG_KEYS = {
    "train_months",
    "gap_months",
    "test_months",
    "step_months",
}

GATE_CONFIG_KEYS = {
    "min_test_trade_count",
    "max_test_mdd",
    "min_test_pf",
    "min_pass_rate",
    "require_positive_total_profit",
}


def run_txt_wfo_pipeline(
    txt_folder: str,
    start_date: date,
    end_date: date,
    gate_config: dict,
    txt_filenames: list[str] | None = None,
    include_wfo_details: bool = False,
    cost_config: CostConfig | None = None,
    strategy_quality: dict[str, dict[str, Any]] | None = None,
    job_id: str | None = None,
    job_base_dir: str = "runs/jobs",
) -> list[dict]:
    folder = Path(txt_folder)
    if not folder.is_dir():
        raise NotADirectoryError(f"txt_folder is not a directory: {folder}")

    effective_cost = cost_config or CostConfig()
    allowed_names = None
    if txt_filenames is not None:
        allowed_names = {Path(filename).name for filename in txt_filenames}

    txt_paths = [
        path
        for path in sorted(folder.glob("*.txt"))
        if path.is_file() and (allowed_names is None or path.name in allowed_names)
    ]
    if job_id:
        update_progress(
            job_id,
            {
                "total": len(txt_paths),
                "completed": 0,
                "current": "",
            },
            base_dir=job_base_dir,
        )

    results: list[dict] = []
    for index, txt_path in enumerate(txt_paths, start=1):
        if job_id and is_stop_requested(job_id, base_dir=job_base_dir):
            raise JobStopped(f"stop requested for job {job_id}")
        if job_id:
            update_progress(
                job_id,
                {
                    "total": len(txt_paths),
                    "completed": index - 1,
                    "current": txt_path.stem,
                },
                base_dir=job_base_dir,
            )
        if not txt_path.is_file():
            continue
        if allowed_names is not None and txt_path.name not in allowed_names:
            continue

        strategy_name = txt_path.stem
        try:
            all_trades = parse_xs_txt(txt_path.read_text(encoding="utf-8-sig"))
            wfo_result = run_wfo(
                start_date=start_date,
                end_date=end_date,
                strategy_name=strategy_name,
                optimize_fn=default_optimize_fn,
                evaluate_fn=build_txt_evaluate_fn(
                    TxtWfoInput(strategy_name=strategy_name, txt_path=str(txt_path)),
                    cost_config=effective_cost,
                ),
                window_kwargs=_build_window_kwargs(gate_config),
                gate_config=_build_gate_config(gate_config),
            )
            summary = wfo_result.summary
            trade_totals = _build_trade_totals(all_trades, effective_cost)
            result = {
                "rank": 0,
                "strategy_name": strategy_name,
                "txt_path": str(txt_path),
                "total_test_net_profit": _safe_number(summary.total_test_net_profit),
                "pass_rate": _safe_number(summary.pass_rate),
                "max_test_mdd": _safe_number(summary.max_test_mdd),
                "average_test_pf": _safe_number(summary.average_test_pf),
                "score": _safe_number(score_wfo_summary(summary)),
                "passed": wfo_result.passed,
                "fail_reason": wfo_result.fail_reason,
            }
            result.update(trade_totals)
            quality = (strategy_quality or {}).get(strategy_name, {})
            result.update(
                {
                    key: value
                    for key, value in quality.items()
                    if key not in {"fail_reasons"}
                }
            )
            fail_reasons = list(quality.get("fail_reasons", []))
            if fail_reasons:
                result["passed"] = False
                result["fail_reason"] = _append_fail_reason(
                    str(result.get("fail_reason", "")),
                    fail_reasons,
                )
                result["score"] = 0.0
            if include_wfo_details:
                result["summary"] = {
                    "total_rounds": summary.total_rounds,
                    "passed_rounds": summary.passed_rounds,
                    "failed_rounds": summary.failed_rounds,
                    "pass_rate": _safe_number(summary.pass_rate),
                    "total_test_net_profit": _safe_number(
                        summary.total_test_net_profit
                    ),
                    "average_test_net_profit": _safe_number(
                        summary.average_test_net_profit
                    ),
                    "max_test_mdd": _safe_number(summary.max_test_mdd),
                    "average_test_pf": _safe_number(summary.average_test_pf),
                    "total_test_trade_count": summary.total_test_trade_count,
                }
                result["round_results"] = [
                    {
                        "round_id": round_result.round_id,
                        "test_net_profit": _safe_number(
                            round_result.test_net_profit
                        ),
                        "test_mdd": _safe_number(round_result.test_mdd),
                        "test_pf": _safe_number(round_result.test_pf),
                        "test_trade_count": round_result.test_trade_count,
                        "pass_flag": round_result.pass_flag,
                        "fail_reason": round_result.fail_reason,
                    }
                    for round_result in wfo_result.round_results
                ]
        except Exception as exc:
            result = _failed_result(
                strategy_name=strategy_name,
                txt_path=txt_path,
                fail_reason=str(exc),
            )
            if include_wfo_details:
                result["summary"] = {}
                result["round_results"] = []

        results.append(result)
        if job_id:
            update_progress(
                job_id,
                {
                    "total": len(txt_paths),
                    "completed": index,
                    "current": strategy_name,
                },
                base_dir=job_base_dir,
            )

    results.sort(key=lambda item: float(item["score"]), reverse=True)
    for rank, result in enumerate(results, start=1):
        result["rank"] = rank
    return results


def export_pipeline_result(result: list[dict], output_path: str) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_strategies": len(result),
        "top_10": result[:10],
        "all_results": result,
    }
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )


def _build_window_kwargs(config: dict[str, Any]) -> dict[str, int]:
    window_kwargs: dict[str, int] = {}
    for key in WINDOW_CONFIG_KEYS:
        if key in config:
            window_kwargs[key] = int(config[key])
    return window_kwargs


def _build_gate_config(config: dict[str, Any]) -> WfoGateConfig:
    gate_kwargs = {key: config[key] for key in GATE_CONFIG_KEYS if key in config}
    if "min_test_trade_count" in gate_kwargs:
        gate_kwargs["min_test_trade_count"] = int(gate_kwargs["min_test_trade_count"])
    if "max_test_mdd" in gate_kwargs:
        gate_kwargs["max_test_mdd"] = float(gate_kwargs["max_test_mdd"])
    if "min_test_pf" in gate_kwargs:
        gate_kwargs["min_test_pf"] = float(gate_kwargs["min_test_pf"])
    if "min_pass_rate" in gate_kwargs:
        gate_kwargs["min_pass_rate"] = float(gate_kwargs["min_pass_rate"])
    if "require_positive_total_profit" in gate_kwargs:
        gate_kwargs["require_positive_total_profit"] = bool(
            gate_kwargs["require_positive_total_profit"]
        )
    return WfoGateConfig(**gate_kwargs)


def _failed_result(strategy_name: str, txt_path: Path, fail_reason: str) -> dict:
    return {
        "rank": 0,
        "strategy_name": strategy_name,
        "txt_path": str(txt_path),
        "total_test_net_profit": 0.0,
        "pass_rate": 0.0,
        "max_test_mdd": 0.0,
        "average_test_pf": 0.0,
        "score": 0.0,
        "passed": False,
        "fail_reason": fail_reason,
    }


def _build_trade_totals(
    trades: list,
    cost_config: CostConfig | None,
) -> dict[str, float]:
    raw_total = sum(float(trade.pnl) for trade in trades)
    if cost_config is None:
        net_total = raw_total
        slippage = 0.0
        fee = 0.0
        tax = 0.0
        total_cost = 0.0
    else:
        breakdowns = [trade_cost_breakdown(trade, cost_config) for trade in trades]
        net_total = sum(item["net_pnl"] for item in breakdowns)
        slippage = sum(item["slippage_cost"] for item in breakdowns)
        fee = sum(item["fee_cost"] for item in breakdowns)
        tax = sum(item["tax_cost"] for item in breakdowns)
        total_cost = sum(item["total_cost"] for item in breakdowns)

    trade_count = len(trades)
    trade_days = {trade.exit_time.date() for trade in trades}
    avg_trades_per_day = trade_count / len(trade_days) if trade_days else 0.0
    return {
        "raw_total_profit": _safe_number(raw_total),
        "net_total_profit": _safe_number(net_total),
        "total_slippage_cost": _safe_number(slippage),
        "total_fee_cost": _safe_number(fee),
        "total_tax_cost": _safe_number(tax),
        "total_cost": _safe_number(total_cost),
        "avg_net_pnl_per_trade": _safe_number(net_total / trade_count if trade_count else 0.0),
        "avg_trades_per_day": _safe_number(avg_trades_per_day),
    }


def _append_fail_reason(existing: str, reasons: list[str]) -> str:
    parts = [part.strip() for part in existing.split(";") if part.strip()]
    parts.extend(reason for reason in reasons if reason)
    return "; ".join(parts)


def _safe_number(value: float | int) -> float | str:
    number = float(value)
    if math.isnan(number):
        return "NaN"
    if math.isinf(number):
        return "Infinity" if number > 0 else "-Infinity"
    return number
