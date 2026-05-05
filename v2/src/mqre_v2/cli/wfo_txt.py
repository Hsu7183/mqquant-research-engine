from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict
from datetime import date
from typing import Any, Sequence

from mqre_v2.validation.wfo import (
    TxtWfoInput,
    WfoGateConfig,
    build_txt_evaluate_fn,
    default_optimize_fn,
    run_wfo,
)


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    txt_input = TxtWfoInput(
        strategy_name=args.strategy_name,
        txt_path=args.txt_path,
    )
    gate_config = WfoGateConfig(
        min_test_trade_count=args.min_test_trade_count,
        max_test_mdd=args.max_test_mdd,
        min_test_pf=args.min_test_pf,
        min_pass_rate=args.min_pass_rate,
    )
    result = run_wfo(
        start_date=args.start_date,
        end_date=args.end_date,
        strategy_name=args.strategy_name,
        optimize_fn=default_optimize_fn,
        evaluate_fn=build_txt_evaluate_fn(txt_input),
        window_kwargs={
            "train_months": args.train_months,
            "gap_months": args.gap_months,
            "test_months": args.test_months,
            "step_months": args.step_months,
        },
        gate_config=gate_config,
    )

    print(json.dumps(_build_summary_payload(args.strategy_name, result), allow_nan=False))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run WFO validation from an XS TXT trade file.")
    parser.add_argument("--txt-path", required=True)
    parser.add_argument("--strategy-name", required=True)
    parser.add_argument("--start-date", required=True, type=_parse_date)
    parser.add_argument("--end-date", required=True, type=_parse_date)
    parser.add_argument("--train-months", default=36, type=int)
    parser.add_argument("--gap-months", default=1, type=int)
    parser.add_argument("--test-months", default=6, type=int)
    parser.add_argument("--step-months", default=6, type=int)
    parser.add_argument("--min-test-trade-count", default=20, type=int)
    parser.add_argument("--max-test-mdd", default=15000.0, type=float)
    parser.add_argument("--min-test-pf", default=1.05, type=float)
    parser.add_argument("--min-pass-rate", default=0.6, type=float)
    return parser


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid date: {value}") from exc


def _build_summary_payload(strategy_name: str, result: Any) -> dict[str, Any]:
    summary = result.summary
    return _json_safe(
        {
            "strategy_name": strategy_name,
            "windows": [asdict(window) for window in result.windows],
            "total_rounds": summary.total_rounds,
            "passed_rounds": summary.passed_rounds,
            "failed_rounds": summary.failed_rounds,
            "pass_rate": summary.pass_rate,
            "total_test_net_profit": summary.total_test_net_profit,
            "average_test_net_profit": summary.average_test_net_profit,
            "max_test_mdd": summary.max_test_mdd,
            "average_test_pf": summary.average_test_pf,
            "total_test_trade_count": summary.total_test_trade_count,
            "passed": result.passed,
            "fail_reason": result.fail_reason,
        }
    )


def _json_safe(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            return None
        return "Infinity" if value > 0 else "-Infinity"
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
