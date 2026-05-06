from __future__ import annotations

STRATEGY_FAMILIES = [
    "trend_breakout",
    "open_range_breakout",
    "vwap_pullback",
    "mean_reversion_range",
    "volume_breakout",
    "breakdown_momentum",
    "slow_grind_trend",
    "afternoon_trend_extension",
]

COMMON_PARAM_SPACE = {
    "begin_time": ["0848", "0900"],
    "end_time": ["1240", "1255"],
    "force_exit_time": ["1312"],
    "max_hold_bars": [10, 20, 30, 45, 60],
    "cooldown_bars": [0, 3, 5, 10],
    "direction": ["long", "short", "both"],
}

PARAM_SPACES = {
    "trend_breakout": {
        "don_len": [20, 40, 60, 90, 120, 180],
        "bb_len": [10, 20, 40, 60],
        "bb_k": [1.5, 2.0, 2.5, 3.0, 3.5],
        "min_break": [0, 2, 5, 8, 10],
        "break_limit": [10, 20, 40, 60, 80],
        "ema_fast": [2, 4, 6, 8],
        "ema_mid": [5, 10, 15, 20],
        "ema_slow": [20, 40, 60, 80],
        "fixed_tp": [40, 80, 120, 160, 200],
        "fixed_sl": [20, 40, 60, 80, 120],
    },
    "open_range_breakout": {
        "or_start": ["0845"],
        "or_end": ["0900", "0915", "0930"],
        "or_buffer": [0, 5, 10, 15, 20],
        "break_limit": [10, 20, 40, 60, 80],
        "fixed_tp": [40, 80, 120, 160],
        "fixed_sl": [20, 40, 60, 90],
    },
    "vwap_pullback": {
        "ema_fast": [2, 4, 6, 8],
        "ema_mid": [5, 10, 15, 20],
        "vwap_buffer": [0, 10, 20, 40, 80],
        "vwap_slope_filter": [True, False],
        "fixed_tp": [30, 60, 90, 120],
        "fixed_sl": [20, 40, 60, 90],
    },
    "mean_reversion_range": {
        "bb_len": [10, 20, 40, 60],
        "bb_k": [1.5, 2.0, 2.5, 3.0],
        "vwap_buffer": [10, 20, 40, 80],
        "range_filter": [40, 80, 120, 180],
        "fixed_tp": [20, 40, 60, 80],
        "fixed_sl": [20, 40, 60, 90],
    },
    "volume_breakout": {
        "don_len": [20, 40, 60, 90, 120],
        "vol_len": [10, 20, 40, 60],
        "vol_k": [1.2, 1.5, 2.0, 3.0, 5.0],
        "min_break": [0, 2, 5, 8],
        "break_limit": [10, 20, 40, 60, 80],
        "fixed_tp": [40, 80, 120, 160],
        "fixed_sl": [20, 40, 60, 90],
    },
    "breakdown_momentum": {
        "momentum_bars": [2, 3, 4, 5],
        "don_len": [10, 20, 40, 60],
        "min_break": [0, 2, 5, 8],
        "fixed_tp": [30, 60, 90, 120],
        "fixed_sl": [20, 40, 60, 90],
    },
    "slow_grind_trend": {
        "ema_fast": [2, 4, 6, 8],
        "ema_mid": [5, 10, 15, 20],
        "ema_slow": [20, 40, 60, 80],
        "vwap_buffer": [0, 10, 20, 40],
        "fixed_tp": [30, 60, 90, 120],
        "fixed_sl": [20, 40, 60, 90],
    },
    "afternoon_trend_extension": {
        "begin_time": ["1200", "1215"],
        "end_time": ["1255"],
        "ema_fast": [2, 4, 6, 8],
        "ema_mid": [5, 10, 15, 20],
        "don_len": [10, 20, 40, 60],
        "min_break": [0, 2, 5],
        "fixed_tp": [20, 40, 60, 90],
        "fixed_sl": [20, 40, 60],
    },
}


def family_param_space(family: str) -> dict:
    if family not in PARAM_SPACES:
        raise ValueError(f"unknown strategy family: {family}")
    params = dict(COMMON_PARAM_SPACE)
    params.update(PARAM_SPACES[family])
    return params


__all__ = ["COMMON_PARAM_SPACE", "PARAM_SPACES", "STRATEGY_FAMILIES", "family_param_space"]
