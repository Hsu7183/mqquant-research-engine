from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, time
from math import sqrt
from typing import Any

from mqre_v2.core.bars import BarRecord
from mqre_v2.core.trades import TradeRecord
from mqre_v2.strategy_gen.generator import GeneratedStrategyConfig


@dataclass(frozen=True, slots=True)
class _OpenPosition:
    entry_time: datetime
    entry_price: float
    direction: int
    entry_index: int
    entry_date: object


@dataclass(slots=True)
class _RollingWindow:
    maxlen: int
    values: deque[tuple[int, float]]
    total: float = 0.0
    total_sq: float = 0.0
    cursor: int = 0
    max_values: deque[tuple[int, float]] = field(default_factory=deque)
    min_values: deque[tuple[int, float]] = field(default_factory=deque)

    def add(self, value: float) -> None:
        self.cursor += 1
        item = (self.cursor, value)
        if len(self.values) == self.maxlen:
            old_id, old = self.values.popleft()
            self.total -= old
            self.total_sq -= old * old
            if self.max_values and self.max_values[0][0] == old_id:
                self.max_values.popleft()
            if self.min_values and self.min_values[0][0] == old_id:
                self.min_values.popleft()

        self.values.append(item)
        self.total += value
        self.total_sq += value * value
        while self.max_values and self.max_values[-1][1] <= value:
            self.max_values.pop()
        self.max_values.append(item)
        while self.min_values and self.min_values[-1][1] >= value:
            self.min_values.pop()
        self.min_values.append(item)

    def avg(self) -> float | None:
        if not self.values:
            return None
        return self.total / len(self.values)

    def std(self) -> float | None:
        if not self.values:
            return None
        mean = self.total / len(self.values)
        variance = max(self.total_sq / len(self.values) - mean * mean, 0.0)
        return sqrt(variance)

    def high(self) -> float | None:
        return self.max_values[0][1] if self.max_values else None

    def low(self) -> float | None:
        return self.min_values[0][1] if self.min_values else None

    def as_list(self) -> list[float]:
        return [value for _, value in self.values]


def backtest_generated_intraday_strategy(
    bars: list[BarRecord],
    config: GeneratedStrategyConfig,
) -> list[TradeRecord]:
    if len(bars) < 2:
        return []

    params = config.params
    begin_time = _parse_hhmm(str(params.get("begin_time", "0848")), "begin_time")
    end_time = _parse_hhmm(str(params.get("end_time", "1240")), "end_time")
    force_exit_time = _parse_hhmm(
        str(params.get("force_exit_time", "1312")),
        "force_exit_time",
    )
    max_hold_bars = int(params.get("max_hold_bars", 30))
    cooldown_bars = int(params.get("cooldown_bars", 0))
    fixed_tp = float(params.get("fixed_tp", 60.0))
    fixed_sl = float(params.get("fixed_sl", 40.0))

    indicators = _IndicatorState(params)
    trades: list[TradeRecord] = []
    position: _OpenPosition | None = None
    cooldown_until = -1
    current_date = None

    ordered_bars = bars if bars[0].ts <= bars[-1].ts else sorted(bars, key=lambda item: item.ts)
    for index, bar in enumerate(ordered_bars):
        bar_date = bar.ts.date()
        if current_date != bar_date:
            current_date = bar_date
            indicators.reset_day()
            if position is not None:
                trades.append(_close_position(position, bar))
                position = None
                cooldown_until = index + cooldown_bars

        if position is not None:
            exit_trade = _maybe_exit_position(
                position=position,
                bar=bar,
                index=index,
                fixed_tp=fixed_tp,
                fixed_sl=fixed_sl,
                max_hold_bars=max_hold_bars,
                force_exit_time=force_exit_time,
            )
            if exit_trade is not None:
                trades.append(exit_trade)
                position = None
                cooldown_until = index + cooldown_bars
                indicators.update(bar)
                continue

        if (
            position is None
            and index >= cooldown_until
            and begin_time <= bar.ts.time() <= end_time
        ):
            direction = _entry_direction(config, bar, indicators.snapshot())
            if direction != 0:
                position = _OpenPosition(
                    entry_time=bar.ts,
                    entry_price=float(bar.open),
                    direction=direction,
                    entry_index=index,
                    entry_date=bar_date,
                )

        indicators.update(bar)

    return trades


class _IndicatorState:
    def __init__(self, params: dict[str, Any]) -> None:
        self.don = _RollingWindow(int(params.get("don_len", 20)), deque())
        self.bb = _RollingWindow(int(params.get("bb_len", 20)), deque())
        self.vol = _RollingWindow(int(params.get("vol_len", 20)), deque())
        self.momentum = _RollingWindow(int(params.get("momentum_bars", 3)), deque())
        self.ema_fast_len = int(params.get("ema_fast", 4))
        self.ema_mid_len = int(params.get("ema_mid", 10))
        self.ema_slow_len = int(params.get("ema_slow", 40))
        self.ema_fast: float | None = None
        self.ema_mid: float | None = None
        self.ema_slow: float | None = None
        self.prev_close: float | None = None
        self.prev_high: float | None = None
        self.prev_low: float | None = None
        self.day_high: float | None = None
        self.day_low: float | None = None
        self.vwap_num = 0.0
        self.vwap_den = 0.0
        self.prev_vwap: float | None = None
        self.or_high: float | None = None
        self.or_low: float | None = None
        self.or_start = _parse_hhmm(str(params.get("or_start", "0845")), "or_start")
        self.or_end = _parse_hhmm(str(params.get("or_end", "0915")), "or_end")

    def reset_day(self) -> None:
        self.day_high = None
        self.day_low = None
        self.vwap_num = 0.0
        self.vwap_den = 0.0
        self.prev_vwap = None
        self.or_high = None
        self.or_low = None

    def snapshot(self) -> dict[str, Any]:
        bb_avg = self.bb.avg()
        bb_std = self.bb.std()
        return {
            "don_high": self.don.high(),
            "don_low": self.don.low(),
            "bb_avg": bb_avg,
            "bb_std": bb_std,
            "vol_avg": self.vol.avg(),
            "momentum_values": self.momentum.as_list(),
            "ema_fast": self.ema_fast,
            "ema_mid": self.ema_mid,
            "ema_slow": self.ema_slow,
            "prev_close": self.prev_close,
            "prev_high": self.prev_high,
            "prev_low": self.prev_low,
            "day_high": self.day_high,
            "day_low": self.day_low,
            "vwap": self.prev_vwap,
            "or_high": self.or_high,
            "or_low": self.or_low,
        }

    def update(self, bar: BarRecord) -> None:
        close = float(bar.close)
        high = float(bar.high)
        low = float(bar.low)
        open_price = float(bar.open)
        volume = float(bar.volume) if bar.volume is not None else 1.0
        typical = (high + low + close) / 3.0

        self.day_high = high if self.day_high is None else max(self.day_high, high)
        self.day_low = low if self.day_low is None else min(self.day_low, low)
        self.vwap_num += typical * volume
        self.vwap_den += volume
        self.prev_vwap = self.vwap_num / self.vwap_den if self.vwap_den else None

        if self.or_start <= bar.ts.time() <= self.or_end:
            self.or_high = high if self.or_high is None else max(self.or_high, high)
            self.or_low = low if self.or_low is None else min(self.or_low, low)

        self.don.add(high)
        self.bb.add(close)
        self.vol.add(volume)
        self.momentum.add(close - open_price)
        self.ema_fast = _ema_update(self.ema_fast, close, self.ema_fast_len)
        self.ema_mid = _ema_update(self.ema_mid, close, self.ema_mid_len)
        self.ema_slow = _ema_update(self.ema_slow, close, self.ema_slow_len)
        self.prev_close = close
        self.prev_high = high
        self.prev_low = low


def _entry_direction(
    config: GeneratedStrategyConfig,
    bar: BarRecord,
    ind: dict[str, Any],
) -> int:
    allowed = _allowed_directions(config.direction)
    family = config.family
    params = config.params

    if family == "trend_breakout":
        return _trend_breakout(bar, ind, params, allowed)
    if family == "open_range_breakout":
        return _open_range_breakout(bar, ind, params, allowed)
    if family == "vwap_pullback":
        return _vwap_pullback(bar, ind, params, allowed)
    if family == "mean_reversion_range":
        return _mean_reversion_range(bar, ind, params, allowed)
    if family == "volume_breakout":
        return _volume_breakout(bar, ind, params, allowed)
    if family == "breakdown_momentum":
        return _breakdown_momentum(bar, ind, params, allowed)
    if family == "slow_grind_trend":
        return _slow_grind_trend(bar, ind, params, allowed)
    if family == "afternoon_trend_extension":
        return _afternoon_trend_extension(bar, ind, params, allowed)

    raise ValueError(f"unsupported strategy family: {family}")


def _trend_breakout(bar: BarRecord, ind: dict, params: dict, allowed: set[int]) -> int:
    return _breakout_with_ema(bar, ind, params, allowed)


def _open_range_breakout(bar: BarRecord, ind: dict, params: dict, allowed: set[int]) -> int:
    or_high = ind.get("or_high")
    or_low = ind.get("or_low")
    if or_high is None or or_low is None:
        return 0
    buffer = float(params.get("or_buffer", 0.0))
    break_limit = float(params.get("break_limit", 80.0))
    return _breakout_direction(float(bar.open), or_high, or_low, buffer, break_limit, allowed)


def _vwap_pullback(bar: BarRecord, ind: dict, params: dict, allowed: set[int]) -> int:
    vwap = ind.get("vwap")
    ema_fast = ind.get("ema_fast")
    prev_high = ind.get("prev_high")
    prev_low = ind.get("prev_low")
    if None in {vwap, ema_fast, prev_high, prev_low}:
        return 0
    buffer = float(params.get("vwap_buffer", 0.0))
    open_price = float(bar.open)
    if 1 in allowed and open_price > vwap + buffer and open_price > ema_fast and open_price > prev_high:
        return 1
    if -1 in allowed and open_price < vwap - buffer and open_price < ema_fast and open_price < prev_low:
        return -1
    return 0


def _mean_reversion_range(bar: BarRecord, ind: dict, params: dict, allowed: set[int]) -> int:
    bb_avg = ind.get("bb_avg")
    bb_std = ind.get("bb_std")
    day_high = ind.get("day_high")
    day_low = ind.get("day_low")
    prev_close = ind.get("prev_close")
    if None in {bb_avg, bb_std, day_high, day_low, prev_close}:
        return 0
    if day_high - day_low < float(params.get("range_filter", 80.0)):
        return 0
    band = float(params.get("bb_k", 2.0)) * bb_std
    open_price = float(bar.open)
    if 1 in allowed and prev_close < bb_avg - band and open_price > prev_close:
        return 1
    if -1 in allowed and prev_close > bb_avg + band and open_price < prev_close:
        return -1
    return 0


def _volume_breakout(bar: BarRecord, ind: dict, params: dict, allowed: set[int]) -> int:
    vol_avg = ind.get("vol_avg")
    if vol_avg is None or bar.volume is None:
        return 0
    if float(bar.volume) < vol_avg * float(params.get("vol_k", 1.5)):
        return 0
    return _breakout_with_donchian(bar, ind, params, allowed)


def _breakdown_momentum(bar: BarRecord, ind: dict, params: dict, allowed: set[int]) -> int:
    values = ind.get("momentum_values") or []
    if len(values) < int(params.get("momentum_bars", 3)):
        return 0
    prev_high = ind.get("prev_high")
    prev_low = ind.get("prev_low")
    if prev_high is None or prev_low is None:
        return 0
    open_price = float(bar.open)
    if 1 in allowed and all(value > 0 for value in values) and open_price > prev_high:
        return 1
    if -1 in allowed and all(value < 0 for value in values) and open_price < prev_low:
        return -1
    return 0


def _slow_grind_trend(bar: BarRecord, ind: dict, params: dict, allowed: set[int]) -> int:
    ema_fast = ind.get("ema_fast")
    ema_mid = ind.get("ema_mid")
    ema_slow = ind.get("ema_slow")
    vwap = ind.get("vwap")
    if None in {ema_fast, ema_mid, ema_slow, vwap}:
        return 0
    buffer = float(params.get("vwap_buffer", 0.0))
    open_price = float(bar.open)
    if 1 in allowed and ema_fast > ema_mid > ema_slow and open_price > vwap + buffer:
        return 1
    if -1 in allowed and ema_fast < ema_mid < ema_slow and open_price < vwap - buffer:
        return -1
    return 0


def _afternoon_trend_extension(bar: BarRecord, ind: dict, params: dict, allowed: set[int]) -> int:
    return _breakout_with_ema(bar, ind, params, allowed)


def _breakout_with_ema(bar: BarRecord, ind: dict, params: dict, allowed: set[int]) -> int:
    ema_slow = ind.get("ema_slow")
    prev_close = ind.get("prev_close")
    if ema_slow is None or prev_close is None:
        return 0
    direction = _breakout_with_donchian(bar, ind, params, allowed)
    if direction == 1 and prev_close >= ema_slow:
        return 1
    if direction == -1 and prev_close <= ema_slow:
        return -1
    return 0


def _breakout_with_donchian(bar: BarRecord, ind: dict, params: dict, allowed: set[int]) -> int:
    don_high = ind.get("don_high")
    don_low = ind.get("don_low")
    if don_high is None or don_low is None:
        return 0
    return _breakout_direction(
        float(bar.open),
        float(don_high),
        float(don_low),
        float(params.get("min_break", 0.0)),
        float(params.get("break_limit", 80.0)),
        allowed,
    )


def _breakout_direction(
    open_price: float,
    high_level: float,
    low_level: float,
    buffer: float,
    break_limit: float,
    allowed: set[int],
) -> int:
    long_break = open_price - high_level
    short_break = low_level - open_price
    if 1 in allowed and buffer < long_break <= break_limit:
        return 1
    if -1 in allowed and buffer < short_break <= break_limit:
        return -1
    return 0


def _maybe_exit_position(
    position: _OpenPosition,
    bar: BarRecord,
    index: int,
    fixed_tp: float,
    fixed_sl: float,
    max_hold_bars: int,
    force_exit_time: time,
) -> TradeRecord | None:
    open_price = float(bar.open)
    unrealized = (open_price - position.entry_price) * position.direction
    held_bars = index - position.entry_index
    should_exit = (
        unrealized >= fixed_tp
        or unrealized <= -fixed_sl
        or held_bars >= max_hold_bars
        or bar.ts.time() >= force_exit_time
        or bar.ts.date() != position.entry_date
    )
    if not should_exit:
        return None
    return _close_position(position, bar)


def _close_position(position: _OpenPosition, bar: BarRecord) -> TradeRecord:
    exit_price = float(bar.open)
    return TradeRecord(
        entry_time=position.entry_time,
        exit_time=bar.ts,
        entry_price=position.entry_price,
        exit_price=exit_price,
        direction=position.direction,
        pnl=(exit_price - position.entry_price) * position.direction,
    )


def _allowed_directions(direction: str) -> set[int]:
    if direction == "long":
        return {1}
    if direction == "short":
        return {-1}
    if direction == "both":
        return {1, -1}
    raise ValueError(f"invalid strategy direction: {direction}")


def _ema_update(previous: float | None, value: float, length: int) -> float:
    if previous is None:
        return value
    alpha = 2.0 / (length + 1.0)
    return value * alpha + previous * (1.0 - alpha)


def _parse_hhmm(value: str, name: str) -> time:
    cleaned = value.strip()
    if len(cleaned) != 4 or not cleaned.isdigit():
        raise ValueError(f"{name} must use HHMM format")
    try:
        return time(hour=int(cleaned[:2]), minute=int(cleaned[2:]))
    except ValueError as exc:
        raise ValueError(f"invalid {name}: {value}") from exc


__all__ = ["backtest_generated_intraday_strategy"]
