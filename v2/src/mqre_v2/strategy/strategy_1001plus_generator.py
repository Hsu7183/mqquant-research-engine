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
RISK_EMA_SHORT_MIN = 4
RISK_EMA_SHORT_MAX = 10
RISK_EMA_LONG_MIN = 20
RISK_EMA_LONG_MAX = 50
RISK_RSI_LONG_MIN = 62
RISK_RSI_LONG_MAX = 70
RISK_RSI_SHORT_MIN = 30
RISK_RSI_SHORT_MAX = 38
RISK_ATR_STOP_MIN = 1.0
RISK_ATR_STOP_MAX = 1.8
RISK_ATR_TAKE_PROFIT_MIN = 2.0
RISK_ATR_TAKE_PROFIT_MAX = 4.0
RISK_DONCHIAN_MIN = 25
RISK_DONCHIAN_MAX = 50
RISK_VWAP_TRUE_PROBABILITY = 0.8


def generate_1001plus_strategies(
    n: int = 300,
    seed: int | None = None,
    mode: str = "default",
) -> list[dict[str, Any]]:
    if n <= 0:
        raise ValueError("n must be > 0")
    if mode not in {"default", "risk_constrained"}:
        raise ValueError("mode must be 'default' or 'risk_constrained'")

    rng = random.Random(seed)
    strategies: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    max_attempts = n * 100
    attempts = 0

    while len(strategies) < n:
        attempts += 1
        if attempts > max_attempts:
            raise ValueError("unable to generate enough unique 1001plus strategies")

        params = _random_params(rng, mode)
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


def _random_params(rng: random.Random, mode: str) -> dict[str, Any]:
    ranges = _ranges_for_mode(mode)
    ema_short = rng.randint(ranges["ema_short_min"], ranges["ema_short_max"])
    ema_long = rng.randint(
        max(ranges["ema_long_min"], ema_short + 1),
        ranges["ema_long_max"],
    )
    atr_stop = _random_tenth(
        rng,
        ranges["atr_stop_min"],
        ranges["atr_stop_max"],
    )
    atr_take_profit = _random_tenth(
        rng,
        max(ranges["atr_take_profit_min"], atr_stop),
        ranges["atr_take_profit_max"],
    )
    return {
        "ema_short_len": ema_short,
        "ema_long_len": ema_long,
        "rsi_long_threshold": rng.randint(
            ranges["rsi_long_min"],
            ranges["rsi_long_max"],
        ),
        "rsi_short_threshold": rng.randint(
            ranges["rsi_short_min"],
            ranges["rsi_short_max"],
        ),
        "atr_stop_k": atr_stop,
        "atr_take_profit_k": atr_take_profit,
        "donchian_len": rng.randint(ranges["donchian_min"], ranges["donchian_max"]),
        "use_vwap_filter": _random_vwap_filter(rng, mode),
    }


def _ranges_for_mode(mode: str) -> dict[str, int | float]:
    if mode == "risk_constrained":
        return {
            "ema_short_min": RISK_EMA_SHORT_MIN,
            "ema_short_max": RISK_EMA_SHORT_MAX,
            "ema_long_min": RISK_EMA_LONG_MIN,
            "ema_long_max": RISK_EMA_LONG_MAX,
            "rsi_long_min": RISK_RSI_LONG_MIN,
            "rsi_long_max": RISK_RSI_LONG_MAX,
            "rsi_short_min": RISK_RSI_SHORT_MIN,
            "rsi_short_max": RISK_RSI_SHORT_MAX,
            "atr_stop_min": RISK_ATR_STOP_MIN,
            "atr_stop_max": RISK_ATR_STOP_MAX,
            "atr_take_profit_min": RISK_ATR_TAKE_PROFIT_MIN,
            "atr_take_profit_max": RISK_ATR_TAKE_PROFIT_MAX,
            "donchian_min": RISK_DONCHIAN_MIN,
            "donchian_max": RISK_DONCHIAN_MAX,
        }
    return {
        "ema_short_min": EMA_SHORT_MIN,
        "ema_short_max": EMA_SHORT_MAX,
        "ema_long_min": EMA_LONG_MIN,
        "ema_long_max": EMA_LONG_MAX,
        "rsi_long_min": RSI_LONG_MIN,
        "rsi_long_max": RSI_LONG_MAX,
        "rsi_short_min": RSI_SHORT_MIN,
        "rsi_short_max": RSI_SHORT_MAX,
        "atr_stop_min": ATR_STOP_MIN,
        "atr_stop_max": ATR_STOP_MAX,
        "atr_take_profit_min": ATR_TAKE_PROFIT_MIN,
        "atr_take_profit_max": ATR_TAKE_PROFIT_MAX,
        "donchian_min": DONCHIAN_MIN,
        "donchian_max": DONCHIAN_MAX,
    }


def _random_vwap_filter(rng: random.Random, mode: str) -> bool:
    if mode == "risk_constrained":
        return rng.random() < RISK_VWAP_TRUE_PROBABILITY
    return rng.choice([True, False])


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
    "RISK_ATR_STOP_MAX",
    "RISK_ATR_STOP_MIN",
    "RISK_ATR_TAKE_PROFIT_MAX",
    "RISK_ATR_TAKE_PROFIT_MIN",
    "RISK_DONCHIAN_MAX",
    "RISK_DONCHIAN_MIN",
    "RISK_EMA_LONG_MAX",
    "RISK_EMA_LONG_MIN",
    "RISK_EMA_SHORT_MAX",
    "RISK_EMA_SHORT_MIN",
    "RISK_RSI_LONG_MAX",
    "RISK_RSI_LONG_MIN",
    "RISK_RSI_SHORT_MAX",
    "RISK_RSI_SHORT_MIN",
    "RISK_VWAP_TRUE_PROBABILITY",
    "generate_1001plus_strategies",
]
