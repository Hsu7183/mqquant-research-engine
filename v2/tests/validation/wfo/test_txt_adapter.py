from datetime import date, datetime
from math import inf

import pytest

from mqre_v2.core.trades import TradeRecord
from mqre_v2.validation.wfo import (
    TxtWfoInput,
    WfoGateConfig,
    WfoRoundResult,
    build_txt_evaluate_fn,
    compute_trade_metrics,
    run_wfo,
)
from mqre_v2.validation.wfo.adapters import OptimizerResult
from mqre_v2.validation.wfo.windows import WfoWindow


def _trade(exit_time: datetime, pnl: float) -> TradeRecord:
    return TradeRecord(
        entry_time=datetime(2023, 1, 1, 9, 0),
        exit_time=exit_time,
        entry_price=100.0,
        exit_price=100.0 + pnl,
        direction=1,
        pnl=pnl,
    )


def _window() -> WfoWindow:
    return WfoWindow(
        round_id=1,
        train_start=date(2023, 1, 1),
        train_end=date(2023, 1, 31),
        gap_start=date(2023, 2, 1),
        gap_end=date(2023, 2, 28),
        test_start=date(2023, 3, 1),
        test_end=date(2023, 3, 31),
    )


def _write_txt(path, rows: str) -> None:
    path.write_text(
        "entry_time,exit_time,side,entry_price,exit_price\n" + rows,
        encoding="utf-8",
    )


def test_compute_trade_metrics_net_profit() -> None:
    metrics = compute_trade_metrics(
        [
            _trade(datetime(2023, 3, 1, 10, 0), 100.0),
            _trade(datetime(2023, 3, 2, 10, 0), -40.0),
            _trade(datetime(2023, 3, 3, 10, 0), 20.0),
        ]
    )

    assert metrics["net_profit"] == pytest.approx(80.0)


def test_compute_trade_metrics_mdd() -> None:
    metrics = compute_trade_metrics(
        [
            _trade(datetime(2023, 3, 1, 10, 0), 100.0),
            _trade(datetime(2023, 3, 2, 10, 0), -40.0),
            _trade(datetime(2023, 3, 3, 10, 0), 20.0),
            _trade(datetime(2023, 3, 4, 10, 0), -90.0),
        ]
    )

    assert metrics["mdd"] == pytest.approx(110.0)


def test_compute_trade_metrics_pf() -> None:
    metrics = compute_trade_metrics(
        [
            _trade(datetime(2023, 3, 1, 10, 0), 100.0),
            _trade(datetime(2023, 3, 2, 10, 0), -40.0),
            _trade(datetime(2023, 3, 3, 10, 0), 20.0),
        ]
    )

    assert metrics["pf"] == pytest.approx(3.0)


def test_compute_trade_metrics_empty() -> None:
    metrics = compute_trade_metrics([])

    assert metrics["trade_count"] == 0
    assert metrics["net_profit"] == 0.0
    assert metrics["mdd"] == 0.0
    assert metrics["pf"] == 0.0


def test_compute_trade_metrics_pf_is_infinite_when_no_losses() -> None:
    metrics = compute_trade_metrics([_trade(datetime(2023, 3, 1, 10, 0), 100.0)])

    assert metrics["pf"] == inf


def test_build_txt_evaluate_fn_reads_txt_and_returns_round_result(tmp_path) -> None:
    txt_path = tmp_path / "trades.txt"
    _write_txt(
        txt_path,
        "2023-03-01T09:00:00,2023-03-01T09:05:00,long,100,110\n",
    )
    evaluate_fn = build_txt_evaluate_fn(TxtWfoInput("txt-strategy", str(txt_path), "hash-1"))

    result = evaluate_fn(
        _window(),
        OptimizerResult("train", {}, "train-hash", 1000.0, 100.0, 1.5, 30),
    )

    assert isinstance(result, WfoRoundResult)
    assert result.strategy_name == "txt-strategy"
    assert result.params_hash == "hash-1"
    assert result.train_net_profit == pytest.approx(1000.0)
    assert result.test_net_profit == pytest.approx(10.0)
    assert result.test_trade_count == 1
    assert result.pass_flag is False
    assert result.fail_reason == ""


def test_build_txt_evaluate_fn_only_includes_test_window_trades(tmp_path) -> None:
    txt_path = tmp_path / "trades.txt"
    _write_txt(
        txt_path,
        "\n".join(
            [
                "2023-02-01T09:00:00,2023-02-01T09:05:00,long,100,999",
                "2023-03-01T09:00:00,2023-03-01T09:05:00,long,100,110",
                "2023-04-01T09:00:00,2023-04-01T09:05:00,long,100,999",
            ]
        )
        + "\n",
    )
    evaluate_fn = build_txt_evaluate_fn(TxtWfoInput("txt-strategy", str(txt_path)))

    result = evaluate_fn(_window(), {})

    assert result.test_trade_count == 1
    assert result.test_net_profit == pytest.approx(10.0)


def test_txt_adapter_can_connect_to_run_wfo(tmp_path) -> None:
    txt_path = tmp_path / "trades.txt"
    _write_txt(
        txt_path,
        "2023-03-01T09:00:00,2023-03-01T09:05:00,long,100,110\n",
    )

    def optimize_fn(window: WfoWindow) -> OptimizerResult:
        return OptimizerResult("train", {}, "train-hash", 1000.0, 100.0, 1.5, 30)

    result = run_wfo(
        date(2023, 1, 1),
        date(2023, 3, 31),
        "txt-strategy",
        optimize_fn,
        build_txt_evaluate_fn(TxtWfoInput("txt-strategy", str(txt_path))),
        window_kwargs={"train_months": 1, "gap_months": 1, "test_months": 1},
        gate_config=WfoGateConfig(min_test_trade_count=1),
    )

    assert result.passed is True
    assert result.summary.total_rounds == 1
    assert result.summary.total_test_net_profit == pytest.approx(10.0)


def test_public_txt_adapter_imports_from_wfo_package() -> None:
    assert TxtWfoInput is not None
    assert build_txt_evaluate_fn is not None
    assert compute_trade_metrics is not None
