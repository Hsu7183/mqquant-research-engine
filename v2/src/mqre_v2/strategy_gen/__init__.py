"""Intraday futures strategy generation helpers."""

from mqre_v2.strategy_gen.generator import (
    GeneratedStrategyConfig,
    generate_intraday_futures_strategies,
)
from mqre_v2.strategy_gen.regime import RegimeType, detect_intraday_regime
from mqre_v2.strategy_gen.templates import STRATEGY_FAMILIES

__all__ = [
    "GeneratedStrategyConfig",
    "RegimeType",
    "STRATEGY_FAMILIES",
    "detect_intraday_regime",
    "generate_intraday_futures_strategies",
]
