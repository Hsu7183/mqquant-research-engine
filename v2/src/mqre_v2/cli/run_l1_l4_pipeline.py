from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any, Sequence

from mqre_v2.automation.auto_research import AutoResearchConfig, run_auto_research
from mqre_v2.cli.backtest_m1_to_latest import backtest_m1_to_latest
from mqre_v2.cli.run_latest_pipeline import run_latest_pipeline
from mqre_v2.decision.promotion_pipeline import (
    AutoPromotionConfig,
    run_auto_promotion_pipeline,
)


def run_l1_l4_pipeline(
    m1_path: str,
    strategy_name: str,
    start_date: date,
    end_date: date,
    output_ranking_json: str = "runs/latest/reports/ranking.json",
    forward_log_path: str = "reports/forward_test_log.csv",
    recommendation_output_path: str = "reports/auto_promotion_recommendation.json",
    audit_log_path: str = "reports/decision_audit_log.csv",
    min_score: float = 100.0,
    min_pass_rate: float = 0.6,
    max_mdd: float = 15000.0,
    strategy: str = "simple_m1",
) -> dict[str, Any]:
    backtest_summary = backtest_m1_to_latest(
        m1_path=m1_path,
        strategy_name=strategy_name,
        strategy=strategy,
    )
    ranking_path = Path(output_ranking_json)

    latest_summary = run_latest_pipeline(
        base_dir="runs",
        start_date=start_date,
        end_date=end_date,
        output_filename=ranking_path.name,
    )

    auto_research_summary = run_auto_research(
        AutoResearchConfig(
            txt_folder=str(Path("runs") / "latest" / "txt"),
            start_date=start_date,
            end_date=end_date,
            output_json_path=output_ranking_json,
            forward_log_path=forward_log_path,
            top_n=10,
            auto_add_top1_to_forward=True,
            min_score_to_forward=0.0,
        )
    )

    detail_reports_count = _count_detail_reports(Path("runs") / "latest" / "reports")
    if latest_summary.get("detail_json_count") is not None:
        detail_reports_count = int(latest_summary["detail_json_count"])

    promotion_summary = run_auto_promotion_pipeline(
        AutoPromotionConfig(
            ranking_report_path=output_ranking_json,
            recommendation_output_path=recommendation_output_path,
            audit_log_path=audit_log_path,
            min_score=min_score,
            min_pass_rate=min_pass_rate,
            max_mdd=max_mdd,
        )
    )

    return {
        "strategy_name": strategy_name,
        "strategy": strategy,
        "m1_path": m1_path,
        "bars_count": backtest_summary["bars_count"],
        "trades_generated": backtest_summary["trades_count"],
        "trade_txt": backtest_summary["output_trade_txt"],
        "ranking_json": output_ranking_json,
        "detail_reports_count": detail_reports_count,
        "forward_log_path": forward_log_path,
        "forward_added": auto_research_summary["added_to_forward"],
        "forward_notes": auto_research_summary["notes"],
        "recommendation_output_path": recommendation_output_path,
        "audit_log_path": audit_log_path,
        "recommend_promote": promotion_summary["recommend_promote"],
        "reason": promotion_summary["reason"],
        "risk_warnings": promotion_summary["risk_warnings"],
        "requires_human_review": promotion_summary["requires_human_review"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    summary = run_l1_l4_pipeline(
        m1_path=args.m1_path,
        strategy_name=args.strategy_name,
        start_date=args.start_date,
        end_date=args.end_date,
        output_ranking_json=args.output_ranking_json,
        forward_log_path=args.forward_log_path,
        recommendation_output_path=args.recommendation_output_path,
        audit_log_path=args.audit_log_path,
        min_score=args.min_score,
        min_pass_rate=args.min_pass_rate,
        max_mdd=args.max_mdd,
        strategy=args.strategy,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run mqquant L1-L4 pipeline from M1 data.")
    parser.add_argument("--m1-path", required=True)
    parser.add_argument("--strategy-name", required=True)
    parser.add_argument(
        "--strategy",
        choices=["simple_m1", "1001plus"],
        default="simple_m1",
    )
    parser.add_argument("--start-date", required=True, type=_parse_date)
    parser.add_argument("--end-date", required=True, type=_parse_date)
    parser.add_argument(
        "--output-ranking-json",
        default="runs/latest/reports/ranking.json",
    )
    parser.add_argument("--forward-log-path", default="reports/forward_test_log.csv")
    parser.add_argument(
        "--recommendation-output-path",
        default="reports/auto_promotion_recommendation.json",
    )
    parser.add_argument("--audit-log-path", default="reports/decision_audit_log.csv")
    parser.add_argument("--min-score", default=100.0, type=float)
    parser.add_argument("--min-pass-rate", default=0.6, type=float)
    parser.add_argument("--max-mdd", default=15000.0, type=float)
    return parser


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid date: {value}") from exc


def _count_detail_reports(reports_dir: Path) -> int:
    details_dir = reports_dir / "details"
    if not details_dir.is_dir():
        return 0
    return len([path for path in details_dir.glob("*.json") if path.is_file()])


if __name__ == "__main__":
    raise SystemExit(main())
