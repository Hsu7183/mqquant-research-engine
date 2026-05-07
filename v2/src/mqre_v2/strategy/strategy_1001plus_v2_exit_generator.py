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


TRAILING_START_MIN = 1.5
TRAILING_START_MAX = 3.0
TRAILING_GIVEBACK_MIN = 0.3
TRAILING_GIVEBACK_MAX = 0.7
TIME_STOP_MIN = 20
TIME_STOP_MAX = 100
TP_TIGHTEN_FACTOR_MIN = 0.3
TP_TIGHTEN_FACTOR_MAX = 0.7
DEFAULT_V2_EXIT_GENERATOR_SEED = 2002


def generate_1001plus_v2_exit_strategies(
    n: int = 300,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    if n <= 0:
        raise ValueError("n must be > 0")

    rng = random.Random(seed)
    strategies: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    max_attempts = n * 200
    attempts = 0

    while len(strategies) < n:
        attempts += 1
        if attempts > max_attempts:
            raise ValueError("unable to generate enough unique 1001plus v2 exit strategies")

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
    return {
        "ema_short_len": ema_short,
        "ema_long_len": ema_long,
        "rsi_long_threshold": rng.randint(RISK_RSI_LONG_MIN, RISK_RSI_LONG_MAX),
        "rsi_short_threshold": rng.randint(RISK_RSI_SHORT_MIN, RISK_RSI_SHORT_MAX),
        "atr_stop_k": atr_stop,
        "atr_take_profit_k": atr_take_profit,
        "donchian_len": rng.randint(RISK_DONCHIAN_MIN, RISK_DONCHIAN_MAX),
        "use_vwap_filter": rng.random() < RISK_VWAP_TRUE_PROBABILITY,
        "trailing_start_atr": _random_tenth(
            rng,
            TRAILING_START_MIN,
            TRAILING_START_MAX,
        ),
        "trailing_giveback": _random_tenth(
            rng,
            TRAILING_GIVEBACK_MIN,
            TRAILING_GIVEBACK_MAX,
        ),
        "time_stop_bars": rng.randint(TIME_STOP_MIN, TIME_STOP_MAX),
        "tp_tighten_factor": _random_tenth(
            rng,
            TP_TIGHTEN_FACTOR_MIN,
            TP_TIGHTEN_FACTOR_MAX,
        ),
    }


def _strategy_name(params: dict[str, Any]) -> str:
    return (
        "1001plus_v2exit_"
        f"ES{params['ema_short_len']}_"
        f"EL{params['ema_long_len']}_"
        f"RL{params['rsi_long_threshold']}_"
        f"RS{params['rsi_short_threshold']}_"
        f"AS{_token(params['atr_stop_k'])}_"
        f"AT{_token(params['atr_take_profit_k'])}_"
        f"D{params['donchian_len']}_"
        f"VW{1 if params['use_vwap_filter'] else 0}_"
        f"TR{_token(params['trailing_start_atr'])}_"
        f"GB{_token(params['trailing_giveback'])}_"
        f"TM{params['time_stop_bars']}_"
        f"TF{_token(params['tp_tighten_factor'])}"
    )


def _random_tenth(rng: random.Random, start: float, end: float) -> float:
    start_tick = int(round(start * 10))
    end_tick = int(round(end * 10))
    return rng.randint(start_tick, end_tick) / 10.0


def _token(value: float) -> str:
    text = f"{value:.1f}".rstrip("0").rstrip(".")
    return text.replace(".", "p")


__all__ = [
    "DEFAULT_V2_EXIT_GENERATOR_SEED",
    "TIME_STOP_MAX",
    "TIME_STOP_MIN",
    "TP_TIGHTEN_FACTOR_MAX",
    "TP_TIGHTEN_FACTOR_MIN",
    "TRAILING_GIVEBACK_MAX",
    "TRAILING_GIVEBACK_MIN",
    "TRAILING_START_MAX",
    "TRAILING_START_MIN",
    "generate_1001plus_v2_exit_strategies",
]
