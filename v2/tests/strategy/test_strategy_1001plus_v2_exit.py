from __future__ import annotations

from datetime import datetime

from mqre_v2.core.bars import BarRecord
from mqre_v2.strategy.strategy_1001plus_v2_exit import (
    Strategy1001PlusV2ExitParams,
    backtest_strategy_1001plus_v2_exit,
)


def test_v2_exit_entry_still_uses_current_open() -> None:
    bars = _long_breakout_bars(exit_open=115)

    trades = backtest_strategy_1001plus_v2_exit(bars, _params())

    assert len(trades) == 1
    assert trades[0].entry_time == _dt("2026-01-02 08:49")
    assert trades[0].entry_price == 109
    _assert_entry_prices_are_bar_opens(trades, bars)


def test_v2_exit_does_not_use_current_close_for_entry() -> None:
    bars = [
        _bar("2026-01-02 08:45", 100, 101, 99, 100),
        _bar("2026-01-02 08:46", 100, 102, 99, 101),
        _bar("2026-01-02 08:47", 101, 103, 100, 102),
        _bar("2026-01-02 08:48", 102, 103, 101, 102),
        _bar("2026-01-02 08:49", 105, 250, 50, 250),
        _bar("2026-01-02 08:50", 250, 252, 248, 251),
        _bar("2026-01-02 08:51", 500, 500, 500, 500),
    ]

    trades = backtest_strategy_1001plus_v2_exit(bars, _params())

    assert trades
    assert trades[0].entry_time == _dt("2026-01-02 08:50")
    assert trades[0].entry_price == 250


def test_v2_exit_trailing_stop_can_lock_open_profit() -> None:
    bars = _long_breakout_bars(exit_open=109)
    bars.append(_bar("2026-01-02 08:51", 116, 120, 112, 113))

    trades = backtest_strategy_1001plus_v2_exit(
        bars,
        _params(
            atr_stop_k=10.0,
            atr_take_profit_k=20.0,
            trailing_start_atr=0.5,
            trailing_giveback=0.5,
            tp_tighten_factor=0.9,
        ),
    )

    assert len(trades) == 1
    assert trades[0].exit_time == _dt("2026-01-02 08:51")
    assert trades[0].exit_price > trades[0].entry_price


def test_v2_exit_time_stop_exits_after_configured_bars() -> None:
    bars = _long_breakout_bars(exit_open=110)

    trades = backtest_strategy_1001plus_v2_exit(
        bars,
        _params(
            atr_stop_k=10.0,
            atr_take_profit_k=20.0,
            time_stop_bars=1,
            trailing_start_atr=10.0,
        ),
    )

    assert len(trades) == 1
    assert trades[0].exit_time == _dt("2026-01-02 08:50")
    assert trades[0].exit_price == 110


def test_v2_exit_partial_take_profit_uses_tighter_stop() -> None:
    bars = _long_breakout_bars(exit_open=109)
    bars.append(_bar("2026-01-02 08:51", 112, 140, 120, 121))

    trades = backtest_strategy_1001plus_v2_exit(
        bars,
        _params(
            atr_stop_k=10.0,
            atr_take_profit_k=2.0,
            trailing_start_atr=20.0,
            tp_tighten_factor=0.3,
        ),
    )

    assert len(trades) == 1
    assert trades[0].exit_time == _dt("2026-01-02 08:51")
    assert trades[0].exit_price > trades[0].entry_price


def test_v2_exit_single_bar_single_action_on_force_exit() -> None:
    bars = _long_breakout_bars(exit_open=110)[:-1]
    bars.extend(
        [
            _bar("2026-01-02 13:11", 110, 118, 109, 117),
            _bar("2026-01-02 13:12", 111, 112, 110, 111),
        ]
    )

    trades = backtest_strategy_1001plus_v2_exit(
        bars,
        _params(
            atr_stop_k=10.0,
            atr_take_profit_k=20.0,
            trailing_start_atr=20.0,
        ),
    )

    assert len(trades) == 1
    assert trades[0].exit_time == _dt("2026-01-02 13:12")
    assert trades[0].entry_time != trades[0].exit_time


def _params(**overrides) -> Strategy1001PlusV2ExitParams:
    values = {
        "strategy_name": "1001plus_v2_exit_test",
        "ema_short_len": 2,
        "ema_long_len": 3,
        "rsi_len": 2,
        "atr_len": 2,
        "donchian_len": 3,
        "rsi_long_threshold": 50.0,
        "rsi_short_threshold": 50.0,
        "rsi_long_exit": 0.0,
        "rsi_short_exit": 100.0,
        "atr_stop_k": 1.0,
        "atr_take_profit_k": 1.0,
        "max_hold_bars": 60,
        "cooldown_bars": 0,
        "begin_time": "0845",
        "end_time": "1240",
        "force_exit_time": "1312",
        "volatility_exit_atr_ratio": 0.01,
    }
    values.update(overrides)
    return Strategy1001PlusV2ExitParams(**values)


def _long_breakout_bars(exit_open: float) -> list[BarRecord]:
    return [
        _bar("2026-01-02 08:45", 100, 101, 99, 100),
        _bar("2026-01-02 08:46", 100, 102, 99, 101),
        _bar("2026-01-02 08:47", 101, 103, 100, 102),
        _bar("2026-01-02 08:48", 102, 110, 101, 109),
        _bar("2026-01-02 08:49", 109, 109, 109, 109),
        _bar("2026-01-02 08:50", exit_open, exit_open, exit_open, exit_open),
    ]


def _assert_entry_prices_are_bar_opens(trades, bars: list[BarRecord]) -> None:
    opens_by_time = {bar.ts: bar.open for bar in bars}
    for trade in trades:
        assert trade.entry_price == opens_by_time[trade.entry_time]


def _bar(ts: str, open_: float, high: float, low: float, close: float) -> BarRecord:
    return BarRecord(
        ts=_dt(ts),
        open=float(open_),
        high=float(high),
        low=float(low),
        close=float(close),
        volume=100,
    )


def _dt(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M")
