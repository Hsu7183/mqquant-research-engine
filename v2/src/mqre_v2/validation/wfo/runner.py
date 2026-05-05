from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from mqre_v2.validation.wfo.gates import (
    WfoGateConfig,
    evaluate_wfo_round,
    evaluate_wfo_summary,
)
from mqre_v2.validation.wfo.results import (
    WfoRoundResult,
    WfoSummary,
    summarize_wfo_results,
)
from mqre_v2.validation.wfo.windows import WfoWindow, generate_wfo_windows


@dataclass(frozen=True)
class WfoRunResult:
    windows: list[WfoWindow]
    round_results: list[WfoRoundResult]
    summary: WfoSummary
    passed: bool
    fail_reason: str


def run_wfo(
    start_date: date,
    end_date: date,
    strategy_name: str,
    optimize_fn: Callable[[WfoWindow], Any],
    evaluate_fn: Callable[[WfoWindow, Any], WfoRoundResult],
    window_kwargs: dict | None = None,
    gate_config: WfoGateConfig | None = None,
) -> WfoRunResult:
    _ = strategy_name
    window_options = window_kwargs or {}
    config = gate_config or WfoGateConfig()

    windows = generate_wfo_windows(start_date, end_date, **window_options)
    if not windows:
        raise ValueError("no WFO windows generated")

    round_results: list[WfoRoundResult] = []
    for window in windows:
        candidate = optimize_fn(window)
        round_result = evaluate_fn(window, candidate)
        round_results.append(evaluate_wfo_round(round_result, config))

    summary = summarize_wfo_results(round_results)
    passed, fail_reason = evaluate_wfo_summary(summary, config)

    return WfoRunResult(
        windows=windows,
        round_results=round_results,
        summary=summary,
        passed=passed,
        fail_reason=fail_reason,
    )
