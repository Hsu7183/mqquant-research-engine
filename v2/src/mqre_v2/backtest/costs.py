from __future__ import annotations

from dataclasses import dataclass

from mqre_v2.core.trades import TradeRecord


@dataclass(frozen=True, slots=True)
class CostConfig:
    slippage_points_per_side: float = 2.0
    fee_money_per_side: float = 0.0
    tax_rate: float = 0.00002
    point_value: float = 50.0
    qty: int = 1


def calculate_trade_cost_points(
    entry_price: float,
    exit_price: float,
    cost: CostConfig,
) -> dict[str, float]:
    _validate_cost_config(cost)

    slippage_cost_points = float(cost.slippage_points_per_side) * 2.0
    fee_cost_points = (float(cost.fee_money_per_side) * 2.0) / float(cost.point_value)
    tax_cost_money = (
        (float(entry_price) + float(exit_price))
        * float(cost.point_value)
        * float(cost.tax_rate)
        * int(cost.qty)
    )
    tax_cost_points = tax_cost_money / float(cost.point_value) / int(cost.qty)
    total_cost_points = (
        slippage_cost_points + fee_cost_points + tax_cost_points
    )

    return {
        "slippage_cost_points": float(slippage_cost_points),
        "fee_cost_points": float(fee_cost_points),
        "tax_cost_points": float(tax_cost_points),
        "total_cost_points": float(total_cost_points),
    }


def calculate_net_pnl_points(
    raw_pnl_points: float,
    entry_price: float,
    exit_price: float,
    cost: CostConfig,
) -> float:
    costs = calculate_trade_cost_points(entry_price, exit_price, cost)
    return float(raw_pnl_points) - costs["total_cost_points"]


def trade_cost_breakdown(
    trade: TradeRecord,
    cost: CostConfig,
) -> dict[str, float]:
    costs = calculate_trade_cost_points(trade.entry_price, trade.exit_price, cost)
    raw_pnl = float(trade.pnl)
    net_pnl = raw_pnl - costs["total_cost_points"]
    return {
        "raw_pnl": raw_pnl,
        "net_pnl": float(net_pnl),
        "slippage_cost": costs["slippage_cost_points"],
        "fee_cost": costs["fee_cost_points"],
        "tax_cost": costs["tax_cost_points"],
        "total_cost": costs["total_cost_points"],
    }


def net_pnl_points_for_trade(trade: TradeRecord, cost: CostConfig) -> float:
    return trade_cost_breakdown(trade, cost)["net_pnl"]


def _validate_cost_config(cost: CostConfig) -> None:
    if cost.point_value <= 0:
        raise ValueError("point_value must be > 0")
    if cost.qty <= 0:
        raise ValueError("qty must be > 0")
    if cost.slippage_points_per_side < 0:
        raise ValueError("slippage_points_per_side cannot be negative")
    if cost.fee_money_per_side < 0:
        raise ValueError("fee_money_per_side cannot be negative")
    if cost.tax_rate < 0:
        raise ValueError("tax_rate cannot be negative")


__all__ = [
    "CostConfig",
    "calculate_net_pnl_points",
    "calculate_trade_cost_points",
    "net_pnl_points_for_trade",
    "trade_cost_breakdown",
]
