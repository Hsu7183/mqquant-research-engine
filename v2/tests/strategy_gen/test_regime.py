from __future__ import annotations

from datetime import datetime, timedelta

from mqre_v2.core.bars import BarRecord
from mqre_v2.strategy_gen.regime import RegimeType, detect_intraday_regime


def test_detect_intraday_regime_trend_up() -> None:
    bars = _bars(start=100, step=2, count=60)

    regime = detect_intraday_regime(bars)

    assert regime["trend_direction"] == "up"
    assert regime["regime_type"] == RegimeType.TREND_UP


def test_detect_intraday_regime_trend_down() -> None:
    bars = _bars(start=200, step=-2, count=60)

    regime = detect_intraday_regime(bars)

    assert regime["trend_direction"] == "down"
    assert regime["regime_type"] == RegimeType.TREND_DOWN


def test_detect_intraday_regime_range() -> None:
    bars = []
    ts = datetime(2026, 1, 2, 8, 45)
    for index in range(60):
        base = 100 + (20 if index % 2 == 0 else -20)
        bars.append(
            BarRecord(
                ts=ts + timedelta(minutes=index),
                open=base,
                high=base + 20,
                low=base - 20,
                close=100,
                volume=100,
            )
        )

    regime = detect_intraday_regime(bars)

    assert regime["trend_direction"] == "flat"
    assert regime["regime_type"] == RegimeType.RANGE


def _bars(start: float, step: float, count: int) -> list[BarRecord]:
    ts = datetime(2026, 1, 2, 8, 45)
    bars = []
    for index in range(count):
        open_price = start + step * index
        close_price = open_price + step
        bars.append(
            BarRecord(
                ts=ts + timedelta(minutes=index),
                open=open_price,
                high=max(open_price, close_price) + 1,
                low=min(open_price, close_price) - 1,
                close=close_price,
                volume=100,
            )
        )
    return bars
