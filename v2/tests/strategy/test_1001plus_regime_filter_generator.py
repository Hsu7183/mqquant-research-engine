from __future__ import annotations

from mqre_v2.strategy.strategy_1001plus_regime_filter import (
    Strategy1001PlusRegimeFilterParams,
)
from mqre_v2.strategy.strategy_1001plus_regime_filter_generator import (
    REGIME_ATR_THRESHOLD_MAX,
    REGIME_ATR_THRESHOLD_MIN,
    REGIME_EMA_SLOPE_THRESHOLD_MAX,
    REGIME_EMA_SLOPE_THRESHOLD_MIN,
    REGIME_VWAP_DISTANCE_THRESHOLD_MAX,
    REGIME_VWAP_DISTANCE_THRESHOLD_MIN,
    generate_1001plus_regime_filter_strategies,
)
from mqre_v2.strategy.strategy_1001plus_generator import (
    RISK_ATR_STOP_MAX,
    RISK_ATR_STOP_MIN,
    RISK_ATR_TAKE_PROFIT_MAX,
    RISK_ATR_TAKE_PROFIT_MIN,
    RISK_DONCHIAN_MAX,
    RISK_DONCHIAN_MIN,
    RISK_EMA_LONG_MAX,
    RISK_EMA_LONG_MIN,
    RISK_EMA_SHORT_MAX,
    RISK_EMA_SHORT_MIN,
    RISK_RSI_LONG_MAX,
    RISK_RSI_LONG_MIN,
    RISK_RSI_SHORT_MAX,
    RISK_RSI_SHORT_MIN,
)


def test_generate_1001plus_regime_filter_count() -> None:
    strategies = generate_1001plus_regime_filter_strategies(n=300, seed=42)

    assert len(strategies) == 300


def test_generate_1001plus_regime_filter_names_are_unique() -> None:
    strategies = generate_1001plus_regime_filter_strategies(n=500, seed=42)
    names = [item["strategy_name"] for item in strategies]

    assert len(names) == len(set(names))


def test_generate_1001plus_regime_filter_params_are_in_range() -> None:
    strategies = generate_1001plus_regime_filter_strategies(n=300, seed=42)

    for item in strategies:
        params = item["params"]
        assert RISK_EMA_SHORT_MIN <= params["ema_short_len"] <= RISK_EMA_SHORT_MAX
        assert RISK_EMA_LONG_MIN <= params["ema_long_len"] <= RISK_EMA_LONG_MAX
        assert params["ema_short_len"] < params["ema_long_len"]
        assert RISK_RSI_LONG_MIN <= params["rsi_long_threshold"] <= RISK_RSI_LONG_MAX
        assert RISK_RSI_SHORT_MIN <= params["rsi_short_threshold"] <= RISK_RSI_SHORT_MAX
        assert RISK_ATR_STOP_MIN <= params["atr_stop_k"] <= RISK_ATR_STOP_MAX
        assert RISK_ATR_TAKE_PROFIT_MIN <= params["atr_take_profit_k"] <= RISK_ATR_TAKE_PROFIT_MAX
        assert params["atr_stop_k"] <= params["atr_take_profit_k"]
        assert RISK_DONCHIAN_MIN <= params["donchian_len"] <= RISK_DONCHIAN_MAX
        assert REGIME_ATR_THRESHOLD_MIN <= params["regime_atr_threshold_k"] <= REGIME_ATR_THRESHOLD_MAX
        assert (
            REGIME_EMA_SLOPE_THRESHOLD_MIN
            <= params["regime_ema_slope_threshold"]
            <= REGIME_EMA_SLOPE_THRESHOLD_MAX
        )
        assert (
            REGIME_VWAP_DISTANCE_THRESHOLD_MIN
            <= params["regime_vwap_distance_threshold"]
            <= REGIME_VWAP_DISTANCE_THRESHOLD_MAX
        )
        assert isinstance(params["enable_regime_volatility_filter"], bool)
        assert isinstance(params["enable_regime_trend_filter"], bool)
        assert isinstance(params["enable_regime_vwap_distance_filter"], bool)
        assert (
            params["enable_regime_volatility_filter"]
            or params["enable_regime_trend_filter"]
            or params["enable_regime_vwap_distance_filter"]
        )
        Strategy1001PlusRegimeFilterParams(strategy_name=item["strategy_name"], **params)


def test_generate_1001plus_regime_filter_is_reproducible() -> None:
    first = generate_1001plus_regime_filter_strategies(n=30, seed=42)
    second = generate_1001plus_regime_filter_strategies(n=30, seed=42)

    assert first == second
