from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from typing import Any

from mqre_v2.core.bars import BarRecord
from mqre_v2.core.trades import TradeRecord
from mqre_v2.strategy.strategy_1001plus import (
    _IndicatorState,
    _entry_direction,
    _parse_hhmm,
    _validate_params,
)


@dataclass(frozen=True, slots=True)
class Strategy1001PlusV2ExitParams:
    strategy_name: str = "1001plus_v2_exit"
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
    use_vwap_filter: bool = True
    trailing_start_atr: float = 2.0
    trailing_giveback: float = 0.5
    time_stop_bars: int = 60
    tp_tighten_factor: float = 0.5
    volatility_exit_atr_ratio: float = 0.6


@dataclass(slots=True)
class _V2OpenPosition:
    entry_time: datetime
    entry_price: float
    direction: int
    entry_index: int
    entry_date: object
    entry_atr: float
    best_favorable: float = 0.0
    trailing_active: bool = False
    profit_locked: bool = False
    locked_stop_price: float | None = None


def backtest_strategy_1001plus_v2_exit(
    bars: list[BarRecord],
    params: Strategy1001PlusV2ExitParams | None = None,
) -> list[TradeRecord]:
    effective = params or Strategy1001PlusV2ExitParams()
    _validate_v2_params(effective)
    if len(bars) < 2:
        return []

    begin_time = _parse_hhmm(effective.begin_time, "begin_time")
    end_time = _parse_hhmm(effective.end_time, "end_time")
    force_exit_time = _parse_hhmm(effective.force_exit_time, "force_exit_time")
    ordered_bars = bars if bars[0].ts <= bars[-1].ts else sorted(bars, key=lambda item: item.ts)

    indicators = _IndicatorState(effective)
    trades: list[TradeRecord] = []
    position: _V2OpenPosition | None = None
    cooldown_until = -1
    current_date: object | None = None

    for index, bar in enumerate(ordered_bars):
        bar_date = bar.ts.date()
        if current_date != bar_date:
            if position is not None:
                trades.append(_close_position(position, bar, float(bar.open)))
                position = None
                cooldown_until = index + effective.cooldown_bars
            current_date = bar_date
            indicators.start_day(bar_date)

        snapshot = indicators.snapshot()

        if position is not None:
            exit_trade = _maybe_exit_position_v2(
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
                position = _V2OpenPosition(
                    entry_time=bar.ts,
                    entry_price=float(bar.open),
                    direction=direction,
                    entry_index=index,
                    entry_date=bar_date,
                    entry_atr=float(entry_atr),
                )

        indicators.update_with_completed_bar(bar)

    return trades


def _maybe_exit_position_v2(
    position: _V2OpenPosition,
    bar: BarRecord,
    index: int,
    snapshot: dict[str, Any],
    params: Strategy1001PlusV2ExitParams,
    force_exit_time: time,
) -> TradeRecord | None:
    open_price = float(bar.open)
    held_bars = index - position.entry_index
    current_atr = snapshot.get("atr")
    rsi = snapshot.get("rsi")

    if (
        bar.ts.time() >= force_exit_time
        or bar.ts.date() != position.entry_date
        or held_bars >= params.time_stop_bars
    ):
        return _close_position(position, bar, open_price)

    if _rsi_reversal(position.direction, rsi, params):
        return _close_position(position, bar, open_price)

    if (
        current_atr is not None
        and held_bars > 1
        and float(current_atr) <= position.entry_atr * params.volatility_exit_atr_ratio
    ):
        return _close_position(position, bar, open_price)

    if position.direction == 1:
        return _maybe_exit_long(position, bar, params)
    return _maybe_exit_short(position, bar, params)


def _maybe_exit_long(
    position: _V2OpenPosition,
    bar: BarRecord,
    params: Strategy1001PlusV2ExitParams,
) -> TradeRecord | None:
    high = float(bar.high)
    low = float(bar.low)
    entry = position.entry_price
    atr = position.entry_atr

    initial_stop = entry - (atr * params.atr_stop_k)
    if low <= initial_stop:
        return _close_position(position, bar, initial_stop)

    favorable = max(position.best_favorable, high - entry)
    position.best_favorable = favorable
    _activate_profit_lock(position, params)
    _activate_trailing(position, params)

    locked_stop = _locked_stop(position, params)
    if locked_stop is not None and low <= locked_stop:
        return _close_position(position, bar, locked_stop)

    take_profit = entry + (atr * params.atr_take_profit_k)
    if high >= take_profit:
        return _close_position(position, bar, take_profit)

    return None


def _maybe_exit_short(
    position: _V2OpenPosition,
    bar: BarRecord,
    params: Strategy1001PlusV2ExitParams,
) -> TradeRecord | None:
    high = float(bar.high)
    low = float(bar.low)
    entry = position.entry_price
    atr = position.entry_atr

    initial_stop = entry + (atr * params.atr_stop_k)
    if high >= initial_stop:
        return _close_position(position, bar, initial_stop)

    favorable = max(position.best_favorable, entry - low)
    position.best_favorable = favorable
    _activate_profit_lock(position, params)
    _activate_trailing(position, params)

    locked_stop = _locked_stop(position, params)
    if locked_stop is not None and high >= locked_stop:
        return _close_position(position, bar, locked_stop)

    take_profit = entry - (atr * params.atr_take_profit_k)
    if low <= take_profit:
        return _close_position(position, bar, take_profit)

    return None


def _activate_profit_lock(
    position: _V2OpenPosition,
    params: Strategy1001PlusV2ExitParams,
) -> None:
    tp1 = position.entry_atr * params.atr_take_profit_k * params.tp_tighten_factor
    if position.profit_locked or position.best_favorable < tp1:
        return

    position.profit_locked = True
    locked_profit = position.entry_atr * params.atr_stop_k * params.tp_tighten_factor
    position.locked_stop_price = position.entry_price + (
        locked_profit * position.direction
    )


def _activate_trailing(
    position: _V2OpenPosition,
    params: Strategy1001PlusV2ExitParams,
) -> None:
    if position.best_favorable >= position.entry_atr * params.trailing_start_atr:
        position.trailing_active = True


def _locked_stop(
    position: _V2OpenPosition,
    params: Strategy1001PlusV2ExitParams,
) -> float | None:
    stops: list[float] = []
    if position.locked_stop_price is not None:
        stops.append(position.locked_stop_price)
    if position.trailing_active:
        giveback_stop = position.entry_price + (
            position.best_favorable
            * (1.0 - params.trailing_giveback)
            * position.direction
        )
        stops.append(giveback_stop)

    if not stops:
        return None
    if position.direction == 1:
        return max(stops)
    return min(stops)


def _rsi_reversal(
    direction: int,
    rsi: Any,
    params: Strategy1001PlusV2ExitParams,
) -> bool:
    if rsi is None:
        return False
    if direction == 1 and float(rsi) <= params.rsi_long_exit:
        return True
    if direction == -1 and float(rsi) >= params.rsi_short_exit:
        return True
    return False


def _close_position(
    position: _V2OpenPosition,
    bar: BarRecord,
    exit_price: float,
) -> TradeRecord:
    return TradeRecord(
        entry_time=position.entry_time,
        exit_time=bar.ts,
        entry_price=position.entry_price,
        exit_price=float(exit_price),
        direction=position.direction,
        pnl=(float(exit_price) - position.entry_price) * position.direction,
    )


def _validate_v2_params(params: Strategy1001PlusV2ExitParams) -> None:
    _validate_params(params)
    for name in [
        "trailing_start_atr",
        "time_stop_bars",
        "tp_tighten_factor",
        "volatility_exit_atr_ratio",
    ]:
        if float(getattr(params, name)) <= 0:
            raise ValueError(f"{name} must be > 0")
    if not 0.0 < params.trailing_giveback < 1.0:
        raise ValueError("trailing_giveback must be between 0 and 1")


__all__ = [
    "Strategy1001PlusV2ExitParams",
    "backtest_strategy_1001plus_v2_exit",
]
