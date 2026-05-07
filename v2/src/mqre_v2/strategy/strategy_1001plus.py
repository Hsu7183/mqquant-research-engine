from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, time
from typing import Any

from mqre_v2.core.bars import BarRecord
from mqre_v2.core.trades import TradeRecord


@dataclass(frozen=True, slots=True)
class Strategy1001PlusParams:
    strategy_name: str = "1001plus_baseline"
    ema_short_len: int = 8
    ema_long_len: int = 34
    rsi_len: int = 14
    atr_len: int = 14
    donchian_len: int = 20
    rsi_long_threshold: float = 55.0
    rsi_short_threshold: float = 45.0
    rsi_long_exit: float = 48.0
    rsi_short_exit: float = 52.0
    min_break: float = 0.0
    atr_stop_k: float = 1.5
    atr_take_profit_k: float = 3.0
    max_hold_bars: int = 60
    cooldown_bars: int = 1
    begin_time: str = "0848"
    end_time: str = "1240"
    force_exit_time: str = "1312"


@dataclass(frozen=True, slots=True)
class _OpenPosition:
    entry_time: datetime
    entry_price: float
    direction: int
    entry_index: int
    entry_date: object
    entry_atr: float


class _IndicatorState:
    def __init__(self, params: Strategy1001PlusParams) -> None:
        self.params = params
        self.ema_short: float | None = None
        self.ema_long: float | None = None
        self.rsi_avg_gain: float | None = None
        self.rsi_avg_loss: float | None = None
        self.atr: float | None = None
        self.prev_close: float | None = None
        self.prev_high: float | None = None
        self.prev_low: float | None = None
        self.prev_don_high: float | None = None
        self.prev_don_low: float | None = None
        self.vwap_num = 0.0
        self.vwap_den = 0.0
        self.vwap: float | None = None
        self.don_high_values: deque[float] = deque(maxlen=params.donchian_len)
        self.don_low_values: deque[float] = deque(maxlen=params.donchian_len)
        self.completed_count = 0
        self.current_date: object | None = None

    def start_day(self, bar_date: object) -> None:
        self.current_date = bar_date
        self.prev_high = None
        self.prev_low = None
        self.prev_don_high = None
        self.prev_don_low = None
        self.vwap_num = 0.0
        self.vwap_den = 0.0
        self.vwap = None
        self.don_high_values.clear()
        self.don_low_values.clear()

    def snapshot(self) -> dict[str, Any]:
        return {
            "ema_short": self.ema_short,
            "ema_long": self.ema_long,
            "rsi": self._rsi(),
            "atr": self.atr,
            "vwap": self.vwap,
            "prev_close": self.prev_close,
            "prev_high": self.prev_high,
            "prev_low": self.prev_low,
            "prev_don_high": self.prev_don_high,
            "prev_don_low": self.prev_don_low,
            "completed_count": self.completed_count,
        }

    def update_with_completed_bar(self, bar: BarRecord) -> None:
        close = float(bar.close)
        high = float(bar.high)
        low = float(bar.low)
        volume = float(bar.volume) if bar.volume is not None else 1.0
        typical = (high + low + close) / 3.0

        self.prev_don_high = max(self.don_high_values) if self.don_high_values else None
        self.prev_don_low = min(self.don_low_values) if self.don_low_values else None

        self.ema_short = _ema_update(self.ema_short, close, self.params.ema_short_len)
        self.ema_long = _ema_update(self.ema_long, close, self.params.ema_long_len)

        if self.prev_close is not None:
            delta = close - self.prev_close
            gain = max(delta, 0.0)
            loss = max(-delta, 0.0)
            self.rsi_avg_gain = _wilder_update(
                self.rsi_avg_gain,
                gain,
                self.params.rsi_len,
            )
            self.rsi_avg_loss = _wilder_update(
                self.rsi_avg_loss,
                loss,
                self.params.rsi_len,
            )

            true_range = max(
                high - low,
                abs(high - self.prev_close),
                abs(low - self.prev_close),
            )
            self.atr = _wilder_update(self.atr, true_range, self.params.atr_len)
        else:
            self.atr = _wilder_update(self.atr, high - low, self.params.atr_len)

        self.vwap_num += typical * volume
        self.vwap_den += volume
        self.vwap = self.vwap_num / self.vwap_den if self.vwap_den else None

        self.don_high_values.append(high)
        self.don_low_values.append(low)
        self.prev_close = close
        self.prev_high = high
        self.prev_low = low
        self.completed_count += 1

    def _rsi(self) -> float | None:
        if self.rsi_avg_gain is None or self.rsi_avg_loss is None:
            return None
        if self.rsi_avg_loss == 0:
            return 100.0 if self.rsi_avg_gain > 0 else 50.0
        rs = self.rsi_avg_gain / self.rsi_avg_loss
        return 100.0 - (100.0 / (1.0 + rs))


def backtest_strategy_1001plus(
    bars: list[BarRecord],
    params: Strategy1001PlusParams | None = None,
) -> list[TradeRecord]:
    effective = params or Strategy1001PlusParams()
    _validate_params(effective)
    if len(bars) < 2:
        return []

    begin_time = _parse_hhmm(effective.begin_time, "begin_time")
    end_time = _parse_hhmm(effective.end_time, "end_time")
    force_exit_time = _parse_hhmm(effective.force_exit_time, "force_exit_time")
    ordered_bars = bars if bars[0].ts <= bars[-1].ts else sorted(bars, key=lambda item: item.ts)

    indicators = _IndicatorState(effective)
    trades: list[TradeRecord] = []
    position: _OpenPosition | None = None
    cooldown_until = -1
    current_date: object | None = None

    for index, bar in enumerate(ordered_bars):
        bar_date = bar.ts.date()
        if current_date != bar_date:
            if position is not None:
                trades.append(_close_position(position, bar))
                position = None
                cooldown_until = index + effective.cooldown_bars
            current_date = bar_date
            indicators.start_day(bar_date)

        snapshot = indicators.snapshot()

        if position is not None:
            exit_trade = _maybe_exit_position(
                position=position,
                bar=bar,
                index=index,
                snapshot=snapshot,
                params=effective,
                force_exit_time=force_exit_time,
            )
            if exit_trade is not None:
                trades.append(exit_trade)
                position = None
                cooldown_until = index + effective.cooldown_bars
                indicators.update_with_completed_bar(bar)
                continue

        if (
            position is None
            and index >= cooldown_until
            and begin_time <= bar.ts.time() <= end_time
        ):
            direction = _entry_direction(snapshot, effective)
            entry_atr = snapshot.get("atr")
            if direction != 0 and entry_atr is not None and entry_atr > 0:
                position = _OpenPosition(
                    entry_time=bar.ts,
                    entry_price=float(bar.open),
                    direction=direction,
                    entry_index=index,
                    entry_date=bar_date,
                    entry_atr=float(entry_atr),
                )

        indicators.update_with_completed_bar(bar)

    return trades


def _entry_direction(snapshot: dict[str, Any], params: Strategy1001PlusParams) -> int:
    ema_short = snapshot.get("ema_short")
    ema_long = snapshot.get("ema_long")
    rsi = snapshot.get("rsi")
    vwap = snapshot.get("vwap")
    prev_close = snapshot.get("prev_close")
    prev_high = snapshot.get("prev_high")
    prev_low = snapshot.get("prev_low")
    prev_don_high = snapshot.get("prev_don_high")
    prev_don_low = snapshot.get("prev_don_low")

    if None in {
        ema_short,
        ema_long,
        rsi,
        vwap,
        prev_close,
        prev_high,
        prev_low,
        prev_don_high,
        prev_don_low,
    }:
        return 0
    if int(snapshot.get("completed_count", 0)) < params.donchian_len + 1:
        return 0

    long_break = float(prev_high) > float(prev_don_high) + params.min_break
    short_break = float(prev_low) < float(prev_don_low) - params.min_break

    if (
        float(ema_short) > float(ema_long)
        and float(rsi) > params.rsi_long_threshold
        and float(prev_close) > float(vwap)
        and long_break
    ):
        return 1

    if (
        float(ema_short) < float(ema_long)
        and float(rsi) < params.rsi_short_threshold
        and float(prev_close) < float(vwap)
        and short_break
    ):
        return -1

    return 0


def _maybe_exit_position(
    position: _OpenPosition,
    bar: BarRecord,
    index: int,
    snapshot: dict[str, Any],
    params: Strategy1001PlusParams,
    force_exit_time: time,
) -> TradeRecord | None:
    open_price = float(bar.open)
    unrealized = (open_price - position.entry_price) * position.direction
    held_bars = index - position.entry_index
    rsi = snapshot.get("rsi")

    rsi_reversal = False
    if rsi is not None:
        if position.direction == 1 and float(rsi) <= params.rsi_long_exit:
            rsi_reversal = True
        if position.direction == -1 and float(rsi) >= params.rsi_short_exit:
            rsi_reversal = True

    should_exit = (
        unrealized <= -(position.entry_atr * params.atr_stop_k)
        or unrealized >= position.entry_atr * params.atr_take_profit_k
        or rsi_reversal
        or held_bars >= params.max_hold_bars
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


def _ema_update(previous: float | None, value: float, length: int) -> float:
    if previous is None:
        return value
    alpha = 2.0 / (length + 1.0)
    return value * alpha + previous * (1.0 - alpha)


def _wilder_update(previous: float | None, value: float, length: int) -> float:
    if previous is None:
        return value
    return ((previous * (length - 1.0)) + value) / length


def _validate_params(params: Strategy1001PlusParams) -> None:
    for name in [
        "ema_short_len",
        "ema_long_len",
        "rsi_len",
        "atr_len",
        "donchian_len",
        "max_hold_bars",
    ]:
        if int(getattr(params, name)) <= 0:
            raise ValueError(f"{name} must be > 0")
    if params.cooldown_bars < 0:
        raise ValueError("cooldown_bars must be >= 0")
    for name in ["atr_stop_k", "atr_take_profit_k"]:
        if float(getattr(params, name)) <= 0:
            raise ValueError(f"{name} must be > 0")


def _parse_hhmm(value: str, name: str) -> time:
    cleaned = value.strip()
    if len(cleaned) != 4 or not cleaned.isdigit():
        raise ValueError(f"{name} must use HHMM format")
    try:
        return time(hour=int(cleaned[:2]), minute=int(cleaned[2:]))
    except ValueError as exc:
        raise ValueError(f"invalid {name}: {value}") from exc


__all__ = ["Strategy1001PlusParams", "backtest_strategy_1001plus"]
