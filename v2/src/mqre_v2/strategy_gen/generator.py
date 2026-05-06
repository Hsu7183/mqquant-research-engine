from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from mqre_v2.strategy_gen.templates import STRATEGY_FAMILIES, family_param_space


@dataclass(frozen=True, slots=True)
class GeneratedStrategyConfig:
    strategy_id: str
    family: str
    direction: str
    params: dict[str, Any]


def generate_intraday_futures_strategies(
    n: int,
    seed: int | None = None,
    families: list[str] | None = None,
) -> list[GeneratedStrategyConfig]:
    if n <= 0:
        raise ValueError("n must be > 0")

    selected_families = families or STRATEGY_FAMILIES
    if not selected_families:
        raise ValueError("families cannot be empty")
    unknown = sorted(set(selected_families) - set(STRATEGY_FAMILIES))
    if unknown:
        raise ValueError(f"unknown strategy families: {unknown}")

    rng = random.Random(seed)
    configs: list[GeneratedStrategyConfig] = []

    family_sequence = _family_sequence(n, selected_families, rng)
    for index, family in enumerate(family_sequence, start=1):
        params = _sample_params(family, rng)
        direction = str(params["direction"])
        strategy_id = f"{family}_{index:04d}"
        configs.append(
            GeneratedStrategyConfig(
                strategy_id=strategy_id,
                family=family,
                direction=direction,
                params=params,
            )
        )

    return configs


def _family_sequence(n: int, families: list[str], rng: random.Random) -> list[str]:
    sequence = list(families[:n])
    while len(sequence) < n:
        sequence.append(rng.choice(families))
    rng.shuffle(sequence)
    return sequence


def _sample_params(family: str, rng: random.Random) -> dict[str, Any]:
    space = family_param_space(family)
    params = {name: rng.choice(values) for name, values in space.items()}

    fixed_tp = float(params.get("fixed_tp", 60.0))
    fixed_sl = float(params.get("fixed_sl", 40.0))
    if fixed_sl > fixed_tp * 5:
        fixed_sl = fixed_tp * 2
    params["fixed_tp"] = fixed_tp
    params["fixed_sl"] = fixed_sl

    params.setdefault("atr_len", rng.choice([5, 10, 14, 20, 30]))
    params.setdefault("atr_tp_k", rng.choice([1.5, 2.0, 3.0, 5.0, 8.0, 10.0]))
    params.setdefault("atr_sl_k", rng.choice([1.0, 1.5, 2.0, 3.0, 5.0, 8.0]))
    params.setdefault("profit_protect_trigger", rng.choice([20, 40, 60, 90, 120]))
    params.setdefault("giveback", rng.choice([5, 10, 20, 40, 60]))
    params.setdefault("don_len", rng.choice([20, 40, 60, 90, 120, 180]))
    params.setdefault("bb_len", rng.choice([10, 20, 40, 60]))
    params.setdefault("bb_k", rng.choice([1.5, 2.0, 2.5, 3.0]))
    params.setdefault("min_break", rng.choice([0, 2, 5, 8]))
    params.setdefault("break_limit", rng.choice([10, 20, 40, 60, 80]))
    params.setdefault("ema_fast", rng.choice([2, 4, 6, 8]))
    params.setdefault("ema_mid", rng.choice([5, 10, 15, 20]))
    params.setdefault("ema_slow", rng.choice([20, 40, 60, 80]))
    params.setdefault("vwap_buffer", rng.choice([0, 10, 20, 40]))
    params.setdefault("vwap_slope_filter", rng.choice([True, False]))
    params.setdefault("vol_len", rng.choice([10, 20, 40, 60]))
    params.setdefault("vol_k", rng.choice([1.2, 1.5, 2.0, 3.0]))
    params.setdefault("or_start", "0845")
    params.setdefault("or_end", rng.choice(["0900", "0915", "0930"]))
    params.setdefault("or_buffer", rng.choice([0, 5, 10, 15]))
    params.setdefault("momentum_bars", rng.choice([2, 3, 4]))
    return params


__all__ = ["GeneratedStrategyConfig", "generate_intraday_futures_strategies"]
