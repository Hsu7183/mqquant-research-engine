from __future__ import annotations

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
from mqre_v2.strategy.strategy_1001plus_v2_exit import Strategy1001PlusV2ExitParams
from mqre_v2.strategy.strategy_1001plus_v2_exit_generator import (
    TIME_STOP_MAX,
    TIME_STOP_MIN,
    TP_TIGHTEN_FACTOR_MAX,
    TP_TIGHTEN_FACTOR_MIN,
    TRAILING_GIVEBACK_MAX,
    TRAILING_GIVEBACK_MIN,
    TRAILING_START_MAX,
    TRAILING_START_MIN,
    generate_1001plus_v2_exit_strategies,
)


def test_generate_1001plus_v2_exit_strategies_count() -> None:
    strategies = generate_1001plus_v2_exit_strategies(n=300, seed=42)

    assert len(strategies) == 300


def test_generate_1001plus_v2_exit_names_are_unique() -> None:
    strategies = generate_1001plus_v2_exit_strategies(n=500, seed=42)
    names = [item["strategy_name"] for item in strategies]

    assert len(names) == len(set(names))


def test_generate_1001plus_v2_exit_params_are_in_range() -> None:
    strategies = generate_1001plus_v2_exit_strategies(n=300, seed=42)

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
        assert isinstance(params["use_vwap_filter"], bool)
        assert TRAILING_START_MIN <= params["trailing_start_atr"] <= TRAILING_START_MAX
        assert TRAILING_GIVEBACK_MIN <= params["trailing_giveback"] <= TRAILING_GIVEBACK_MAX
        assert TIME_STOP_MIN <= params["time_stop_bars"] <= TIME_STOP_MAX
        assert TP_TIGHTEN_FACTOR_MIN <= params["tp_tighten_factor"] <= TP_TIGHTEN_FACTOR_MAX
        Strategy1001PlusV2ExitParams(strategy_name=item["strategy_name"], **params)


def test_generate_1001plus_v2_exit_varies_exit_combinations() -> None:
    strategies = generate_1001plus_v2_exit_strategies(n=100, seed=42)
    exit_combos = {
        (
            item["params"]["trailing_start_atr"],
            item["params"]["trailing_giveback"],
            item["params"]["time_stop_bars"],
            item["params"]["tp_tighten_factor"],
        )
        for item in strategies
    }

    assert len(exit_combos) > 1


def test_generate_1001plus_v2_exit_rejects_non_positive_count() -> None:
    try:
        generate_1001plus_v2_exit_strategies(n=0, seed=42)
    except ValueError as exc:
        assert "n" in str(exc)
    else:
        raise AssertionError("expected ValueError")
