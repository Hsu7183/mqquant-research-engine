from datetime import date
from typing import Any

import pytest

from mqre_v2.validation.wfo import WfoGateConfig, WfoRunResult, WfoRoundResult, run_wfo
from mqre_v2.validation.wfo.windows import WfoWindow


def _round_result(
    window: WfoWindow,
    candidate: Any,
    *,
    test_net_profit: float = 100.0,
    test_mdd: float = 1000.0,
    test_pf: float = 1.2,
    test_trade_count: int = 25,
) -> WfoRoundResult:
    return WfoRoundResult(
        round_id=window.round_id,
        train_start=window.train_start,
        train_end=window.train_end,
        gap_start=window.gap_start,
        gap_end=window.gap_end,
        test_start=window.test_start,
        test_end=window.test_end,
        strategy_name=str(candidate["strategy_name"]),
        params_hash=str(candidate["params_hash"]),
        train_net_profit=1000.0,
        train_mdd=120.0,
        train_pf=1.5,
        train_trade_count=60,
        test_net_profit=test_net_profit,
        test_mdd=test_mdd,
        test_pf=test_pf,
        test_trade_count=test_trade_count,
        pass_flag=False,
        fail_reason="unchecked",
    )


def _run_dates() -> tuple[date, date]:
    return date(2020, 1, 1), date(2024, 12, 31)


def test_run_wfo_returns_full_run_result() -> None:
    def optimize_fn(window: WfoWindow) -> dict[str, str]:
        return {"strategy_name": "baseline", "params_hash": f"params-{window.round_id}"}

    def evaluate_fn(window: WfoWindow, candidate: dict[str, str]) -> WfoRoundResult:
        return _round_result(window, candidate)

    start_date, end_date = _run_dates()
    result = run_wfo(start_date, end_date, "baseline", optimize_fn, evaluate_fn)

    assert isinstance(result, WfoRunResult)
    assert len(result.windows) == 3
    assert len(result.round_results) == 3
    assert result.summary.total_rounds == 3
    assert result.passed is True
    assert result.fail_reason == ""


def test_optimize_fn_is_called_once_per_window() -> None:
    calls: list[WfoWindow] = []

    def optimize_fn(window: WfoWindow) -> dict[str, str]:
        calls.append(window)
        return {"strategy_name": "baseline", "params_hash": f"params-{window.round_id}"}

    def evaluate_fn(window: WfoWindow, candidate: dict[str, str]) -> WfoRoundResult:
        return _round_result(window, candidate)

    start_date, end_date = _run_dates()
    result = run_wfo(start_date, end_date, "baseline", optimize_fn, evaluate_fn)

    assert calls == result.windows


def test_evaluate_fn_is_called_once_per_window() -> None:
    calls: list[tuple[WfoWindow, dict[str, str]]] = []

    def optimize_fn(window: WfoWindow) -> dict[str, str]:
        return {"strategy_name": "baseline", "params_hash": f"params-{window.round_id}"}

    def evaluate_fn(window: WfoWindow, candidate: dict[str, str]) -> WfoRoundResult:
        calls.append((window, candidate))
        return _round_result(window, candidate)

    start_date, end_date = _run_dates()
    result = run_wfo(start_date, end_date, "baseline", optimize_fn, evaluate_fn)

    assert [window for window, _ in calls] == result.windows
    assert len(calls) == len(result.windows)


def test_round_results_are_gated() -> None:
    def optimize_fn(window: WfoWindow) -> dict[str, str]:
        return {"strategy_name": "baseline", "params_hash": f"params-{window.round_id}"}

    def evaluate_fn(window: WfoWindow, candidate: dict[str, str]) -> WfoRoundResult:
        return _round_result(window, candidate, test_trade_count=5)

    start_date, end_date = _run_dates()
    result = run_wfo(start_date, end_date, "baseline", optimize_fn, evaluate_fn)

    assert all(round_result.pass_flag is False for round_result in result.round_results)
    assert all(
        round_result.fail_reason == "test_trade_count below minimum"
        for round_result in result.round_results
    )


def test_summary_is_generated_from_gated_results() -> None:
    def optimize_fn(window: WfoWindow) -> dict[str, str]:
        return {"strategy_name": "baseline", "params_hash": f"params-{window.round_id}"}

    def evaluate_fn(window: WfoWindow, candidate: dict[str, str]) -> WfoRoundResult:
        return _round_result(
            window,
            candidate,
            test_net_profit=100.0 * window.round_id,
            test_trade_count=20 + window.round_id,
        )

    start_date, end_date = _run_dates()
    result = run_wfo(start_date, end_date, "baseline", optimize_fn, evaluate_fn)

    assert result.summary.total_rounds == 3
    assert result.summary.passed_rounds == 3
    assert result.summary.total_test_net_profit == pytest.approx(600.0)
    assert result.summary.average_test_net_profit == pytest.approx(200.0)


def test_summary_gate_failure_sets_run_failure() -> None:
    def optimize_fn(window: WfoWindow) -> dict[str, str]:
        return {"strategy_name": "baseline", "params_hash": f"params-{window.round_id}"}

    def evaluate_fn(window: WfoWindow, candidate: dict[str, str]) -> WfoRoundResult:
        return _round_result(window, candidate, test_trade_count=5)

    start_date, end_date = _run_dates()
    result = run_wfo(start_date, end_date, "baseline", optimize_fn, evaluate_fn)

    assert result.passed is False
    assert result.fail_reason == "pass_rate below minimum"


def test_no_windows_raises_value_error() -> None:
    def optimize_fn(window: WfoWindow) -> dict[str, str]:
        return {"strategy_name": "baseline", "params_hash": f"params-{window.round_id}"}

    def evaluate_fn(window: WfoWindow, candidate: dict[str, str]) -> WfoRoundResult:
        return _round_result(window, candidate)

    with pytest.raises(ValueError, match="no WFO windows generated"):
        run_wfo(
            date(2020, 1, 1),
            date(2020, 12, 31),
            "baseline",
            optimize_fn,
            evaluate_fn,
        )


def test_optimize_fn_exception_is_not_swallowed() -> None:
    def optimize_fn(window: WfoWindow) -> dict[str, str]:
        raise RuntimeError(f"optimizer failed round {window.round_id}")

    def evaluate_fn(window: WfoWindow, candidate: dict[str, str]) -> WfoRoundResult:
        return _round_result(window, candidate)

    start_date, end_date = _run_dates()
    with pytest.raises(RuntimeError, match="optimizer failed round 1"):
        run_wfo(start_date, end_date, "baseline", optimize_fn, evaluate_fn)


def test_evaluate_fn_exception_is_not_swallowed() -> None:
    def optimize_fn(window: WfoWindow) -> dict[str, str]:
        return {"strategy_name": "baseline", "params_hash": f"params-{window.round_id}"}

    def evaluate_fn(window: WfoWindow, candidate: dict[str, str]) -> WfoRoundResult:
        raise RuntimeError(f"evaluation failed round {window.round_id}")

    start_date, end_date = _run_dates()
    with pytest.raises(RuntimeError, match="evaluation failed round 1"):
        run_wfo(start_date, end_date, "baseline", optimize_fn, evaluate_fn)


def test_public_runner_imports_from_wfo_package() -> None:
    assert run_wfo is not None
    assert WfoRunResult is not None
