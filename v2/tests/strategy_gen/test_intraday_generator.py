from __future__ import annotations

from collections import Counter

from mqre_v2.strategy_gen.generator import generate_intraday_futures_strategies
from mqre_v2.strategy_gen.templates import STRATEGY_FAMILIES


def test_generate_300_strategies() -> None:
    configs = generate_intraday_futures_strategies(n=300, seed=42)

    assert len(configs) == 300
    assert all(config.params for config in configs)


def test_seed_is_reproducible() -> None:
    first = generate_intraday_futures_strategies(n=20, seed=7)
    second = generate_intraday_futures_strategies(n=20, seed=7)

    assert first == second


def test_strategy_ids_are_unique() -> None:
    configs = generate_intraday_futures_strategies(n=300, seed=42)
    ids = [config.strategy_id for config in configs]

    assert len(ids) == len(set(ids))


def test_each_family_can_be_generated() -> None:
    configs = generate_intraday_futures_strategies(
        n=len(STRATEGY_FAMILIES),
        seed=1,
        families=STRATEGY_FAMILIES,
    )
    counts = Counter(config.family for config in configs)

    assert set(counts) == set(STRATEGY_FAMILIES)
    assert all(count >= 1 for count in counts.values())


def test_rejects_unreasonable_stop_loss_ratio() -> None:
    configs = generate_intraday_futures_strategies(n=100, seed=3)

    for config in configs:
        assert config.params["fixed_sl"] <= config.params["fixed_tp"] * 5
