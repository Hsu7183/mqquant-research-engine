from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "v2" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mqre_v2.export import export_latest_run  # noqa: E402


def build_mock_pipeline_result() -> dict:
    start = datetime(2024, 1, 2, 8, 45, 0)
    equity = 100000.0
    equity_curve = []
    trades = []
    cumulative = 0.0

    for index in range(40):
        pnl = 95.0 + index * 2.5
        if index in {9, 17, 29}:
            pnl -= 260.0
        cumulative += pnl
        trades.append(
            {
                "datetime": start + timedelta(days=index),
                "price": 20400 + index * 6,
                "side": "buy" if index % 2 == 0 else "sell",
                "pnl": pnl,
                "cumulative_pnl": cumulative,
            }
        )

    peak = equity
    for index, trade in enumerate(trades):
        equity += float(trade["pnl"])
        peak = max(peak, equity)
        equity_curve.append(
            {
                "datetime": trade["datetime"],
                "equity": equity,
                "drawdown": max(0.0, peak - equity),
            }
        )

    return {
        "ranking": [
            {
                "strategy_id": "1001plus_mock_pipeline",
                "score": 132.5,
                "annual_return": 0.214,
                "sharpe": 1.68,
                "max_drawdown": 8800.0,
                "trade_count": 388,
                "win_rate": 0.57,
                "profit_factor": 1.72,
                "robustness_score": 0.81,
                "wfo_pass_rate": 0.74,
                "oos_sharpe": 1.31,
            },
            {
                "strategy_id": "1001plus_mock_challenger",
                "score": 118.0,
                "annual_return": 0.18,
                "sharpe": 1.42,
                "max_drawdown": 11200.0,
                "trade_count": 344,
                "win_rate": 0.54,
                "profit_factor": 1.51,
                "robustness_score": 0.72,
                "wfo_pass_rate": 0.67,
                "oos_sharpe": 1.14,
            },
        ],
        "strategy_detail": {
            "strategy_id": "1001plus_mock_pipeline",
            "params": {
                "baseline": "1001plus",
                "don_len": 72,
                "ema_fast": 5,
                "ema_slow": 34,
                "atr_len": 14,
            },
            "performance": {
                "return": 0.214,
                "annual_return": 0.214,
                "sharpe": 1.68,
                "mdd": 8800.0,
                "win_rate": 0.57,
                "profit_factor": 1.72,
                "trade_count": 388,
                "average_trade_pnl": 41.8,
            },
            "cost_model": {
                "slippage_points_per_side": 2.0,
                "fee_money_per_side": 0.0,
                "tax_rate": 0.00002,
                "point_value": 50.0,
                "qty": 1,
            },
            "entry_logic_summary": "Mock v2 result: 1001plus trend breakout confirmation.",
            "exit_logic_summary": "Mock v2 result: ATR target, ATR stop, and force exit.",
            "tags": ["1001plus", "trend", "breakout"],
        },
        "equity_curve": equity_curve,
        "trades": trades,
        "oos_summary": {
            "oos_periods": [
                {"start": "2024-01-01", "end": "2024-03-31", "return": 0.042, "sharpe": 1.2, "max_drawdown": 7400}
            ],
            "oos_sharpe": 1.2,
            "oos_return": 0.042,
            "oos_mdd": 7400.0,
        },
        "wfo_summary": {
            "rounds": [
                {"round_id": 1, "sharpe": 1.1, "return": 0.02, "max_drawdown": 7300, "passed": True},
                {"round_id": 2, "sharpe": 1.26, "return": 0.031, "max_drawdown": 8100, "passed": True},
            ],
            "avg_sharpe": 1.18,
            "pass_rate": 1.0,
            "stability_score": 0.78,
        },
        "risk_report": {
            "max_dd": 8800.0,
            "ulcer_index": 3.42,
            "recovery_days": 12,
            "volatility": 0.19,
            "downside_volatility": 0.11,
        },
        "decision_audit": {
            "baseline_strategy": "1001plus_baseline",
            "challenger_strategy": "1001plus_mock_pipeline",
            "promotion_decision": "review_required",
            "reason": "mock v2 output exported successfully for dashboard review",
            "timestamp": datetime(2026, 5, 7, 9, 0, 0),
        },
    }


def main() -> None:
    files = export_latest_run(build_mock_pipeline_result(), output_dir=str(ROOT / "runs" / "latest"))
    print(json.dumps({"output_dir": "runs/latest", "files": [str(Path(path).relative_to(ROOT)) for path in files]}, indent=2))


if __name__ == "__main__":
    main()
