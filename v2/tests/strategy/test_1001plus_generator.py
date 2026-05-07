from __future__ import annotations

from mqre_v2.strategy.strategy_1001plus import Strategy1001PlusParams
from mqre_v2.strategy.strategy_1001plus_generator import (
    ATR_STOP_MAX,
    ATR_STOP_MIN,
    ATR_TAKE_PROFIT_MAX,
    ATR_TAKE_PROFIT_MIN,
    DONCHIAN_MAX,
    DONCHIAN_MIN,
    EMA_LONG_MAX,
    EMA_LONG_MIN,
    EMA_SHORT_MAX,
    EMA_SHORT_MIN,
    RSI_LONG_MAX,
    RSI_LONG_MIN,
    RSI_SHORT_MAX,
    RSI_SHORT_MIN,
    generate_1001plus_strategies,
)


def test_generate_1001plus_strategies_count() -> None:
    strategies = generate_1001plus_strategies(n=300, seed=42)

    assert len(strategies) == 300


def test_generate_1001plus_strategies_have_unique_names() -> None:
    strategies = generate_1001plus_strategies(n=500, seed=42)
    names = [item["strategy_name"] for item in strategies]

    assert len(names) == len(set(names))


def test_generate_1001plus_strategy_params_are_in_range() -> None:
    strategies = generate_1001plus_strategies(n=300, seed=42)

    for item in strategies:
        params = item["params"]
        assert EMA_SHORT_MIN <= params["ema_short_len"] <= EMA_SHORT_MAX
        assert EMA_LONG_MIN <= params["ema_long_len"] <= EMA_LONG_MAX
        assert params["ema_short_len"] < params["ema_long_len"]
        assert RSI_LONG_MIN <= params["rsi_long_threshold"] <= RSI_LONG_MAX
        assert RSI_SHORT_MIN <= params["rsi_short_threshold"] <= RSI_SHORT_MAX
        assert ATR_STOP_MIN <= params["atr_stop_k"] <= ATR_STOP_MAX
        assert ATR_TAKE_PROFIT_MIN <= params["atr_take_profit_k"] <= ATR_TAKE_PROFIT_MAX
        assert params["atr_stop_k"] <= params["atr_take_profit_k"]
        assert DONCHIAN_MIN <= params["donchian_len"] <= DONCHIAN_MAX
        assert isinstance(params["use_vwap_filter"], bool)
        Strategy1001PlusParams(strategy_name=item["strategy_name"], **params)


def test_generate_1001plus_strategies_can_generate_1000_unique() -> None:
    strategies = generate_1001plus_strategies(n=1000, seed=7)
    names = {item["strategy_name"] for item in strategies}

    assert len(names) == 1000
