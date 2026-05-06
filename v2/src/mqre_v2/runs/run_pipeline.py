from __future__ import annotations

import math
import json
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any

from mqre_v2.backtest.costs import CostConfig, net_pnl_points_for_trade, trade_cost_breakdown
from mqre_v2.core.trades import TradeRecord
from mqre_v2.export.artifact_exporter import export_latest_run
from mqre_v2.io.txt_parser import parse_xs_txt
from mqre_v2.jobs.job_manager import (
    JobStopped,
    complete_job,
    create_job,
    fail_job,
    stop_job,
)
from mqre_v2.pipeline.txt_wfo_pipeline import run_txt_wfo_pipeline
from mqre_v2.reporting.wfo_report import export_json_report
from mqre_v2.runs.run_manager import load_manifest, write_manifest
from mqre_v2.runs.run_txt_validator import validate_run_txt
from mqre_v2.validation.cost_stress import run_cost_stress

STARTING_EQUITY = 100000.0


@dataclass(frozen=True)
class RunPipelineResult:
    run_id: str
    total_strategies: int
    valid_txt: int
    ranking: list[dict]
    output_json_path: str
    job_id: str


def run_pipeline_from_run(
    run_path: str,
    start_date: date,
    end_date: date,
    output_filename: str = "ranking.json",
    cost_config: CostConfig | None = None,
    job_id: str | None = None,
    job_base_dir: str | None = None,
) -> RunPipelineResult:
    root = Path(run_path)
    effective_job_base = job_base_dir or str(root.parent / "jobs")
    effective_job_id = job_id or create_job(base_dir=effective_job_base)
    try:
        validation = validate_run_txt(run_path)
        if len(validation.valid_txt) == 0:
            raise ValueError("no valid TXT files for run pipeline")

        manifest = load_manifest(run_path)
        txt_folder = root / "txt"
        effective_cost = cost_config or CostConfig()
        ranking = run_txt_wfo_pipeline(
            txt_folder=str(txt_folder),
            start_date=start_date,
            end_date=end_date,
            gate_config={},
            txt_filenames=validation.valid_txt,
            include_wfo_details=True,
            cost_config=effective_cost,
            job_id=effective_job_id,
            job_base_dir=effective_job_base,
        )

        output_path = root / "reports" / output_filename
        report_rows = [_to_report_row(item) for item in ranking]
        _write_strategy_detail_reports(root, manifest.run_id, ranking, effective_cost)
        export_dashboard_artifacts_from_ranking(
            root=root,
            run_id=manifest.run_id,
            ranking=ranking,
            cost_config=effective_cost,
        )
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
        complete_job(effective_job_id, base_dir=effective_job_base)

        return RunPipelineResult(
            run_id=manifest.run_id,
            total_strategies=len(ranking),
            valid_txt=len(validation.valid_txt),
            ranking=ranking,
            output_json_path=str(output_path),
            job_id=effective_job_id,
        )
    except JobStopped:
        stop_job(effective_job_id, base_dir=effective_job_base)
        raise
    except Exception as exc:
        fail_job(effective_job_id, str(exc), base_dir=effective_job_base)
        raise


def export_dashboard_artifacts_from_ranking(
    root: Path,
    run_id: str,
    ranking: list[dict],
    cost_config: CostConfig | None = None,
) -> list[str]:
    top_item = ranking[0] if ranking else {}
    trades = _read_artifact_trades(top_item)
    artifact_result: dict[str, Any] = {
        "ranking": ranking,
        "strategy_detail": _build_dashboard_strategy_detail(
            top_item,
            trades=trades,
            cost_config=cost_config,
        ),
        "wfo_summary": _build_dashboard_wfo_summary(top_item),
        "risk_report": _build_dashboard_risk_report(top_item, trades, cost_config),
        "decision_audit": {
            "baseline_strategy": f"{run_id}_baseline",
            "challenger_strategy": str(
                top_item.get("strategy_name")
                or top_item.get("strategy_id")
                or "1001plus_candidate"
            ),
            "promotion_decision": "review_required",
            "reason": "pipeline completed; dashboard artifacts exported for human review",
        },
    }
    if trades:
        artifact_result["trades"] = _build_dashboard_trade_rows(trades, cost_config)
        artifact_result["equity_curve"] = _build_dashboard_equity_curve(
            trades,
            cost_config,
        )

    return export_latest_run(artifact_result, output_dir=str(root))


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
    row = {
        "rank": int(item["rank"]),
        "strategy_name": str(item["strategy_name"]),
        "score": _as_float(item["score"]),
        "total_test_net_profit": _as_float(item["total_test_net_profit"]),
        "pass_rate": _as_float(item["pass_rate"]),
        "max_test_mdd": _as_float(item["max_test_mdd"]),
        "average_test_pf": _as_float(item["average_test_pf"]),
    }
    for key in [
        "raw_total_profit",
        "net_total_profit",
        "total_slippage_cost",
        "total_fee_cost",
        "total_tax_cost",
        "total_cost",
        "avg_net_pnl_per_trade",
        "avg_trades_per_day",
    ]:
        if key in item:
            row[key] = _as_float(item[key])
    if "passed" in item:
        row["passed"] = bool(item["passed"])
    if "fail_reason" in item:
        row["fail_reason"] = str(item["fail_reason"])
    return row


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


def _read_artifact_trades(item: dict) -> list[TradeRecord]:
    txt_path = item.get("txt_path")
    if not txt_path:
        return []
    try:
        return parse_xs_txt(Path(str(txt_path)).read_text(encoding="utf-8-sig"))
    except Exception:
        return []


def _build_dashboard_strategy_detail(
    item: dict,
    trades: list[TradeRecord],
    cost_config: CostConfig | None,
) -> dict:
    strategy_id = str(
        item.get("strategy_id")
        or item.get("strategy_name")
        or "1001plus_candidate"
    )
    weekly_series = build_weekly_series(trades, cost_config=cost_config)
    trade_stats = build_trade_stats(
        trades,
        weekly_series=weekly_series,
        cost_config=cost_config,
    )
    net_profit = _as_float(
        item.get(
            "net_total_profit",
            item.get("total_test_net_profit", trade_stats["net_total_profit"]),
        )
    )
    trade_count = int(trade_stats["trade_count"]) if trades else int(
        _as_float(item.get("total_test_trade_count", 0.0))
    )
    return {
        "strategy_id": strategy_id,
        "params": {
            "source": "v2_pipeline",
            "txt_path": str(item.get("txt_path", "")),
        },
        "performance": {
            "return": net_profit / STARTING_EQUITY,
            "annual_return": net_profit / STARTING_EQUITY,
            "sharpe": _as_float(item.get("average_test_pf", 0.0)),
            "mdd": _as_float(item.get("max_test_mdd", trade_stats["max_drawdown"])),
            "win_rate": _as_float(trade_stats["win_rate"]),
            "profit_factor": _as_float(item.get("average_test_pf", trade_stats["profit_factor"])),
            "trade_count": trade_count,
            "average_trade_pnl": _as_float(
                item.get("avg_net_pnl_per_trade", trade_stats["avg_net_pnl_per_trade"])
            ),
            "net_total_profit": net_profit,
            "raw_total_profit": _as_float(
                item.get("raw_total_profit", trade_stats["raw_total_profit"])
            ),
        },
        "cost_model": _dashboard_cost_model(cost_config, trade_stats),
        "entry_logic_summary": "Exported from v2 pipeline Trade TXT results.",
        "exit_logic_summary": "Exported from completed TradeRecord exits; strategy logic remains upstream.",
        "tags": ["1001plus", "v2_pipeline"],
    }


def _build_dashboard_trade_rows(
    trades: list[TradeRecord],
    cost_config: CostConfig | None,
) -> list[dict]:
    rows: list[dict] = []
    cumulative = 0.0
    for trade in sorted(trades, key=lambda item: item.exit_time):
        pnl = _trade_pnl(trade, cost_config)
        cumulative += pnl
        rows.append(
            {
                "datetime": trade.exit_time,
                "price": trade.exit_price,
                "side": "buy" if trade.direction == 1 else "sell",
                "pnl": pnl,
                "cumulative_pnl": cumulative,
            }
        )
    return rows


def _build_dashboard_equity_curve(
    trades: list[TradeRecord],
    cost_config: CostConfig | None,
) -> list[dict]:
    rows: list[dict] = []
    equity = STARTING_EQUITY
    peak = equity
    for trade in sorted(trades, key=lambda item: item.exit_time):
        equity += _trade_pnl(trade, cost_config)
        peak = max(peak, equity)
        rows.append(
            {
                "datetime": trade.exit_time,
                "equity": equity,
                "drawdown": max(0.0, peak - equity),
            }
        )
    return rows


def _build_dashboard_wfo_summary(item: dict) -> dict:
    rounds = item.get("round_results", [])
    if not isinstance(rounds, list):
        rounds = []
    return {
        "rounds": [
            {
                "round_id": round_item.get("round_id", index),
                "sharpe": _as_float(round_item.get("test_pf", 0.0)),
                "return": _as_float(round_item.get("test_net_profit", 0.0)) / STARTING_EQUITY,
                "max_drawdown": _as_float(round_item.get("test_mdd", 0.0)),
                "trade_count": int(_as_float(round_item.get("test_trade_count", 0.0))),
                "passed": bool(round_item.get("pass_flag", False)),
            }
            for index, round_item in enumerate(rounds, start=1)
            if isinstance(round_item, dict)
        ],
        "avg_sharpe": _as_float(item.get("average_test_pf", 0.0)),
        "pass_rate": _as_float(item.get("pass_rate", 0.0)),
        "stability_score": _as_float(item.get("pass_rate", 0.0)),
    }


def _build_dashboard_risk_report(
    item: dict,
    trades: list[TradeRecord],
    cost_config: CostConfig | None,
) -> dict:
    equity_curve = _build_dashboard_equity_curve(trades, cost_config)
    max_drawdown = _as_float(item.get("max_test_mdd", 0.0))
    if equity_curve:
        max_drawdown = max(_as_float(row["drawdown"]) for row in equity_curve)
    return {
        "max_dd": max_drawdown,
        "ulcer_index": _compute_ulcer_index(equity_curve),
        "recovery_days": _compute_recovery_days(equity_curve),
        "volatility": 0.0,
        "downside_volatility": 0.0,
    }


def _dashboard_cost_model(
    cost_config: CostConfig | None,
    trade_stats: dict,
) -> dict:
    if cost_config is None:
        return {
            "slippage_points_per_side": 0.0,
            "fee_money_per_side": 0.0,
            "tax_rate": 0.0,
            "point_value": 0.0,
            "qty": 0,
            "total_cost": _as_float(trade_stats.get("total_cost", 0.0)),
        }
    return {
        "slippage_points_per_side": cost_config.slippage_points_per_side,
        "fee_money_per_side": cost_config.fee_money_per_side,
        "tax_rate": cost_config.tax_rate,
        "point_value": cost_config.point_value,
        "qty": cost_config.qty,
        "total_cost": _as_float(trade_stats.get("total_cost", 0.0)),
        "avg_cost_per_trade": _as_float(trade_stats.get("avg_cost_per_trade", 0.0)),
    }


def _compute_ulcer_index(equity_curve: list[dict]) -> float:
    if not equity_curve:
        return 0.0
    peak = STARTING_EQUITY
    squared_drawdowns = []
    for row in equity_curve:
        equity = _as_float(row.get("equity", STARTING_EQUITY))
        peak = max(peak, equity)
        drawdown_pct = ((peak - equity) / peak) * 100.0 if peak else 0.0
        squared_drawdowns.append(drawdown_pct * drawdown_pct)
    return math.sqrt(sum(squared_drawdowns) / len(squared_drawdowns))


def _compute_recovery_days(equity_curve: list[dict]) -> int:
    longest = 0
    current = 0
    peak = STARTING_EQUITY
    for row in equity_curve:
        equity = _as_float(row.get("equity", STARTING_EQUITY))
        if equity >= peak:
            peak = equity
            current = 0
        else:
            current += 1
            longest = max(longest, current)
    return longest


def _write_strategy_detail_reports(
    root: Path,
    run_id: str,
    ranking: list[dict],
    cost_config: CostConfig | None = None,
) -> list[str]:
    details_dir = root / "reports" / "details"
    details_dir.mkdir(parents=True, exist_ok=True)

    written_paths: list[str] = []
    for item in ranking:
        trades = parse_xs_txt(
            Path(str(item["txt_path"])).read_text(encoding="utf-8-sig")
        )
        weekly_series = build_weekly_series(trades, cost_config=cost_config)
        payload = _build_strategy_detail_payload(
            run_id,
            item,
            trades=trades,
            weekly_series=weekly_series,
            cost_config=cost_config,
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


def build_weekly_series(
    trades: list[TradeRecord],
    cost_config: CostConfig | None = None,
) -> dict:
    weekly_totals: dict[str, float] = {}
    for trade in trades:
        iso_year, iso_week, _ = trade.exit_time.date().isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"
        weekly_totals[week_key] = weekly_totals.get(week_key, 0.0) + _trade_pnl(
            trade,
            cost_config,
        )

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


def build_trade_stats(
    trades: list[TradeRecord],
    weekly_series: dict,
    cost_config: CostConfig | None = None,
) -> dict:
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
            "raw_total_profit": 0.0,
            "net_total_profit": 0.0,
            "total_slippage_cost": 0.0,
            "total_fee_cost": 0.0,
            "total_tax_cost": 0.0,
            "total_cost": 0.0,
            "avg_cost_per_trade": 0.0,
            "avg_net_pnl_per_trade": 0.0,
        }

    raw_pnls = [float(trade.pnl) for trade in trades]
    cost_rows = [_trade_cost_row(trade, cost_config) for trade in trades]
    pnls = [row["net_pnl"] for row in cost_rows]
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    avg_win = gross_profit / len(wins) if wins else 0.0
    avg_loss = gross_loss / len(losses) if losses else 0.0
    max_drawdown, underwater_weeks = _compute_weekly_risk(
        weekly_series.get("equity_curve", [])
    )
    total_cost = sum(row["total_cost"] for row in cost_rows)
    net_total_profit = sum(pnls)

    return {
        "trade_count": trade_count,
        "long_count": sum(1 for trade in trades if trade.direction == 1),
        "short_count": sum(1 for trade in trades if trade.direction == -1),
        "win_count": len(wins),
        "loss_count": len(losses),
        "win_rate": len(wins) / trade_count,
        "total_profit": net_total_profit,
        "avg_trade_pnl": net_total_profit / trade_count,
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
        "max_losing_streak": _max_losing_streak(pnls),
        "raw_total_profit": sum(raw_pnls),
        "net_total_profit": net_total_profit,
        "total_slippage_cost": sum(row["slippage_cost"] for row in cost_rows),
        "total_fee_cost": sum(row["fee_cost"] for row in cost_rows),
        "total_tax_cost": sum(row["tax_cost"] for row in cost_rows),
        "total_cost": total_cost,
        "avg_cost_per_trade": total_cost / trade_count,
        "avg_net_pnl_per_trade": net_total_profit / trade_count,
    }


def _build_strategy_detail_payload(
    run_id: str,
    item: dict,
    trades: list[TradeRecord],
    weekly_series: dict,
    cost_config: CostConfig | None = None,
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

    trade_stats = build_trade_stats(trades, weekly_series, cost_config=cost_config)
    cost_summary = build_cost_summary(trades, cost_config)

    return {
        "strategy_name": str(item["strategy_name"]),
        "run_id": run_id,
        "summary": {
            "score": score,
            "total_test_net_profit": total_profit,
            "raw_total_profit": _as_float(item.get("raw_total_profit", trade_stats["raw_total_profit"])),
            "net_total_profit": _as_float(item.get("net_total_profit", trade_stats["net_total_profit"])),
            "pass_rate": pass_rate,
            "max_test_mdd": max_mdd,
            "average_test_pf": average_pf,
        },
        "period": build_trade_period(trades),
        "trade_stats": trade_stats,
        "cost": cost_summary,
        "cost_stress": run_cost_stress(
            trades,
            cost_config or CostConfig(slippage_points_per_side=0.0, tax_rate=0.0),
        )["scenarios"],
        "trades": build_trade_cost_records(trades, cost_config),
        "equity_curve": weekly_series["equity_curve"],
        "weekly_pnl": weekly_series["weekly_pnl"],
        "period_pnl": period_pnl,
        "kpi": {
            "score": score,
            "profit": trade_stats["net_total_profit"],
            "pass_rate": pass_rate,
            "mdd": max_mdd,
            "pf": average_pf,
        },
    }


def _ratio_or_inf(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return math.inf if numerator > 0 else 0.0
    return numerator / denominator


def build_cost_summary(
    trades: list[TradeRecord],
    cost_config: CostConfig | None = None,
) -> dict[str, float | int]:
    if cost_config is None:
        trade_count = len(trades)
        return {
            "slippage_points_per_side": 0.0,
            "round_trip_slippage_points": 0.0,
            "fee_money_per_side": 0.0,
            "round_trip_fee_money": 0.0,
            "fee_points_round_trip": 0.0,
            "tax_rate": 0.0,
            "point_value": 0.0,
            "qty": 0,
            "total_slippage_cost_points": 0.0,
            "total_fee_cost_points": 0.0,
            "total_tax_cost_points": 0.0,
            "total_cost_points": 0.0,
            "avg_cost_per_trade_points": 0.0 if trade_count else 0.0,
        }

    rows = [_trade_cost_row(trade, cost_config) for trade in trades]
    total_slippage = sum(row["slippage_cost"] for row in rows)
    total_fee = sum(row["fee_cost"] for row in rows)
    total_tax = sum(row["tax_cost"] for row in rows)
    total_cost = sum(row["total_cost"] for row in rows)
    trade_count = len(trades)
    return {
        "slippage_points_per_side": float(cost_config.slippage_points_per_side),
        "round_trip_slippage_points": float(cost_config.slippage_points_per_side) * 2.0,
        "fee_money_per_side": float(cost_config.fee_money_per_side),
        "round_trip_fee_money": float(cost_config.fee_money_per_side) * 2.0,
        "fee_points_round_trip": (
            float(cost_config.fee_money_per_side) * 2.0 / float(cost_config.point_value)
        ),
        "tax_rate": float(cost_config.tax_rate),
        "point_value": float(cost_config.point_value),
        "qty": int(cost_config.qty),
        "total_slippage_cost_points": total_slippage,
        "total_fee_cost_points": total_fee,
        "total_tax_cost_points": total_tax,
        "total_cost_points": total_cost,
        "avg_cost_per_trade_points": total_cost / trade_count if trade_count else 0.0,
    }


def build_trade_cost_records(
    trades: list[TradeRecord],
    cost_config: CostConfig | None = None,
) -> list[dict]:
    records = []
    for index, trade in enumerate(trades, start=1):
        row = _trade_cost_row(trade, cost_config)
        records.append(
            {
                "index": index,
                "entry_time": trade.entry_time.isoformat(),
                "exit_time": trade.exit_time.isoformat(),
                "direction": trade.direction,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "raw_pnl": row["raw_pnl"],
                "net_pnl": row["net_pnl"],
                "slippage_cost": row["slippage_cost"],
                "fee_cost": row["fee_cost"],
                "tax_cost": row["tax_cost"],
                "total_cost": row["total_cost"],
            }
        )
    return records


def _trade_pnl(trade: TradeRecord, cost_config: CostConfig | None) -> float:
    if cost_config is None:
        return float(trade.pnl)
    return net_pnl_points_for_trade(trade, cost_config)


def _trade_cost_row(
    trade: TradeRecord,
    cost_config: CostConfig | None,
) -> dict[str, float]:
    if cost_config is None:
        raw_pnl = float(trade.pnl)
        return {
            "raw_pnl": raw_pnl,
            "net_pnl": raw_pnl,
            "slippage_cost": 0.0,
            "fee_cost": 0.0,
            "tax_cost": 0.0,
            "total_cost": 0.0,
        }
    return trade_cost_breakdown(trade, cost_config)


def _max_losing_streak(pnl_values: list[float]) -> int:
    current = 0
    max_streak = 0
    for pnl in pnl_values:
        if pnl < 0:
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
