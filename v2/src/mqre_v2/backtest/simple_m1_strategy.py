from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time

from mqre_v2.core.bars import BarRecord
from mqre_v2.core.trades import TradeRecord


@dataclass(frozen=True, slots=True)
class SimpleM1StrategyParams:
    strategy_name: str = "simple_m1_momentum"
    entry_buffer: float = 10.0
    take_profit: float = 30.0
    stop_loss: float = 20.0
    max_hold_bars: int = 30
    begin_time: str = "0848"
    end_time: str = "1240"
    force_exit_time: str = "1312"


@dataclass(frozen=True, slots=True)
class _OpenPosition:
    entry_time: datetime
    entry_price: float
    direction: int
    entry_index: int


def backtest_simple_m1_strategy(
    bars: list[BarRecord],
    params: SimpleM1StrategyParams,
) -> list[TradeRecord]:
    _validate_params(params)
    if len(bars) < 2:
        return []

    begin_time = _parse_hhmm(params.begin_time, "begin_time")
    end_time = _parse_hhmm(params.end_time, "end_time")
    force_exit_time = _parse_hhmm(params.force_exit_time, "force_exit_time")

    trades: list[TradeRecord] = []
    position: _OpenPosition | None = None

    for index in range(1, len(bars)):
        previous_bar = bars[index - 1]
        current_bar = bars[index]
        current_time = current_bar.ts.time()

        if position is not None:
            exit_trade = _maybe_exit_position(
                position=position,
                bar=current_bar,
                index=index,
                params=params,
                force_exit_time=force_exit_time,
            )
            if exit_trade is not None:
                trades.append(exit_trade)
                position = None
                continue

        if position is None and begin_time <= current_time <= end_time:
            direction = _entry_signal(previous_bar, params.entry_buffer)
            if direction != 0:
                position = _OpenPosition(
                    entry_time=current_bar.ts,
                    entry_price=float(current_bar.open),
                    direction=direction,
                    entry_index=index,
                )

    return trades


def _validate_params(params: SimpleM1StrategyParams) -> None:
    if params.entry_buffer <= 0:
        raise ValueError("entry_buffer must be > 0")
    if params.take_profit <= 0:
        raise ValueError("take_profit must be > 0")
    if params.stop_loss <= 0:
        raise ValueError("stop_loss must be > 0")
    if params.max_hold_bars <= 0:
        raise ValueError("max_hold_bars must be > 0")


def _entry_signal(previous_bar: BarRecord, entry_buffer: float) -> int:
    if previous_bar.close - previous_bar.open >= entry_buffer:
        return 1
    if previous_bar.open - previous_bar.close >= entry_buffer:
        return -1
    return 0


def _maybe_exit_position(
    position: _OpenPosition,
    bar: BarRecord,
    index: int,
    params: SimpleM1StrategyParams,
    force_exit_time: time,
) -> TradeRecord | None:
    open_price = float(bar.open)
    unrealized = (open_price - position.entry_price) * position.direction
    held_bars = index - position.entry_index

    should_exit = (
        unrealized >= params.take_profit
        or unrealized <= -params.stop_loss
        or held_bars >= params.max_hold_bars
        or bar.ts.time() >= force_exit_time
    )
    if not should_exit:
        return None

    return TradeRecord(
        entry_time=position.entry_time,
        exit_time=bar.ts,
        entry_price=position.entry_price,
        exit_price=open_price,
        direction=position.direction,
        pnl=unrealized,
    )


def _parse_hhmm(value: str, name: str) -> time:
    cleaned = value.strip()
    if len(cleaned) != 4 or not cleaned.isdigit():
        raise ValueError(f"{name} must use HHMM format")
    hour = int(cleaned[:2])
    minute = int(cleaned[2:])
    try:
        return time(hour=hour, minute=minute)
    except ValueError as exc:
        raise ValueError(f"invalid {name}: {value}") from exc


__all__ = ["SimpleM1StrategyParams", "backtest_simple_m1_strategy"]
