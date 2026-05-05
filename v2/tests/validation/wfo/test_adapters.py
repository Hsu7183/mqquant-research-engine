from datetime import date

from mqre_v2.validation.wfo import (
    BacktestResult,
    OptimizerResult,
    WfoRoundResult,
    default_evaluate_fn,
    default_optimize_fn,
    run_wfo,
)
from mqre_v2.validation.wfo.gates import WfoGateConfig, evaluate_wfo_round
from mqre_v2.validation.wfo.windows import WfoWindow, generate_wfo_windows


def _window() -> WfoWindow:
    return generate_wfo_windows(date(2020, 1, 1), date(2024, 12, 31))[0]


def test_default_optimize_fn_returns_optimizer_result() -> None:
    result = default_optimize_fn(_window())

    assert isinstance(result, OptimizerResult)
    assert result.strategy_name == "dummy_strategy"
    assert result.params["adapter"] == "dummy"


def test_default_optimize_fn_params_hash_has_value() -> None:
    result = default_optimize_fn(_window())

    assert result.params_hash
    assert result.params_hash == str(result.params)


def test_default_evaluate_fn_returns_wfo_round_result() -> None:
    window = _window()
    optimizer_result = default_optimize_fn(window)
    result = default_evaluate_fn(window, optimizer_result)

    assert isinstance(result, WfoRoundResult)
    assert result.round_id == window.round_id
    assert result.strategy_name == optimizer_result.strategy_name
    assert result.params_hash == optimizer_result.params_hash


def test_default_evaluate_fn_result_can_be_gated() -> None:
    window = _window()
    result = default_evaluate_fn(window, default_optimize_fn(window))
    gated = evaluate_wfo_round(result, WfoGateConfig())

    assert gated.pass_flag is True
    assert gated.fail_reason == ""


def test_default_adapters_can_connect_to_run_wfo() -> None:
    result = run_wfo(
        date(2020, 1, 1),
        date(2024, 12, 31),
        "dummy_strategy",
        default_optimize_fn,
        default_evaluate_fn,
    )

    assert len(result.windows) == 3
    assert len(result.round_results) == 3
    assert result.passed is True
    assert result.summary.passed_rounds == 3


def test_backtest_result_dataclass_can_hold_test_metrics() -> None:
    result = BacktestResult(
        test_net_profit=500.0,
        test_mdd=1000.0,
        test_pf=1.2,
        test_trade_count=25,
    )

    assert result.test_net_profit == 500.0
    assert result.test_trade_count == 25
