from __future__ import annotations

import random
from typing import Any


EMA_SHORT_MIN = 2
EMA_SHORT_MAX = 10
EMA_LONG_MIN = 10
EMA_LONG_MAX = 50
RSI_LONG_MIN = 55
RSI_LONG_MAX = 70
RSI_SHORT_MIN = 30
RSI_SHORT_MAX = 45
ATR_STOP_MIN = 1.0
ATR_STOP_MAX = 3.0
ATR_TAKE_PROFIT_MIN = 1.5
ATR_TAKE_PROFIT_MAX = 5.0
DONCHIAN_MIN = 10
DONCHIAN_MAX = 50
DEFAULT_GENERATOR_SEED = 1001


def generate_1001plus_strategies(
    n: int = 300,
    seed: int | None = DEFAULT_GENERATOR_SEED,
) -> list[dict[str, Any]]:
    if n <= 0:
        raise ValueError("n must be > 0")

    rng = random.Random(seed)
    strategies: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    max_attempts = n * 100
    attempts = 0

    while len(strategies) < n:
        attempts += 1
        if attempts > max_attempts:
            raise ValueError("unable to generate enough unique 1001plus strategies")

        params = _random_params(rng)
        strategy_name = _strategy_name(params)
        if strategy_name in seen_names:
            continue

        seen_names.add(strategy_name)
        strategies.append(
            {
                "strategy_name": strategy_name,
                "params": params,
            }
        )

    return strategies


def _random_params(rng: random.Random) -> dict[str, Any]:
    ema_short = rng.randint(EMA_SHORT_MIN, EMA_SHORT_MAX)
    ema_long = rng.randint(max(EMA_LONG_MIN, ema_short + 1), EMA_LONG_MAX)
    atr_stop = _random_tenth(rng, ATR_STOP_MIN, ATR_STOP_MAX)
    atr_take_profit = _random_tenth(
        rng,
        max(ATR_TAKE_PROFIT_MIN, atr_stop),
        ATR_TAKE_PROFIT_MAX,
    )
    return {
        "ema_short_len": ema_short,
        "ema_long_len": ema_long,
        "rsi_long_threshold": rng.randint(RSI_LONG_MIN, RSI_LONG_MAX),
        "rsi_short_threshold": rng.randint(RSI_SHORT_MIN, RSI_SHORT_MAX),
        "atr_stop_k": atr_stop,
        "atr_take_profit_k": atr_take_profit,
        "donchian_len": rng.randint(DONCHIAN_MIN, DONCHIAN_MAX),
        "use_vwap_filter": rng.choice([True, False]),
    }


def _random_tenth(rng: random.Random, start: float, end: float) -> float:
    start_tick = int(round(start * 10))
    end_tick = int(round(end * 10))
    return rng.randint(start_tick, end_tick) / 10.0


def _strategy_name(params: dict[str, Any]) -> str:
    return (
        "1001plus_"
        f"ES{params['ema_short_len']}_"
        f"EL{params['ema_long_len']}_"
        f"RL{params['rsi_long_threshold']}_"
        f"RS{params['rsi_short_threshold']}_"
        f"AS{_token(params['atr_stop_k'])}_"
        f"AT{_token(params['atr_take_profit_k'])}_"
        f"D{params['donchian_len']}_"
        f"VW{1 if params['use_vwap_filter'] else 0}"
    )


def _token(value: float) -> str:
    text = f"{value:.1f}".rstrip("0").rstrip(".")
    return text.replace(".", "p")


__all__ = [
    "ATR_STOP_MAX",
    "ATR_STOP_MIN",
    "ATR_TAKE_PROFIT_MAX",
    "ATR_TAKE_PROFIT_MIN",
    "DONCHIAN_MAX",
    "DONCHIAN_MIN",
    "EMA_LONG_MAX",
    "EMA_LONG_MIN",
    "EMA_SHORT_MAX",
    "EMA_SHORT_MIN",
    "RSI_LONG_MAX",
    "RSI_LONG_MIN",
    "RSI_SHORT_MAX",
    "RSI_SHORT_MIN",
    "generate_1001plus_strategies",
]
