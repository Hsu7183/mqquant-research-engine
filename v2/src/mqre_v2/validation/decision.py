from __future__ import annotations

import math
from dataclasses import dataclass

from mqre_v2.validation.wfo.results import WfoSummary


@dataclass(frozen=True)
class DecisionResult:
    upgrade: bool
    reason: str
    baseline_score: float
    challenger_score: float


def score_wfo_summary(summary: WfoSummary) -> float:
    profit_component = 0.0
    if summary.total_test_net_profit > 0:
        profit_component = math.log(1 + summary.total_test_net_profit) * 10

    average_test_pf = summary.average_test_pf
    if math.isinf(average_test_pf):
        average_test_pf = 5.0

    return (
        summary.pass_rate * 50
        + profit_component
        - summary.max_test_mdd * 0.001
        + average_test_pf * 10
    )


def compare_baseline_challenger(
    baseline: WfoSummary,
    challenger: WfoSummary,
    min_improvement: float = 5.0,
) -> DecisionResult:
    baseline_score = score_wfo_summary(baseline)
    challenger_score = score_wfo_summary(challenger)

    if challenger_score >= baseline_score + min_improvement:
        reason = "challenger score improved significantly"
        upgrade = True
    elif challenger_score < baseline_score:
        reason = "challenger worse than baseline"
        upgrade = False
    else:
        reason = "no significant improvement"
        upgrade = False

    return DecisionResult(
        upgrade=upgrade,
        reason=reason,
        baseline_score=baseline_score,
        challenger_score=challenger_score,
    )


__all__ = [
    "DecisionResult",
    "compare_baseline_challenger",
    "score_wfo_summary",
]
