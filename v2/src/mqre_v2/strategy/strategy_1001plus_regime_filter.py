from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from statistics import mean
from typing import Any

from mqre_v2.core.bars import BarRecord
from mqre_v2.core.trades import TradeRecord
from mqre_v2.strategy.strategy_1001plus import (
    Strategy1001PlusParams,
    _IndicatorState,
    _OpenPosition,
    _close_position,
    _entry_direction,
    _maybe_exit_position,
    _parse_hhmm,
    _validate_params,
)


@dataclass(frozen=True, slots=True)
class Strategy1001PlusRegimeFilterParams(Strategy1001PlusParams):
    strategy_name: str = "1001plus_regime_filter"
    regime_atr_ma_len: int = 20
    regime_atr_threshold_k: float = 1.5
    regime_ema_slope_threshold: float = 0.5
    regime_vwap_distance_threshold: float = 5.0
    enable_regime_volatility_filter: bool = True
    enable_regime_trend_filter: bool = True
    enable_regime_vwap_distance_filter: bool = False


class _RegimeIndicatorState(_IndicatorState):
    def __init__(self, params: Strategy1001PlusRegimeFilterParams) -> None:
        super().__init__(params)
        self.regime_params = params
        self.prev_ema_long: float | None = None
        self.atr_values: deque[float] = deque(maxlen=params.regime_atr_ma_len)

    def snapshot(self) -> dict[str, Any]:
        snapshot = super().snapshot()
        snapshot["prev_ema_long"] = self.prev_ema_long
        snapshot["atr_ma"] = mean(self.atr_values) if self.atr_values else None
        return snapshot

    def update_with_completed_bar(self, bar: BarRecord) -> None:
        previous_ema_long = self.ema_long
        super().update_with_completed_bar(bar)
        self.prev_ema_long = previous_ema_long
        if self.atr is not None:
            self.atr_values.append(float(self.atr))


def backtest_strategy_1001plus_regime_filter(
    bars: list[BarRecord],
    params: Strategy1001PlusRegimeFilterParams | None = None,
) -> list[TradeRecord]:
    effective = params or Strategy1001PlusRegimeFilterParams()
    _validate_regime_filter_params(effective)
    if len(bars) < 2:
        return []

    begin_time = _parse_hhmm(effective.begin_time, "begin_time")
    end_time = _parse_hhmm(effective.end_time, "end_time")
    force_exit_time = _parse_hhmm(effective.force_exit_time, "force_exit_time")
    ordered_bars = bars if bars[0].ts <= bars[-1].ts else sorted(bars, key=lambda item: item.ts)

    indicators = _RegimeIndicatorState(effective)
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
            if (
                direction != 0
                and entry_atr is not None
                and entry_atr > 0
                and _regime_filter_pass(snapshot, effective)
            ):
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


def _regime_filter_pass(
    snapshot: dict[str, Any],
    params: Strategy1001PlusRegimeFilterParams,
) -> bool:
    if params.enable_regime_volatility_filter:
        atr = snapshot.get("atr")
        atr_ma = snapshot.get("atr_ma")
        if atr is None or atr_ma is None or float(atr_ma) <= 0:
            return False
        if float(atr) > params.regime_atr_threshold_k * float(atr_ma):
            return False

    if params.enable_regime_trend_filter:
        ema_long = snapshot.get("ema_long")
        prev_ema_long = snapshot.get("prev_ema_long")
        if ema_long is None or prev_ema_long is None:
            return False
        if abs(float(ema_long) - float(prev_ema_long)) <= params.regime_ema_slope_threshold:
            return False

    if params.enable_regime_vwap_distance_filter:
        prev_close = snapshot.get("prev_close")
        vwap = snapshot.get("vwap")
        if prev_close is None or vwap is None:
            return False
        if abs(float(prev_close) - float(vwap)) <= params.regime_vwap_distance_threshold:
            return False

    return True


def _validate_regime_filter_params(params: Strategy1001PlusRegimeFilterParams) -> None:
    _validate_params(params)
    if params.regime_atr_ma_len <= 0:
        raise ValueError("regime_atr_ma_len must be > 0")
    if params.regime_atr_threshold_k <= 0:
        raise ValueError("regime_atr_threshold_k must be > 0")
    if params.regime_ema_slope_threshold < 0:
        raise ValueError("regime_ema_slope_threshold must be >= 0")
    if params.regime_vwap_distance_threshold < 0:
        raise ValueError("regime_vwap_distance_threshold must be >= 0")


__all__ = [
    "Strategy1001PlusRegimeFilterParams",
    "backtest_strategy_1001plus_regime_filter",
]
