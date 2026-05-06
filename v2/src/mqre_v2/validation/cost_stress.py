from __future__ import annotations

from dataclasses import replace
from math import inf

from mqre_v2.backtest.costs import CostConfig, net_pnl_points_for_trade
from mqre_v2.core.trades import TradeRecord


def run_cost_stress(
    trades: list[TradeRecord],
    base_cost: CostConfig,
    slippage_scenarios: list[float] | None = None,
) -> dict:
    scenarios = slippage_scenarios or [2, 3, 4, 5]
    return {
        "scenarios": [
            _evaluate_scenario(trades, replace(base_cost, slippage_points_per_side=float(slippage)))
            for slippage in scenarios
        ]
    }


def _evaluate_scenario(trades: list[TradeRecord], cost: CostConfig) -> dict:
    pnl_values = [net_pnl_points_for_trade(trade, cost) for trade in trades]
    total_net_pnl = float(sum(pnl_values))
    profit_factor = _profit_factor(pnl_values)
    max_drawdown = _max_drawdown(pnl_values)
    return {
        "slippage_points": float(cost.slippage_points_per_side),
        "total_net_pnl": total_net_pnl,
        "profit_factor": float(profit_factor),
        "max_drawdown": max_drawdown,
        "trade_count": len(trades),
        "passed": total_net_pnl > 0 and profit_factor >= 1.1,
    }


def _profit_factor(pnl_values: list[float]) -> float:
    gross_profit = sum(value for value in pnl_values if value > 0)
    gross_loss = abs(sum(value for value in pnl_values if value < 0))
    if gross_loss == 0:
        return inf if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def _max_drawdown(pnl_values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for pnl in pnl_values:
        equity += pnl
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
    return float(max_drawdown)


__all__ = ["run_cost_stress"]
