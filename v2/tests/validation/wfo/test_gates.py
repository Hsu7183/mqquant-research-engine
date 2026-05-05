from datetime import date

from mqre_v2.validation.wfo import (
    WfoGateConfig,
    WfoRoundResult,
    WfoSummary,
    evaluate_wfo_round,
    evaluate_wfo_summary,
)


def _round_result(
    *,
    test_net_profit: float = 500.0,
    test_mdd: float = 1000.0,
    test_pf: float = 1.2,
    test_trade_count: int = 25,
    pass_flag: bool = False,
    fail_reason: str = "unchecked",
) -> WfoRoundResult:
    return WfoRoundResult(
        round_id=1,
        train_start=date(2020, 1, 1),
        train_end=date(2022, 12, 31),
        gap_start=date(2023, 1, 1),
        gap_end=date(2023, 1, 31),
        test_start=date(2023, 2, 1),
        test_end=date(2023, 7, 31),
        strategy_name="baseline",
        params_hash="abc123",
        train_net_profit=1000.0,
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


def test_round_passes_when_all_conditions_are_met() -> None:
    gated = evaluate_wfo_round(_round_result(), WfoGateConfig())

    assert gated.pass_flag is True
    assert gated.fail_reason == ""


def test_round_fails_when_trade_count_is_too_low() -> None:
    gated = evaluate_wfo_round(
        _round_result(test_trade_count=19),
        WfoGateConfig(min_test_trade_count=20),
    )

    assert gated.pass_flag is False
    assert gated.fail_reason == "test_trade_count below minimum"


def test_round_fails_when_mdd_is_too_high() -> None:
    gated = evaluate_wfo_round(
        _round_result(test_mdd=15001.0),
        WfoGateConfig(max_test_mdd=15000.0),
    )

    assert gated.pass_flag is False
    assert gated.fail_reason == "test_mdd above maximum"


def test_round_fails_when_pf_is_too_low() -> None:
    gated = evaluate_wfo_round(
        _round_result(test_pf=1.04),
        WfoGateConfig(min_test_pf=1.05),
    )

    assert gated.pass_flag is False
    assert gated.fail_reason == "test_pf below minimum"


def test_round_fails_when_net_profit_is_not_positive() -> None:
    gated = evaluate_wfo_round(_round_result(test_net_profit=0.0), WfoGateConfig())

    assert gated.pass_flag is False
    assert gated.fail_reason == "test_net_profit not positive"


def test_multiple_round_fail_reasons_are_joined_with_semicolons() -> None:
    gated = evaluate_wfo_round(
        _round_result(test_trade_count=10, test_pf=0.9, test_net_profit=-1.0),
        WfoGateConfig(min_test_trade_count=20, min_test_pf=1.05),
    )

    assert gated.pass_flag is False
    assert (
        gated.fail_reason
        == "test_trade_count below minimum; test_pf below minimum; test_net_profit not positive"
    )


def test_evaluate_wfo_round_does_not_mutate_original_result() -> None:
    original = _round_result(pass_flag=False, fail_reason="unchecked")
    gated = evaluate_wfo_round(original, WfoGateConfig())

    assert gated is not original
    assert original.pass_flag is False
    assert original.fail_reason == "unchecked"
    assert gated.pass_flag is True
    assert gated.fail_reason == ""


def test_summary_fails_when_pass_rate_is_too_low() -> None:
    summary = WfoSummary(
        total_rounds=3,
        passed_rounds=1,
        failed_rounds=2,
        pass_rate=1 / 3,
        total_test_net_profit=500.0,
        average_test_net_profit=166.67,
        max_test_mdd=1000.0,
        average_test_pf=1.2,
        total_test_trade_count=75,
    )

    passed, fail_reason = evaluate_wfo_summary(summary, WfoGateConfig(min_pass_rate=0.6))

    assert passed is False
    assert fail_reason == "pass_rate below minimum"


def test_summary_fails_when_total_test_net_profit_is_not_positive() -> None:
    summary = WfoSummary(
        total_rounds=3,
        passed_rounds=2,
        failed_rounds=1,
        pass_rate=2 / 3,
        total_test_net_profit=0.0,
        average_test_net_profit=0.0,
        max_test_mdd=1000.0,
        average_test_pf=1.2,
        total_test_trade_count=75,
    )

    passed, fail_reason = evaluate_wfo_summary(
        summary,
        WfoGateConfig(require_positive_total_profit=True),
    )

    assert passed is False
    assert fail_reason == "total_test_net_profit not positive"


def test_public_gate_imports_from_wfo_package() -> None:
    assert WfoGateConfig is not None
    assert evaluate_wfo_round is not None
    assert evaluate_wfo_summary is not None
