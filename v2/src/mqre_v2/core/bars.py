from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class BarRecord:
    """Market-data OHLC bar record."""

    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | int | None = None


__all__ = ["BarRecord"]
