from __future__ import annotations

import argparse
import json
from typing import Sequence

from mqre_v2.decision.promotion_pipeline import (
    AutoPromotionConfig,
    run_auto_promotion_pipeline,
)


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    summary = run_auto_promotion_pipeline(
        AutoPromotionConfig(
            ranking_report_path=args.ranking_report_path,
            recommendation_output_path=args.recommendation_output_path,
            audit_log_path=args.audit_log_path,
            min_score=args.min_score,
            min_pass_rate=args.min_pass_rate,
            max_mdd=args.max_mdd,
        )
    )
    print(json.dumps(summary, ensure_ascii=False, allow_nan=False))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run mqquant auto promotion recommendation pipeline.",
    )
    parser.add_argument("--ranking-report-path", required=True)
    parser.add_argument("--recommendation-output-path", required=True)
    parser.add_argument("--audit-log-path", required=True)
    parser.add_argument("--min-score", default=100.0, type=float)
    parser.add_argument("--min-pass-rate", default=0.6, type=float)
    parser.add_argument("--max-mdd", default=15000.0, type=float)
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
