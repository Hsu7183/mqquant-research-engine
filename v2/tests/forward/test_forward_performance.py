import csv
import json
from datetime import datetime
from pathlib import Path

import pytest

from mqre_v2.forward.forward_evaluator import evaluate_forward_performance
from mqre_v2.forward.forward_logger import log_forward_trade


def test_log_forward_trade_writes_cumulative_csv(tmp_path: Path) -> None:
    log_path = tmp_path / "forward_log.csv"

    first = log_forward_trade(
        "alpha",
        datetime(2026, 5, 7, 9, 0),
        price=20000.0,
        pnl=100.0,
        log_path=str(log_path),
    )
    second = log_forward_trade(
        "alpha",
        datetime(2026, 5, 7, 9, 5),
        price=20020.0,
        pnl=-30.0,
        log_path=str(log_path),
    )

    with log_path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert first["cumulative_pnl"] == pytest.approx(100.0)
    assert second["cumulative_pnl"] == pytest.approx(70.0)
    assert rows[0]["strategy_id"] == "alpha"
    assert float(rows[1]["cumulative_pnl"]) == pytest.approx(70.0)


def test_evaluate_forward_performance_writes_report(tmp_path: Path) -> None:
    log_path = tmp_path / "forward_log.csv"
    ranking_path = tmp_path / "ranking.json"
    report_path = tmp_path / "forward_report.json"
    ranking_path.write_text(
        json.dumps(
            [
                {
                    "strategy_id": "alpha",
                    "annual_return": 0.001,
                    "score": 120.0,
                }
            ]
        ),
        encoding="utf-8",
    )
    for index, pnl in enumerate([100.0, -40.0, 80.0, 50.0], start=1):
        log_forward_trade(
            "alpha",
            f"2026-05-07 09:0{index}:00",
            price=20000.0 + index,
            pnl=pnl,
            log_path=str(log_path),
        )

    report = evaluate_forward_performance(
        "alpha",
        log_path=str(log_path),
        output_path=str(report_path),
        backtest_summary_path=str(ranking_path),
    )
    loaded = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["trade_count"] == 4
    assert report["total_pnl"] == pytest.approx(190.0)
    assert report["win_rate"] == pytest.approx(0.75)
    assert report["max_drawdown"] == pytest.approx(40.0)
    assert report["vs_backtest_diff"] == pytest.approx(90.0)
    assert loaded["strategy_id"] == "alpha"
    assert loaded["recommendation"] == "continue"


def test_evaluate_forward_performance_marks_bad_deviation(tmp_path: Path) -> None:
    log_path = tmp_path / "forward_log.csv"
    ranking_path = tmp_path / "ranking.json"
    report_path = tmp_path / "forward_report.json"
    ranking_path.write_text(
        json.dumps([{"strategy_id": "alpha", "annual_return": 0.2}]),
        encoding="utf-8",
    )
    for index, pnl in enumerate([-100.0, -80.0, 20.0], start=1):
        log_forward_trade(
            "alpha",
            f"2026-05-07 09:0{index}:00",
            price=20000.0 + index,
            pnl=pnl,
            log_path=str(log_path),
        )

    report = evaluate_forward_performance(
        "alpha",
        log_path=str(log_path),
        output_path=str(report_path),
        backtest_summary_path=str(ranking_path),
    )

    assert report["is_deviating"] is True
    assert report["forward_status"] == "bad"
    assert report["recommendation"] == "stop"
