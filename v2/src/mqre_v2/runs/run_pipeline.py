from __future__ import annotations

import math
import json
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any

from mqre_v2.core.trades import TradeRecord
from mqre_v2.io.txt_parser import parse_xs_txt
from mqre_v2.pipeline.txt_wfo_pipeline import run_txt_wfo_pipeline
from mqre_v2.reporting.wfo_report import export_json_report
from mqre_v2.runs.run_manager import load_manifest, write_manifest
from mqre_v2.runs.run_txt_validator import validate_run_txt

STARTING_EQUITY = 100000.0


@dataclass(frozen=True)
class RunPipelineResult:
    run_id: str
    total_strategies: int
    valid_txt: int
    ranking: list[dict]
    output_json_path: str


def run_pipeline_from_run(
    run_path: str,
    start_date: date,
    end_date: date,
    output_filename: str = "ranking.json",
) -> RunPipelineResult:
    validation = validate_run_txt(run_path)
    if len(validation.valid_txt) == 0:
        raise ValueError("no valid TXT files for run pipeline")

    manifest = load_manifest(run_path)
    root = Path(run_path)
    txt_folder = root / "txt"
    ranking = run_txt_wfo_pipeline(
        txt_folder=str(txt_folder),
        start_date=start_date,
        end_date=end_date,
        gate_config={},
        txt_filenames=validation.valid_txt,
        include_wfo_details=True,
    )

    output_path = root / "reports" / output_filename
    report_rows = [_to_report_row(item) for item in ranking]
    _write_strategy_detail_reports(root, manifest.run_id, ranking)
    export_json_report(
        _build_report_payload(manifest.run_id, report_rows),
        str(output_path),
    )

    updated_manifest = replace(
        manifest,
        pipeline_completed=True,
        pipeline_total=len(ranking),
        pipeline_valid=len(validation.valid_txt),
    )
    write_manifest(run_path, updated_manifest)

    return RunPipelineResult(
        run_id=manifest.run_id,
        total_strategies=len(ranking),
        valid_txt=len(validation.valid_txt),
        ranking=ranking,
        output_json_path=str(output_path),
    )


def _build_report_payload(run_id: str, ranking: list[dict]) -> dict:
    return {
        "run_id": run_id,
        "summary": {
            "total_strategies": len(ranking),
            "valid_strategies": len(ranking),
        },
        "top_10": ranking[:10],
        "all_results": ranking,
    }


def write_ranking_summary_detail_reports(ranking_report_path: str) -> list[str]:
    source = Path(ranking_report_path)
    with source.open("r", encoding="utf-8") as handle:
        report = json.load(handle)

    run_id = str(report.get("run_id", source.parent.parent.name))
    ranking = report.get("all_results") or report.get("top_10") or []
    details_dir = source.parent / "details"
    details_dir.mkdir(parents=True, exist_ok=True)

    written_paths: list[str] = []
    for item in ranking:
        payload = _build_ranking_summary_detail_payload(run_id, item)
        detail_path = details_dir / f"{payload['strategy_name']}.json"
        detail_path.write_text(
            json.dumps(
                _json_safe(payload),
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            ),
            encoding="utf-8",
        )
        written_paths.append(str(detail_path))

    return written_paths


def _to_report_row(item: dict) -> dict:
    return {
        "rank": int(item["rank"]),
        "strategy_name": str(item["strategy_name"]),
        "score": _as_float(item["score"]),
        "total_test_net_profit": _as_float(item["total_test_net_profit"]),
        "pass_rate": _as_float(item["pass_rate"]),
        "max_test_mdd": _as_float(item["max_test_mdd"]),
        "average_test_pf": _as_float(item["average_test_pf"]),
    }


def _build_ranking_summary_detail_payload(run_id: str, item: dict) -> dict:
    score = _as_float(item["score"])
    total_profit = _as_float(item["total_test_net_profit"])
    pass_rate = _as_float(item["pass_rate"])
    max_mdd = _as_float(item["max_test_mdd"])
    average_pf = _as_float(item["average_test_pf"])

    return {
        "strategy_name": str(item["strategy_name"]),
        "run_id": run_id,
        "detail_source": "ranking_summary",
        "summary": {
            "score": score,
            "total_test_net_profit": total_profit,
            "pass_rate": pass_rate,
            "max_test_mdd": max_mdd,
            "average_test_pf": average_pf,
        },
        "period": {
            "start": "",
            "end": "",
        },
        "equity_curve": [],
        "weekly_pnl": [],
        "period_pnl": [],
        "kpi": {
            "score": score,
            "profit": total_profit,
            "pass_rate": pass_rate,
            "mdd": max_mdd,
            "pf": average_pf,
        },
    }


def _write_strategy_detail_reports(root: Path, run_id: str, ranking: list[dict]) -> list[str]:
    details_dir = root / "reports" / "details"
    details_dir.mkdir(parents=True, exist_ok=True)

    written_paths: list[str] = []
    for item in ranking:
        trades = parse_xs_txt(
            Path(str(item["txt_path"])).read_text(encoding="utf-8-sig")
        )
        weekly_series = build_weekly_series(trades)
        payload = _build_strategy_detail_payload(
            run_id,
            item,
            trades=trades,
            weekly_series=weekly_series,
        )
        detail_path = details_dir / f"{payload['strategy_name']}.json"
        detail_path.write_text(
            json.dumps(
                _json_safe(payload),
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            ),
            encoding="utf-8",
        )
        written_paths.append(str(detail_path))

    return written_paths


def build_weekly_series(trades: list[TradeRecord]) -> dict:
    weekly_totals: dict[str, float] = {}
    for trade in trades:
        iso_year, iso_week, _ = trade.exit_time.date().isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"
        weekly_totals[week_key] = weekly_totals.get(week_key, 0.0) + float(trade.pnl)

    equity = STARTING_EQUITY
    equity_curve = []
    weekly_pnl = []
    for week in sorted(weekly_totals):
        pnl = weekly_totals[week]
        equity += pnl
        weekly_pnl.append({"week": week, "pnl": pnl})
        equity_curve.append({"week": week, "equity": equity})

    return {
        "equity_curve": equity_curve,
        "weekly_pnl": weekly_pnl,
    }


def build_trade_period(trades: list[TradeRecord]) -> dict[str, str]:
    if not trades:
        return {"start": "", "end": ""}

    start = min(trade.entry_time for trade in trades).date().isoformat()
    end = max(trade.exit_time for trade in trades).date().isoformat()
    return {"start": start, "end": end}


def build_trade_stats(trades: list[TradeRecord], weekly_series: dict) -> dict:
    trade_count = len(trades)
    if trade_count == 0:
        return {
            "trade_count": 0,
            "long_count": 0,
            "short_count": 0,
            "win_count": 0,
            "loss_count": 0,
            "win_rate": 0.0,
            "total_profit": 0.0,
            "avg_trade_pnl": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "profit_factor": 0.0,
            "payoff_ratio": 0.0,
            "max_drawdown": 0.0,
            "underwater_weeks": 0,
            "max_losing_streak": 0,
        }

    pnls = [float(trade.pnl) for trade in trades]
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    avg_win = gross_profit / len(wins) if wins else 0.0
    avg_loss = gross_loss / len(losses) if losses else 0.0
    max_drawdown, underwater_weeks = _compute_weekly_risk(
        weekly_series.get("equity_curve", [])
    )

    return {
        "trade_count": trade_count,
        "long_count": sum(1 for trade in trades if trade.direction == 1),
        "short_count": sum(1 for trade in trades if trade.direction == -1),
        "win_count": len(wins),
        "loss_count": len(losses),
        "win_rate": len(wins) / trade_count,
        "total_profit": sum(pnls),
        "avg_trade_pnl": sum(pnls) / trade_count,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "largest_win": max(wins) if wins else 0.0,
        "largest_loss": abs(min(losses)) if losses else 0.0,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "profit_factor": _ratio_or_inf(gross_profit, gross_loss),
        "payoff_ratio": _ratio_or_inf(avg_win, avg_loss),
        "max_drawdown": max_drawdown,
        "underwater_weeks": underwater_weeks,
        "max_losing_streak": _max_losing_streak(trades),
    }


def _build_strategy_detail_payload(
    run_id: str,
    item: dict,
    trades: list[TradeRecord],
    weekly_series: dict,
) -> dict:
    period_pnl = []
    equity = 0.0

    for index, round_result in enumerate(item.get("round_results", []), start=1):
        pnl = _as_float(round_result.get("test_net_profit", 0.0))
        equity += pnl
        period_pnl.append({"index": index, "pnl": pnl})

    score = _as_float(item["score"])
    total_profit = _as_float(item["total_test_net_profit"])
    pass_rate = _as_float(item["pass_rate"])
    max_mdd = _as_float(item["max_test_mdd"])
    average_pf = _as_float(item["average_test_pf"])

    return {
        "strategy_name": str(item["strategy_name"]),
        "run_id": run_id,
        "summary": {
            "score": score,
            "total_test_net_profit": total_profit,
            "pass_rate": pass_rate,
            "max_test_mdd": max_mdd,
            "average_test_pf": average_pf,
        },
        "period": build_trade_period(trades),
        "trade_stats": build_trade_stats(trades, weekly_series),
        "equity_curve": weekly_series["equity_curve"],
        "weekly_pnl": weekly_series["weekly_pnl"],
        "period_pnl": period_pnl,
        "kpi": {
            "score": score,
            "profit": total_profit,
            "pass_rate": pass_rate,
            "mdd": max_mdd,
            "pf": average_pf,
        },
    }


def _ratio_or_inf(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return math.inf if numerator > 0 else 0.0
    return numerator / denominator


def _max_losing_streak(trades: list[TradeRecord]) -> int:
    current = 0
    max_streak = 0
    for trade in sorted(trades, key=lambda item: (item.exit_time, item.entry_time)):
        if trade.pnl < 0:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 0
    return max_streak


def _compute_weekly_risk(equity_curve: list[dict]) -> tuple[float, int]:
    peak = STARTING_EQUITY
    max_drawdown = 0.0
    underwater_weeks = 0

    for point in equity_curve:
        equity = float(point["equity"])
        if equity > peak:
            peak = equity
            continue

        drawdown = peak - equity
        if drawdown > 0:
            underwater_weeks += 1
            max_drawdown = max(max_drawdown, drawdown)

    return max_drawdown, underwater_weeks


def _as_float(value: object) -> float:
    if isinstance(value, str) and value in {"Infinity", "-Infinity", "NaN"}:
        return 5.0 if value == "Infinity" else 0.0

    number = float(value)
    if not math.isfinite(number):
        return 5.0 if number > 0 else 0.0
    return number


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            return "NaN"
        return "Infinity" if value > 0 else "-Infinity"
    return value
