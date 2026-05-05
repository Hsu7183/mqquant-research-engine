from datetime import date

import pytest

from mqre_v2.validation.wfo import (
    WfoRoundResult,
    WfoSummary,
    WfoWindow,
    generate_wfo_windows,
    summarize_wfo_results,
)


def _round_result(
    *,
    round_id: int,
    test_net_profit: float,
    test_mdd: float,
    test_pf: float,
    test_trade_count: int,
    pass_flag: bool,
    fail_reason: str = "",
) -> WfoRoundResult:
    return WfoRoundResult(
        round_id=round_id,
        train_start=date(2020, 1, 1),
        train_end=date(2022, 12, 31),
        gap_start=date(2023, 1, 1),
        gap_end=date(2023, 1, 31),
        test_start=date(2023, 2, 1),
        test_end=date(2023, 7, 31),
        strategy_name="baseline",
        params_hash=f"params-{round_id}",
        train_net_profit=1000.0 + round_id,
        train_mdd=120.0,
        train_pf=1.5,
        train_trade_count=60,
        test_net_profit=test_net_profit,
        test_mdd=test_mdd,
        test_pf=test_pf,
        test_trade_count=test_trade_count,
        pass_flag=pass_flag,
        fail_reason=fail_reason,
    )


def test_create_wfo_round_result() -> None:
    result = _round_result(
        round_id=1,
        test_net_profit=300.0,
        test_mdd=50.0,
        test_pf=1.4,
        test_trade_count=20,
        pass_flag=True,
    )

    assert result.round_id == 1
    assert result.strategy_name == "baseline"
    assert result.params_hash == "params-1"
    assert result.pass_flag is True


def test_summarize_wfo_results_counts_and_pass_rate() -> None:
    summary = summarize_wfo_results(
        [
            _round_result(
                round_id=1,
                test_net_profit=300.0,
                test_mdd=50.0,
                test_pf=1.4,
                test_trade_count=20,
                pass_flag=True,
            ),
            _round_result(
                round_id=2,
                test_net_profit=-100.0,
                test_mdd=90.0,
                test_pf=0.8,
                test_trade_count=12,
                pass_flag=False,
                fail_reason="mdd",
            ),
        ]
    )

    assert summary.total_rounds == 2
    assert summary.passed_rounds == 1
    assert summary.failed_rounds == 1
    assert summary.pass_rate == pytest.approx(0.5)


def test_summarize_wfo_results_net_profit() -> None:
    summary = summarize_wfo_results(
        [
            _round_result(
                round_id=1,
                test_net_profit=300.0,
                test_mdd=50.0,
                test_pf=1.4,
                test_trade_count=20,
                pass_flag=True,
            ),
            _round_result(
                round_id=2,
                test_net_profit=-100.0,
                test_mdd=90.0,
                test_pf=0.8,
                test_trade_count=12,
                pass_flag=False,
            ),
            _round_result(
                round_id=3,
                test_net_profit=250.0,
                test_mdd=40.0,
                test_pf=1.6,
                test_trade_count=18,
                pass_flag=True,
            ),
        ]
    )

    assert summary.total_test_net_profit == pytest.approx(450.0)
    assert summary.average_test_net_profit == pytest.approx(150.0)


def test_summarize_wfo_results_risk_pf_and_trade_count() -> None:
    summary = summarize_wfo_results(
        [
            _round_result(
                round_id=1,
                test_net_profit=300.0,
                test_mdd=50.0,
                test_pf=1.4,
                test_trade_count=20,
                pass_flag=True,
            ),
            _round_result(
                round_id=2,
                test_net_profit=-100.0,
                test_mdd=90.0,
                test_pf=0.8,
                test_trade_count=12,
                pass_flag=False,
            ),
            _round_result(
                round_id=3,
                test_net_profit=250.0,
                test_mdd=40.0,
                test_pf=1.6,
                test_trade_count=18,
                pass_flag=True,
            ),
        ]
    )

    assert summary.max_test_mdd == pytest.approx(90.0)
    assert summary.average_test_pf == pytest.approx((1.4 + 0.8 + 1.6) / 3)
    assert summary.total_test_trade_count == 50


def test_summarize_wfo_results_empty_raises() -> None:
    with pytest.raises(ValueError, match="results cannot be empty"):
        summarize_wfo_results([])


def test_public_imports_from_wfo_package() -> None:
    assert WfoRoundResult is not None
    assert WfoSummary is not None
    assert WfoWindow is not None
    assert generate_wfo_windows is not None
    assert summarize_wfo_results is not None
