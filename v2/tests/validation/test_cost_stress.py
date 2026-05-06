from __future__ import annotations

from datetime import datetime

from mqre_v2.backtest.costs import CostConfig
from mqre_v2.core.trades import TradeRecord
from mqre_v2.validation.cost_stress import run_cost_stress


def test_run_cost_stress_returns_slippage_scenarios() -> None:
    trades = [
        _trade(100, 130),
        _trade(100, 120),
        _trade(100, 90),
    ]

    result = run_cost_stress(
        trades,
        CostConfig(slippage_points_per_side=2.0, tax_rate=0.0),
        slippage_scenarios=[2, 5],
    )

    assert len(result["scenarios"]) == 2
    assert result["scenarios"][0]["slippage_points"] == 2.0
    assert result["scenarios"][0]["total_net_pnl"] == 28.0
    assert result["scenarios"][0]["trade_count"] == 3
    assert result["scenarios"][0]["passed"] is True
    assert result["scenarios"][1]["total_net_pnl"] == 10.0


def _trade(entry_price: float, exit_price: float) -> TradeRecord:
    return TradeRecord(
        entry_time=datetime(2026, 1, 2, 9, 0),
        exit_time=datetime(2026, 1, 2, 9, 5),
        entry_price=entry_price,
        exit_price=exit_price,
        direction=1,
        pnl=exit_price - entry_price,
    )
