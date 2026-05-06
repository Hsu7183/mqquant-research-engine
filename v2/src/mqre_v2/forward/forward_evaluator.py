from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from mqre_v2.forward.forward_log import (
    ForwardTestRecord,
    read_forward_records,
    update_forward_status,
)
from mqre_v2.pipeline.txt_wfo_pipeline import run_txt_wfo_pipeline

DEFAULT_FORWARD_LOG_PATH = "runs/forward/forward_log.csv"
DEFAULT_FORWARD_REPORT_PATH = "runs/latest/forward_report.json"


@dataclass(frozen=True)
class ForwardEvaluationConfig:
    txt_folder: str
    start_date: date
    end_date: date
    forward_log_path: str
    promote_threshold_score: float = 100.0
    reject_threshold_score: float = 50.0


def evaluate_forward_performance(
    strategy_id: str,
    log_path: str = DEFAULT_FORWARD_LOG_PATH,
    output_path: str = DEFAULT_FORWARD_REPORT_PATH,
    backtest_summary_path: str = "runs/latest/ranking.json",
) -> dict[str, Any]:
    rows = _read_strategy_forward_rows(log_path, strategy_id)
    expected_pnl = _load_backtest_expected_pnl(strategy_id, backtest_summary_path)
    report = _build_forward_report(strategy_id, rows, expected_pnl)

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return report


def run_forward_evaluation(config: ForwardEvaluationConfig) -> dict[str, Any]:
    records = [
        record
        for record in read_forward_records(config.forward_log_path)
        if record.status == "forward_testing"
    ]

    promoted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    still_testing: list[dict[str, Any]] = []

    for record in records:
        evaluation = _evaluate_forward_record(record, config)
        score = float(evaluation["score"])

        if score >= config.promote_threshold_score:
            update_forward_status(
                config.forward_log_path,
                record.strategy_name,
                "promoted",
                notes=f"forward evaluation score={score}",
            )
            evaluation["status"] = "promoted"
            promoted.append(evaluation)
        elif score < config.reject_threshold_score:
            update_forward_status(
                config.forward_log_path,
                record.strategy_name,
                "rejected",
                notes=f"forward evaluation score={score}",
            )
            evaluation["status"] = "rejected"
            rejected.append(evaluation)
        else:
            evaluation["status"] = "forward_testing"
            still_testing.append(evaluation)

    return {
        "total_checked": len(records),
        "promoted": promoted,
        "rejected": rejected,
        "still_testing": still_testing,
    }


def _evaluate_forward_record(
    record: ForwardTestRecord,
    config: ForwardEvaluationConfig,
) -> dict[str, Any]:
    txt_path = _resolve_txt_path(record, config.txt_folder)
    result = _run_pipeline_for_strategy(record.strategy_name, txt_path, config)
    return {
        "strategy_name": record.strategy_name,
        "txt_path": str(txt_path),
        "score": float(result["score"]),
        "passed": result["passed"],
        "fail_reason": result["fail_reason"],
    }


def _run_pipeline_for_strategy(
    strategy_name: str,
    txt_path: Path,
    config: ForwardEvaluationConfig,
) -> dict[str, Any]:
    results = run_txt_wfo_pipeline(
        txt_folder=str(txt_path.parent),
        start_date=config.start_date,
        end_date=config.end_date,
        gate_config={},
    )
    resolved_txt_path = txt_path.resolve()
    for result in results:
        result_path = Path(str(result["txt_path"]))
        if result_path.exists() and result_path.resolve() == resolved_txt_path:
            return result
        if result["strategy_name"] == strategy_name:
            return result

    raise ValueError(f"strategy txt not found in pipeline results: {strategy_name}")


def _resolve_txt_path(record: ForwardTestRecord, txt_folder: str) -> Path:
    raw_path = Path(record.txt_path)
    candidates = []
    if raw_path.is_absolute():
        candidates.append(raw_path)
    else:
        folder = Path(txt_folder)
        candidates.extend(
            [
                folder / raw_path,
                folder / raw_path.name,
            ]
        )

    candidates.append(Path(txt_folder) / f"{record.strategy_name}.txt")

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


def _read_strategy_forward_rows(log_path: str, strategy_id: str) -> list[dict[str, Any]]:
    source = Path(log_path)
    if not source.exists():
        return []

    rows: list[dict[str, Any]] = []
    with source.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("strategy_id") != strategy_id:
                continue
            rows.append(
                {
                    "datetime": row.get("datetime", ""),
                    "strategy_id": strategy_id,
                    "price": _as_float(row.get("price")),
                    "pnl": _as_float(row.get("pnl")),
                    "cumulative_pnl": _as_float(row.get("cumulative_pnl")),
                }
            )
    return rows


def _build_forward_report(
    strategy_id: str,
    rows: list[dict[str, Any]],
    backtest_expected_pnl: float,
) -> dict[str, Any]:
    pnl_values = [_as_float(row.get("pnl")) for row in rows]
    cumulative_values = _cumulative_values(rows, pnl_values)
    total_pnl = sum(pnl_values)
    trade_count = len(pnl_values)
    max_drawdown = _max_drawdown(cumulative_values)
    win_rate = (
        sum(1 for value in pnl_values if value > 0) / trade_count
        if trade_count
        else 0.0
    )
    sharpe_estimate = _sharpe_estimate(pnl_values)
    vs_backtest_diff = total_pnl - backtest_expected_pnl
    vs_backtest_ratio = (
        total_pnl / backtest_expected_pnl
        if backtest_expected_pnl > 0
        else 0.0
    )
    stability_score = _stability_score(
        total_pnl=total_pnl,
        sharpe_estimate=sharpe_estimate,
        max_drawdown=max_drawdown,
        win_rate=win_rate,
        vs_backtest_ratio=vs_backtest_ratio,
        has_backtest=backtest_expected_pnl > 0,
    )
    is_deviating = total_pnl < 0 or (
        backtest_expected_pnl > 0 and total_pnl < backtest_expected_pnl * 0.5
    )
    forward_status = (
        "good"
        if stability_score >= 70.0 and not is_deviating
        else "warning"
        if stability_score >= 40.0
        else "bad"
    )

    return {
        "strategy_id": strategy_id,
        "trade_count": trade_count,
        "total_pnl": round(total_pnl, 6),
        "sharpe_estimate": round(sharpe_estimate, 6),
        "max_drawdown": round(max_drawdown, 6),
        "win_rate": round(win_rate, 6),
        "backtest_expected_pnl": round(backtest_expected_pnl, 6),
        "vs_backtest_diff": round(vs_backtest_diff, 6),
        "vs_backtest_ratio": round(vs_backtest_ratio, 6),
        "stability_score": round(stability_score, 6),
        "forward_status": forward_status,
        "is_deviating": is_deviating,
        "recommendation": "stop" if forward_status == "bad" or is_deviating else "continue",
    }


def _cumulative_values(
    rows: list[dict[str, Any]],
    pnl_values: list[float],
) -> list[float]:
    if rows and any("cumulative_pnl" in row for row in rows):
        return [_as_float(row.get("cumulative_pnl")) for row in rows]

    cumulative = 0.0
    values: list[float] = []
    for pnl in pnl_values:
        cumulative += pnl
        values.append(cumulative)
    return values


def _load_backtest_expected_pnl(strategy_id: str, path: str) -> float:
    source = Path(path)
    if not source.exists():
        return 0.0

    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return 0.0

    rows = payload
    if isinstance(payload, dict):
        rows = payload.get("top_10") or payload.get("all_results") or payload.get("ranking") or []

    if not isinstance(rows, list):
        return 0.0

    fallback: dict[str, Any] | None = None
    for row in rows:
        if not isinstance(row, dict):
            continue
        if fallback is None:
            fallback = row
        row_id = str(row.get("strategy_id") or row.get("strategy_name") or "")
        if row_id == strategy_id:
            return _expected_pnl_from_row(row)

    return _expected_pnl_from_row(fallback or {})


def _expected_pnl_from_row(row: dict[str, Any]) -> float:
    for key in [
        "total_test_net_profit",
        "net_total_profit",
        "total_pnl",
        "total_profit",
    ]:
        if key in row:
            return _as_float(row.get(key))
    if "annual_return" in row:
        return _as_float(row.get("annual_return")) * 100000.0
    return 0.0


def _sharpe_estimate(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0

    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    std = math.sqrt(variance)
    if std == 0:
        return 0.0
    return (mean / std) * math.sqrt(len(values))


def _max_drawdown(cumulative_values: list[float]) -> float:
    peak = 0.0
    max_dd = 0.0
    for value in cumulative_values:
        peak = max(peak, value)
        max_dd = max(max_dd, peak - value)
    return max_dd


def _stability_score(
    total_pnl: float,
    sharpe_estimate: float,
    max_drawdown: float,
    win_rate: float,
    vs_backtest_ratio: float,
    has_backtest: bool,
) -> float:
    score = 45.0
    score += 20.0 if total_pnl > 0 else -25.0
    score += max(0.0, min(20.0, sharpe_estimate * 8.0))
    score += max(0.0, min(20.0, win_rate * 25.0))

    if total_pnl > 0:
        score -= min(25.0, (max_drawdown / (abs(total_pnl) + 1.0)) * 20.0)
    elif max_drawdown > 0:
        score -= 15.0

    if has_backtest:
        if vs_backtest_ratio >= 0.75:
            score += 10.0
        elif vs_backtest_ratio >= 0.5:
            score += 2.0
        else:
            score -= 20.0

    return max(0.0, min(100.0, score))


def _as_float(value: object) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(number):
        return 0.0
    return number
