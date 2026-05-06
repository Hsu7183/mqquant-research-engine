from __future__ import annotations

import pytest

from mqre_v2.backtest.costs import (
    CostConfig,
    calculate_net_pnl_points,
    calculate_trade_cost_points,
)


def test_calculate_trade_cost_points() -> None:
    cost = CostConfig(
        slippage_points_per_side=2.0,
        fee_money_per_side=50.0,
        tax_rate=0.00002,
        point_value=50.0,
        qty=1,
    )

    result = calculate_trade_cost_points(
        entry_price=40000.0,
        exit_price=40010.0,
        cost=cost,
    )

    assert result["slippage_cost_points"] == 4.0
    assert result["fee_cost_points"] == 2.0
    assert result["tax_cost_points"] == pytest.approx(1.6002)
    assert result["total_cost_points"] == pytest.approx(7.6002)


def test_calculate_net_pnl_points() -> None:
    cost = CostConfig(
        slippage_points_per_side=2.0,
        fee_money_per_side=50.0,
        tax_rate=0.00002,
        point_value=50.0,
        qty=1,
    )

    result = calculate_net_pnl_points(
        raw_pnl_points=10.0,
        entry_price=40000.0,
        exit_price=40010.0,
        cost=cost,
    )

    assert result == pytest.approx(2.3998)
