from __future__ import annotations

import random
from typing import Any

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
    RISK_VWAP_TRUE_PROBABILITY,
)


REGIME_ATR_THRESHOLD_MIN = 1.2
REGIME_ATR_THRESHOLD_MAX = 2.0
REGIME_EMA_SLOPE_THRESHOLD_MIN = 0.1
REGIME_EMA_SLOPE_THRESHOLD_MAX = 2.0
REGIME_VWAP_DISTANCE_THRESHOLD_MIN = 0.0
REGIME_VWAP_DISTANCE_THRESHOLD_MAX = 30.0
REGIME_FILTER_TRUE_PROBABILITY = 0.8
DEFAULT_REGIME_FILTER_GENERATOR_SEED = 3003


def generate_1001plus_regime_filter_strategies(
    n: int = 300,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    if n <= 0:
        raise ValueError("n must be > 0")

    rng = random.Random(seed)
    strategies: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    max_attempts = n * 300
    attempts = 0

    while len(strategies) < n:
        attempts += 1
        if attempts > max_attempts:
            raise ValueError("unable to generate enough unique 1001plus regime filter strategies")

        params = _random_params(rng)
        strategy_name = _strategy_name(params)
        if strategy_name in seen_names:
            continue

        seen_names.add(strategy_name)
        strategies.append({"strategy_name": strategy_name, "params": params})

    return strategies


def _random_params(rng: random.Random) -> dict[str, Any]:
    ema_short = rng.randint(RISK_EMA_SHORT_MIN, RISK_EMA_SHORT_MAX)
    ema_long = rng.randint(max(RISK_EMA_LONG_MIN, ema_short + 1), RISK_EMA_LONG_MAX)
    atr_stop = _random_tenth(rng, RISK_ATR_STOP_MIN, RISK_ATR_STOP_MAX)
    atr_take_profit = _random_tenth(
        rng,
        max(RISK_ATR_TAKE_PROFIT_MIN, atr_stop),
        RISK_ATR_TAKE_PROFIT_MAX,
    )
    enable_volatility = rng.random() < REGIME_FILTER_TRUE_PROBABILITY
    enable_trend = rng.random() < REGIME_FILTER_TRUE_PROBABILITY
    enable_vwap_distance = rng.choice([True, False])
    if not (enable_volatility or enable_trend or enable_vwap_distance):
        enable_volatility = True

    return {
        "ema_short_len": ema_short,
        "ema_long_len": ema_long,
        "rsi_long_threshold": rng.randint(RISK_RSI_LONG_MIN, RISK_RSI_LONG_MAX),
        "rsi_short_threshold": rng.randint(RISK_RSI_SHORT_MIN, RISK_RSI_SHORT_MAX),
        "atr_stop_k": atr_stop,
        "atr_take_profit_k": atr_take_profit,
        "donchian_len": rng.randint(RISK_DONCHIAN_MIN, RISK_DONCHIAN_MAX),
        "use_vwap_filter": rng.random() < RISK_VWAP_TRUE_PROBABILITY,
        "regime_atr_threshold_k": _random_tenth(
            rng,
            REGIME_ATR_THRESHOLD_MIN,
            REGIME_ATR_THRESHOLD_MAX,
        ),
        "regime_ema_slope_threshold": _random_tenth(
            rng,
            REGIME_EMA_SLOPE_THRESHOLD_MIN,
            REGIME_EMA_SLOPE_THRESHOLD_MAX,
        ),
        "regime_vwap_distance_threshold": _random_tenth(
            rng,
            REGIME_VWAP_DISTANCE_THRESHOLD_MIN,
            REGIME_VWAP_DISTANCE_THRESHOLD_MAX,
        ),
        "enable_regime_volatility_filter": enable_volatility,
        "enable_regime_trend_filter": enable_trend,
        "enable_regime_vwap_distance_filter": enable_vwap_distance,
    }


def _strategy_name(params: dict[str, Any]) -> str:
    return (
        "1001plus_regime_"
        f"ES{params['ema_short_len']}_"
        f"EL{params['ema_long_len']}_"
        f"RL{params['rsi_long_threshold']}_"
        f"RS{params['rsi_short_threshold']}_"
        f"AS{_token(params['atr_stop_k'])}_"
        f"AT{_token(params['atr_take_profit_k'])}_"
        f"D{params['donchian_len']}_"
        f"VW{1 if params['use_vwap_filter'] else 0}_"
        f"RK{_token(params['regime_atr_threshold_k'])}_"
        f"SL{_token(params['regime_ema_slope_threshold'])}_"
        f"VD{_token(params['regime_vwap_distance_threshold'])}_"
        f"VF{1 if params['enable_regime_volatility_filter'] else 0}_"
        f"TF{1 if params['enable_regime_trend_filter'] else 0}_"
        f"DF{1 if params['enable_regime_vwap_distance_filter'] else 0}"
    )


def _random_tenth(rng: random.Random, start: float, end: float) -> float:
    start_tick = int(round(start * 10))
    end_tick = int(round(end * 10))
    return rng.randint(start_tick, end_tick) / 10.0


def _token(value: float) -> str:
    text = f"{value:.1f}".rstrip("0").rstrip(".")
    return text.replace(".", "p")


__all__ = [
    "DEFAULT_REGIME_FILTER_GENERATOR_SEED",
    "REGIME_ATR_THRESHOLD_MAX",
    "REGIME_ATR_THRESHOLD_MIN",
    "REGIME_EMA_SLOPE_THRESHOLD_MAX",
    "REGIME_EMA_SLOPE_THRESHOLD_MIN",
    "REGIME_FILTER_TRUE_PROBABILITY",
    "REGIME_VWAP_DISTANCE_THRESHOLD_MAX",
    "REGIME_VWAP_DISTANCE_THRESHOLD_MIN",
    "generate_1001plus_regime_filter_strategies",
]
