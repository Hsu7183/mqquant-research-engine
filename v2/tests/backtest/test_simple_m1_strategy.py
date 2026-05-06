from __future__ import annotations

from datetime import datetime

from mqre_v2.backtest.simple_m1_strategy import (
    SimpleM1StrategyParams,
    backtest_simple_m1_strategy,
)
from mqre_v2.core.bars import BarRecord


def test_m1_bars_can_generate_trade_record() -> None:
    trades = backtest_simple_m1_strategy(
        [
            _bar("2026-01-02 08:48", 100, 115),
            _bar("2026-01-02 08:49", 120, 120),
            _bar("2026-01-02 08:50", 150, 150),
        ],
        SimpleM1StrategyParams(entry_buffer=10, take_profit=20, stop_loss=50),
    )

    assert len(trades) == 1
    assert trades[0].entry_time == datetime(2026, 1, 2, 8, 49)
    assert trades[0].exit_time == datetime(2026, 1, 2, 8, 50)
    assert trades[0].direction == 1
    assert trades[0].pnl == 30


def test_long_take_profit_exits_at_current_open() -> None:
    trades = backtest_simple_m1_strategy(
        [
            _bar("2026-01-02 08:48", 100, 112),
            _bar("2026-01-02 08:49", 100, 100),
            _bar("2026-01-02 08:50", 130, 130),
        ],
        SimpleM1StrategyParams(entry_buffer=10, take_profit=30, stop_loss=50),
    )

    assert trades[0].entry_price == 100
    assert trades[0].exit_price == 130
    assert trades[0].pnl == 30


def test_short_take_profit_exits_at_current_open() -> None:
    trades = backtest_simple_m1_strategy(
        [
            _bar("2026-01-02 08:48", 120, 105),
            _bar("2026-01-02 08:49", 100, 100),
            _bar("2026-01-02 08:50", 70, 70),
        ],
        SimpleM1StrategyParams(entry_buffer=10, take_profit=25, stop_loss=50),
    )

    assert trades[0].direction == -1
    assert trades[0].entry_price == 100
    assert trades[0].exit_price == 70
    assert trades[0].pnl == 30


def test_stop_loss_exits_long_position() -> None:
    trades = backtest_simple_m1_strategy(
        [
            _bar("2026-01-02 08:48", 100, 115),
            _bar("2026-01-02 08:49", 100, 100),
            _bar("2026-01-02 08:50", 80, 80),
        ],
        SimpleM1StrategyParams(entry_buffer=10, take_profit=50, stop_loss=20),
    )

    assert trades[0].direction == 1
    assert trades[0].pnl == -20


def test_stop_loss_exits_short_position() -> None:
    trades = backtest_simple_m1_strategy(
        [
            _bar("2026-01-02 08:48", 120, 100),
            _bar("2026-01-02 08:49", 100, 100),
            _bar("2026-01-02 08:50", 125, 125),
        ],
        SimpleM1StrategyParams(entry_buffer=10, take_profit=50, stop_loss=20),
    )

    assert trades[0].direction == -1
    assert trades[0].pnl == -25


def test_max_hold_bars_exits_position() -> None:
    trades = backtest_simple_m1_strategy(
        [
            _bar("2026-01-02 08:48", 100, 115),
            _bar("2026-01-02 08:49", 100, 100),
            _bar("2026-01-02 08:50", 101, 101),
        ],
        SimpleM1StrategyParams(
            entry_buffer=10,
            take_profit=50,
            stop_loss=50,
            max_hold_bars=1,
        ),
    )

    assert trades[0].exit_time == datetime(2026, 1, 2, 8, 50)
    assert trades[0].pnl == 1


def test_force_exit_time_exits_position() -> None:
    trades = backtest_simple_m1_strategy(
        [
            _bar("2026-01-02 12:39", 100, 115),
            _bar("2026-01-02 12:40", 100, 100),
            _bar("2026-01-02 13:12", 103, 103),
        ],
        SimpleM1StrategyParams(
            entry_buffer=10,
            take_profit=50,
            stop_loss=50,
            max_hold_bars=30,
            force_exit_time="1312",
        ),
    )

    assert trades[0].exit_time == datetime(2026, 1, 2, 13, 12)
    assert trades[0].pnl == 3


def _bar(ts: str, open_price: float, close_price: float) -> BarRecord:
    open_value = float(open_price)
    close_value = float(close_price)
    return BarRecord(
        ts=datetime.strptime(ts, "%Y-%m-%d %H:%M"),
        open=open_value,
        high=max(open_value, close_value),
        low=min(open_value, close_value),
        close=close_value,
    )
