from __future__ import annotations

from datetime import datetime

from mqre_v2.core.bars import BarRecord
from mqre_v2.strategy.strategy_1001plus_regime_filter import (
    Strategy1001PlusRegimeFilterParams,
    backtest_strategy_1001plus_regime_filter,
)


def test_regime_filter_enters_and_exits_at_current_open_when_filters_disabled() -> None:
    bars = _long_breakout_bars(exit_open=115)

    trades = backtest_strategy_1001plus_regime_filter(bars, _params())

    assert len(trades) == 1
    assert trades[0].entry_time == _dt("2026-01-02 08:49")
    assert trades[0].entry_price == 109
    assert trades[0].exit_time == _dt("2026-01-02 08:50")
    assert trades[0].exit_price == 115
    _assert_trade_prices_are_bar_opens(trades, bars)


def test_regime_filter_blocks_entry_when_trend_slope_is_too_small() -> None:
    bars = _long_breakout_bars(exit_open=115)

    unfiltered = backtest_strategy_1001plus_regime_filter(bars, _params())
    filtered = backtest_strategy_1001plus_regime_filter(
        bars,
        _params(
            enable_regime_trend_filter=True,
            regime_ema_slope_threshold=999.0,
        ),
    )

    assert len(unfiltered) == 1
    assert filtered == []


def test_regime_filter_does_not_use_current_close_for_entry() -> None:
    bars = [
        _bar("2026-01-02 08:45", 100, 101, 99, 100),
        _bar("2026-01-02 08:46", 100, 102, 99, 101),
        _bar("2026-01-02 08:47", 101, 103, 100, 102),
        _bar("2026-01-02 08:48", 102, 103, 101, 102),
        _bar("2026-01-02 08:49", 105, 250, 50, 250),
        _bar("2026-01-02 08:50", 250, 252, 248, 251),
        _bar("2026-01-02 08:51", 500, 500, 500, 500),
    ]

    trades = backtest_strategy_1001plus_regime_filter(bars, _params())

    assert trades
    assert trades[0].entry_time != _dt("2026-01-02 08:49")
    assert trades[0].entry_time == _dt("2026-01-02 08:50")
    assert trades[0].entry_price == 250


def test_regime_filter_volatility_filter_can_block_high_atr_environment() -> None:
    bars = _long_breakout_bars(exit_open=115)

    trades = backtest_strategy_1001plus_regime_filter(
        bars,
        _params(
            enable_regime_volatility_filter=True,
            regime_atr_threshold_k=0.01,
        ),
    )

    assert trades == []


def _params(**overrides) -> Strategy1001PlusRegimeFilterParams:
    values = {
        "strategy_name": "1001plus_regime_filter_test",
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
        "enable_regime_volatility_filter": False,
        "enable_regime_trend_filter": False,
        "enable_regime_vwap_distance_filter": False,
    }
    values.update(overrides)
    return Strategy1001PlusRegimeFilterParams(**values)


def _long_breakout_bars(exit_open: float) -> list[BarRecord]:
    return [
        _bar("2026-01-02 08:45", 100, 101, 99, 100),
        _bar("2026-01-02 08:46", 100, 102, 99, 101),
        _bar("2026-01-02 08:47", 101, 103, 100, 102),
        _bar("2026-01-02 08:48", 102, 110, 101, 109),
        _bar("2026-01-02 08:49", 109, 250, 50, 80),
        _bar("2026-01-02 08:50", exit_open, exit_open, exit_open, exit_open),
    ]


def _assert_trade_prices_are_bar_opens(trades, bars: list[BarRecord]) -> None:
    opens_by_time = {bar.ts: bar.open for bar in bars}
    for trade in trades:
        assert trade.entry_price == opens_by_time[trade.entry_time]
        assert trade.exit_price == opens_by_time[trade.exit_time]


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
