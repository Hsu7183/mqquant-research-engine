from __future__ import annotations

from mqre_v2.core.bars import BarRecord


class RegimeType:
    TREND_UP = "TREND_UP"
    TREND_DOWN = "TREND_DOWN"
    RANGE = "RANGE"
    VOLATILE_BREAKOUT = "VOLATILE_BREAKOUT"
    OPEN_DRIVE = "OPEN_DRIVE"
    AFTERNOON_TREND = "AFTERNOON_TREND"


def detect_intraday_regime(bars_for_day: list[BarRecord]) -> dict:
    if not bars_for_day:
        raise ValueError("bars_for_day cannot be empty")

    bars = sorted(bars_for_day, key=lambda bar: bar.ts)
    open_price = float(bars[0].open)
    close_price = float(bars[-1].close)
    day_high = max(float(bar.high) for bar in bars)
    day_low = min(float(bar.low) for bar in bars)
    day_range = day_high - day_low
    open_to_close = close_price - open_price
    abs_move = abs(open_to_close)
    trend_direction = _trend_direction(open_to_close, day_range)
    volatility_level = _volatility_level(day_range)
    volume_level = _volume_level(bars)

    first_30 = bars[: min(30, len(bars))]
    first_30_range = max(float(bar.high) for bar in first_30) - min(
        float(bar.low) for bar in first_30
    )
    afternoon_bars = [bar for bar in bars if bar.ts.time().strftime("%H%M") >= "1200"]
    afternoon_move = (
        float(afternoon_bars[-1].close) - float(afternoon_bars[0].open)
        if len(afternoon_bars) >= 2
        else 0.0
    )

    if (
        trend_direction != "flat"
        and len(first_30) >= 10
        and first_30_range >= max(day_range * 0.55, 40.0)
    ):
        regime_type = RegimeType.OPEN_DRIVE
    elif volume_level == "high" and first_30_range >= max(day_range * 0.4, 30.0):
        regime_type = RegimeType.VOLATILE_BREAKOUT
    elif len(afternoon_bars) >= 20 and abs(afternoon_move) >= max(day_range * 0.35, 30.0):
        regime_type = RegimeType.AFTERNOON_TREND
    elif _is_trend_up(bars, open_to_close, day_range):
        regime_type = RegimeType.TREND_UP
    elif _is_trend_down(bars, open_to_close, day_range):
        regime_type = RegimeType.TREND_DOWN
    elif day_range >= 20.0 and abs_move <= max(day_range * 0.25, 20.0):
        regime_type = RegimeType.RANGE
    else:
        regime_type = RegimeType.RANGE

    return {
        "date": bars[0].ts.date().isoformat(),
        "day_range": day_range,
        "open_to_close": open_to_close,
        "trend_direction": trend_direction,
        "volatility_level": volatility_level,
        "volume_level": volume_level,
        "regime_type": regime_type,
    }


def _trend_direction(open_to_close: float, day_range: float) -> str:
    threshold = max(day_range * 0.25, 20.0)
    if open_to_close > threshold:
        return "up"
    if open_to_close < -threshold:
        return "down"
    return "flat"


def _volatility_level(day_range: float) -> str:
    if day_range >= 180:
        return "high"
    if day_range >= 80:
        return "medium"
    return "low"


def _volume_level(bars: list[BarRecord]) -> str:
    volumes = [float(bar.volume) for bar in bars if bar.volume is not None]
    if not volumes:
        return "unknown"
    first_30 = volumes[: min(30, len(volumes))]
    first_avg = sum(first_30) / len(first_30)
    all_avg = sum(volumes) / len(volumes)
    return "high" if all_avg and first_avg >= all_avg * 1.5 else "normal"


def _is_trend_up(bars: list[BarRecord], open_to_close: float, day_range: float) -> bool:
    if open_to_close < max(day_range * 0.35, 30.0):
        return False
    first, second = _split_halves(bars)
    return _avg_low(second) >= _avg_low(first) and _avg_high(second) >= _avg_high(first)


def _is_trend_down(bars: list[BarRecord], open_to_close: float, day_range: float) -> bool:
    if open_to_close > -max(day_range * 0.35, 30.0):
        return False
    first, second = _split_halves(bars)
    return _avg_high(second) <= _avg_high(first) and _avg_low(second) <= _avg_low(first)


def _split_halves(bars: list[BarRecord]) -> tuple[list[BarRecord], list[BarRecord]]:
    midpoint = max(1, len(bars) // 2)
    return bars[:midpoint], bars[midpoint:] or bars[midpoint - 1 :]


def _avg_high(bars: list[BarRecord]) -> float:
    return sum(float(bar.high) for bar in bars) / len(bars)


def _avg_low(bars: list[BarRecord]) -> float:
    return sum(float(bar.low) for bar in bars) / len(bars)


__all__ = ["RegimeType", "detect_intraday_regime"]
