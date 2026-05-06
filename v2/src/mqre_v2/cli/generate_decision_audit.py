from __future__ import annotations

import argparse
import json
from pathlib import Path

from mqre_v2.decision.artifact_decision import (
    ArtifactDecisionConfig,
    export_decision_audit_from_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate dashboard decision_audit.json from run artifacts.",
    )
    parser.add_argument("--artifact-dir", default="runs/latest")
    parser.add_argument("--ranking-path")
    parser.add_argument("--oos-summary-path")
    parser.add_argument("--wfo-summary-path")
    parser.add_argument("--risk-report-path")
    parser.add_argument("--forward-report-path")
    parser.add_argument("--output-path")
    parser.add_argument("--baseline-strategy", default="1001plus_baseline")
    parser.add_argument("--min-score", type=float, default=100.0)
    parser.add_argument("--min-profit-factor", type=float, default=1.1)
    parser.add_argument("--min-trade-count", type=int, default=30)
    parser.add_argument("--min-oos-sharpe", type=float, default=1.0)
    parser.add_argument("--min-oos-return", type=float, default=0.0)
    parser.add_argument("--max-oos-mdd", type=float, default=15000.0)
    parser.add_argument("--min-wfo-pass-rate", type=float, default=0.6)
    parser.add_argument("--min-wfo-avg-sharpe", type=float, default=1.0)
    parser.add_argument("--min-wfo-stability-score", type=float, default=0.6)
    parser.add_argument("--max-risk-drawdown", type=float, default=15000.0)
    parser.add_argument("--max-ulcer-index", type=float, default=10.0)
    parser.add_argument("--max-recovery-days", type=int, default=60)
    parser.add_argument("--min-forward-score", type=float, default=60.0)
    args = parser.parse_args(argv)

    artifact_dir = Path(args.artifact_dir)
    ranking_path = args.ranking_path or str(artifact_dir / "ranking.json")
    oos_summary_path = args.oos_summary_path or str(artifact_dir / "oos_summary.json")
    wfo_summary_path = args.wfo_summary_path or str(artifact_dir / "wfo_summary.json")
    risk_report_path = args.risk_report_path or str(artifact_dir / "risk_report.json")
    default_forward_path = artifact_dir / "forward_report.json"
    forward_report_path = (
        args.forward_report_path
        if args.forward_report_path is not None
        else str(default_forward_path)
        if default_forward_path.exists()
        else None
    )
    output_path = args.output_path or str(artifact_dir / "decision_audit.json")

    payload = export_decision_audit_from_artifacts(
        ranking_path=ranking_path,
        oos_summary_path=oos_summary_path,
        wfo_summary_path=wfo_summary_path,
        risk_report_path=risk_report_path,
        forward_report_path=forward_report_path,
        output_path=output_path,
        config=ArtifactDecisionConfig(
            baseline_strategy=args.baseline_strategy,
            min_score=args.min_score,
            min_profit_factor=args.min_profit_factor,
            min_trade_count=args.min_trade_count,
            min_oos_sharpe=args.min_oos_sharpe,
            min_oos_return=args.min_oos_return,
            max_oos_mdd=args.max_oos_mdd,
            min_wfo_pass_rate=args.min_wfo_pass_rate,
            min_wfo_avg_sharpe=args.min_wfo_avg_sharpe,
            min_wfo_stability_score=args.min_wfo_stability_score,
            max_risk_drawdown=args.max_risk_drawdown,
            max_ulcer_index=args.max_ulcer_index,
            max_recovery_days=args.max_recovery_days,
            min_forward_score=args.min_forward_score,
        ),
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
