from __future__ import annotations

from datetime import datetime, timedelta

from mqre_v2.backtest.generated_strategy import backtest_generated_intraday_strategy
from mqre_v2.core.bars import BarRecord
from mqre_v2.strategy_gen.generator import GeneratedStrategyConfig
from mqre_v2.strategy_gen.templates import STRATEGY_FAMILIES


def test_each_family_can_run_backtest() -> None:
    bars = _bars()

    for index, family in enumerate(STRATEGY_FAMILIES, start=1):
        config = _config(family, index, direction="both")
        trades = backtest_generated_intraday_strategy(bars, config)
        assert isinstance(trades, list)


def test_entry_uses_previous_data_and_current_open() -> None:
    bars = [
        _bar("2026-01-02 08:48", 100, 100, 100, 100),
        _bar("2026-01-02 08:49", 100, 120, 100, 120),
        _bar("2026-01-02 08:50", 125, 140, 125, 140),
        _bar("2026-01-02 08:51", 150, 150, 150, 150),
    ]
    config = _config("trend_breakout", 1, direction="long")

    trades = backtest_generated_intraday_strategy(bars, config)

    assert trades
    assert trades[0].entry_time == datetime(2026, 1, 2, 8, 50)
    assert trades[0].entry_price == 125


def test_strategy_does_not_hold_overnight() -> None:
    bars = [
        _bar("2026-01-02 08:48", 100, 110, 100, 110),
        _bar("2026-01-02 08:49", 120, 120, 120, 120),
        _bar("2026-01-03 08:45", 125, 125, 125, 125),
    ]
    config = _config("trend_breakout", 1, direction="long", fixed_tp=999, fixed_sl=999)

    trades = backtest_generated_intraday_strategy(bars, config)

    assert trades[0].exit_time.date() == datetime(2026, 1, 3).date()
    assert trades[0].exit_time.time().strftime("%H%M") == "0845"


def test_force_exit_time_is_applied() -> None:
    bars = [
        _bar("2026-01-02 12:39", 100, 110, 100, 110),
        _bar("2026-01-02 12:40", 120, 120, 120, 120),
        _bar("2026-01-02 13:12", 125, 125, 125, 125),
    ]
    config = _config("trend_breakout", 1, direction="long", fixed_tp=999, fixed_sl=999)

    trades = backtest_generated_intraday_strategy(bars, config)

    assert trades[0].exit_time == datetime(2026, 1, 2, 13, 12)


def _config(
    family: str,
    index: int,
    direction: str,
    fixed_tp: float = 20.0,
    fixed_sl: float = 20.0,
) -> GeneratedStrategyConfig:
    return GeneratedStrategyConfig(
        strategy_id=f"{family}_{index:04d}",
        family=family,
        direction=direction,
        params={
            "begin_time": "0848",
            "end_time": "1255",
            "force_exit_time": "1312",
            "max_hold_bars": 30,
            "cooldown_bars": 0,
            "direction": direction,
            "don_len": 2,
            "bb_len": 2,
            "bb_k": 1.5,
            "min_break": 0,
            "break_limit": 100,
            "ema_fast": 2,
            "ema_mid": 3,
            "ema_slow": 4,
            "vwap_buffer": 0,
            "vol_len": 2,
            "vol_k": 1.0,
            "or_start": "0845",
            "or_end": "0849",
            "or_buffer": 0,
            "momentum_bars": 2,
            "range_filter": 1,
            "fixed_tp": fixed_tp,
            "fixed_sl": fixed_sl,
        },
    )


def _bars() -> list[BarRecord]:
    ts = datetime(2026, 1, 2, 8, 45)
    bars = []
    for index in range(120):
        open_price = 100 + index
        close_price = open_price + (2 if index % 4 else -1)
        bars.append(
            BarRecord(
                ts=ts + timedelta(minutes=index),
                open=open_price,
                high=max(open_price, close_price) + 3,
                low=min(open_price, close_price) - 3,
                close=close_price,
                volume=100 + index,
            )
        )
    return bars


def _bar(ts: str, open_price: float, high: float, low: float, close: float) -> BarRecord:
    return BarRecord(
        ts=datetime.strptime(ts, "%Y-%m-%d %H:%M"),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=100,
    )
