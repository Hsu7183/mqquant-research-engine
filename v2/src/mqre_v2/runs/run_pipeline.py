from __future__ import annotations

import math
import json
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path

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


def _write_strategy_detail_reports(root: Path, run_id: str, ranking: list[dict]) -> None:
    details_dir = root / "reports" / "details"
    details_dir.mkdir(parents=True, exist_ok=True)

    for item in ranking:
        trades = parse_xs_txt(
            Path(str(item["txt_path"])).read_text(encoding="utf-8-sig")
        )
        payload = _build_strategy_detail_payload(
            run_id,
            item,
            weekly_series=build_weekly_series(trades),
        )
        detail_path = details_dir / f"{payload['strategy_name']}.json"
        detail_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False),
            encoding="utf-8",
        )


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


def _build_strategy_detail_payload(
    run_id: str,
    item: dict,
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


def _as_float(value: object) -> float:
    if isinstance(value, str) and value in {"Infinity", "-Infinity", "NaN"}:
        return 5.0 if value == "Infinity" else 0.0

    number = float(value)
    if not math.isfinite(number):
        return 5.0 if number > 0 else 0.0
    return number
