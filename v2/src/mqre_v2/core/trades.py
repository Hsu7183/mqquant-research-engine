from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class TradeRecord:
    """Strategy-layer trade record without execution costs."""

    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    direction: int
    pnl: float


@dataclass(slots=True)
class ExtendedTradeRecord:
    """Trade record with execution-cost fields layered on top."""

    base: TradeRecord
    qty: int
    slippage_points: float
    fee_points: float
    pnl_after_cost: float


__all__ = ["ExtendedTradeRecord", "TradeRecord"]
