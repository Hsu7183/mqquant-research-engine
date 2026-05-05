import math

import pytest

from mqre_v2.validation.decision import (
    DecisionResult,
    compare_baseline_challenger,
    score_wfo_summary,
)
from mqre_v2.validation.wfo import WfoSummary


def _summary(
    *,
    pass_rate: float,
    total_test_net_profit: float,
    max_test_mdd: float,
    average_test_pf: float,
) -> WfoSummary:
    total_rounds = 10
    passed_rounds = round(pass_rate * total_rounds)
    return WfoSummary(
        total_rounds=total_rounds,
        passed_rounds=passed_rounds,
        failed_rounds=total_rounds - passed_rounds,
        pass_rate=pass_rate,
        total_test_net_profit=total_test_net_profit,
        average_test_net_profit=total_test_net_profit / total_rounds,
        max_test_mdd=max_test_mdd,
        average_test_pf=average_test_pf,
        total_test_trade_count=200,
    )


def test_challenger_significantly_better_upgrades() -> None:
    baseline = _summary(
        pass_rate=0.6,
        total_test_net_profit=500.0,
        max_test_mdd=1500.0,
        average_test_pf=1.2,
    )
    challenger = _summary(
        pass_rate=0.9,
        total_test_net_profit=3000.0,
        max_test_mdd=500.0,
        average_test_pf=2.0,
    )

    result = compare_baseline_challenger(baseline, challenger)

    assert isinstance(result, DecisionResult)
    assert result.upgrade is True
    assert result.reason == "challenger score improved significantly"
    assert result.challenger_score >= result.baseline_score + 5.0


def test_challenger_slightly_better_but_below_threshold_does_not_upgrade() -> None:
    baseline = _summary(
        pass_rate=0.7,
        total_test_net_profit=1000.0,
        max_test_mdd=1000.0,
        average_test_pf=1.5,
    )
    challenger = _summary(
        pass_rate=0.7,
        total_test_net_profit=1200.0,
        max_test_mdd=1000.0,
        average_test_pf=1.5,
    )

    result = compare_baseline_challenger(baseline, challenger)

    assert result.upgrade is False
    assert result.reason == "no significant improvement"
    assert result.baseline_score < result.challenger_score < result.baseline_score + 5.0


def test_challenger_worse_does_not_upgrade() -> None:
    baseline = _summary(
        pass_rate=0.8,
        total_test_net_profit=1500.0,
        max_test_mdd=800.0,
        average_test_pf=1.8,
    )
    challenger = _summary(
        pass_rate=0.5,
        total_test_net_profit=500.0,
        max_test_mdd=2000.0,
        average_test_pf=1.1,
    )

    result = compare_baseline_challenger(baseline, challenger)

    assert result.upgrade is False
    assert result.reason == "challenger worse than baseline"
    assert result.challenger_score < result.baseline_score


def test_score_handles_infinite_pf() -> None:
    summary = _summary(
        pass_rate=1.0,
        total_test_net_profit=100.0,
        max_test_mdd=0.0,
        average_test_pf=math.inf,
    )

    score = score_wfo_summary(summary)

    assert math.isfinite(score)
    assert score == pytest.approx(50.0 + math.log(101.0) * 10 + 50.0)


def test_score_handles_non_positive_total_profit() -> None:
    summary = _summary(
        pass_rate=1.0,
        total_test_net_profit=-100.0,
        max_test_mdd=100.0,
        average_test_pf=1.0,
    )

    score = score_wfo_summary(summary)

    assert score == pytest.approx(50.0 - 0.1 + 10.0)
