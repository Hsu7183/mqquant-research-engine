from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


TradeSide = Literal["long", "short"]


@dataclass(slots=True)
class TradeRecord:
    """Single completed intraday trade record for OOS evaluation only."""

    entry_time: datetime
    exit_time: datetime
    side: TradeSide
    entry_price: float
    exit_price: float
    qty: int
    slippage_points: float
    fee_points: float
    pnl_points: float
    pnl_after_cost_points: float


__all__ = ["TradeRecord", "TradeSide"]
