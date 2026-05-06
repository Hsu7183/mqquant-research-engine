import json
from datetime import date
from pathlib import Path

import pytest

from mqre_v2.runs.run_manager import RunManifest, create_run_directory, write_manifest
from mqre_v2.runs.run_pipeline import run_pipeline_from_run


def _create_run(tmp_path) -> str:
    run_path = create_run_directory(str(tmp_path / "runs"), "0313plus")
    write_manifest(
        run_path,
        RunManifest(
            run_id=Path(run_path).name,
            strategy_name="0313plus",
            created_at="2026-05-06T00:00:00+00:00",
            parameter_grid_path="grid.yaml",
            template_path="template.xs",
            total_param_combinations=0,
        ),
    )
    return run_path


def _write_xs(run_path: str, stem: str) -> None:
    (Path(run_path) / "xs" / f"{stem}.xs").write_text("value1;", encoding="utf-8")


def _write_txt(run_path: str, stem: str, entry_price: int, exit_price: int) -> None:
    _write_txt_rows(
        run_path,
        stem,
        [
            (
                "2023-03-01T09:00:00",
                "2023-03-01T09:05:00",
                "long",
                entry_price,
                exit_price,
            ),
        ],
    )


def _write_txt_rows(run_path: str, stem: str, rows: list[tuple]) -> None:
    lines = ["entry_time,exit_time,side,entry_price,exit_price"]
    lines.extend(
        f"{entry_time},{exit_time},{side},{entry_price},{exit_price}"
        for entry_time, exit_time, side, entry_price, exit_price in rows
    )
    (Path(run_path) / "txt" / f"{stem}.txt").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def test_strategy_detail_json_is_generated(tmp_path) -> None:
    run_path = _create_run(tmp_path)
    _write_xs(run_path, "alpha")
    _write_txt(run_path, "alpha", 100, 120)

    run_pipeline_from_run(
        run_path,
        start_date=date(2020, 1, 1),
        end_date=date(2023, 12, 31),
    )

    detail_path = Path(run_path) / "reports" / "details" / "alpha.json"
    payload = json.loads(detail_path.read_text(encoding="utf-8"))

    assert detail_path.is_file()
    assert payload["strategy_name"] == "alpha"
    assert payload["run_id"] == Path(run_path).name


def test_each_strategy_has_detail_json(tmp_path) -> None:
    run_path = _create_run(tmp_path)
    _write_xs(run_path, "alpha")
    _write_xs(run_path, "beta")
    _write_txt(run_path, "alpha", 100, 120)
    _write_txt(run_path, "beta", 100, 140)

    run_pipeline_from_run(
        run_path,
        start_date=date(2020, 1, 1),
        end_date=date(2023, 12, 31),
    )

    details_dir = Path(run_path) / "reports" / "details"
    assert sorted(path.name for path in details_dir.glob("*.json")) == [
        "alpha.json",
        "beta.json",
    ]


def test_strategy_detail_equity_curve_uses_weekly_series(tmp_path) -> None:
    run_path = _create_run(tmp_path)
    _write_xs(run_path, "alpha")
    _write_txt(run_path, "alpha", 100, 120)

    run_pipeline_from_run(
        run_path,
        start_date=date(2020, 1, 1),
        end_date=date(2023, 12, 31),
    )
    payload = json.loads(
        (Path(run_path) / "reports" / "details" / "alpha.json").read_text(
            encoding="utf-8"
        )
    )

    assert len(payload["equity_curve"]) == 1
    assert payload["equity_curve"][0] == {"week": "2023-W09", "equity": 100020.0}
    assert payload["weekly_pnl"][0] == {"week": "2023-W09", "pnl": 20.0}
    assert payload["period_pnl"][0] == {"index": 1, "pnl": 20.0}


def test_strategy_detail_kpi_fields_exist(tmp_path) -> None:
    run_path = _create_run(tmp_path)
    _write_xs(run_path, "alpha")
    _write_txt(run_path, "alpha", 100, 120)

    run_pipeline_from_run(
        run_path,
        start_date=date(2020, 1, 1),
        end_date=date(2023, 12, 31),
    )
    payload = json.loads(
        (Path(run_path) / "reports" / "details" / "alpha.json").read_text(
            encoding="utf-8"
        )
    )

    assert "period" in payload
    assert "trade_stats" in payload
    assert set(payload["kpi"]) == {"score", "profit", "pass_rate", "mdd", "pf"}
    assert payload["summary"]["score"] == payload["kpi"]["score"]


def test_strategy_detail_trade_stats_are_calculated(tmp_path) -> None:
    run_path = _create_run(tmp_path)
    _write_xs(run_path, "alpha")
    _write_txt_rows(
        run_path,
        "alpha",
        [
            ("2023-03-01T09:00:00", "2023-03-01T09:05:00", "long", 100, 150),
            ("2023-03-03T09:00:00", "2023-03-03T09:05:00", "short", 120, 100),
            ("2023-03-07T09:00:00", "2023-03-07T09:05:00", "long", 100, 90),
            ("2023-03-08T09:00:00", "2023-03-08T09:05:00", "short", 100, 110),
            ("2023-03-14T09:00:00", "2023-03-14T09:05:00", "long", 100, 130),
        ],
    )

    run_pipeline_from_run(
        run_path,
        start_date=date(2020, 1, 1),
        end_date=date(2023, 12, 31),
    )
    payload = json.loads(
        (Path(run_path) / "reports" / "details" / "alpha.json").read_text(
            encoding="utf-8"
        )
    )
    stats = payload["trade_stats"]

    assert payload["period"] == {"start": "2023-03-01", "end": "2023-03-14"}
    assert payload["weekly_pnl"] == [
        {"week": "2023-W09", "pnl": 70.0},
        {"week": "2023-W10", "pnl": -20.0},
        {"week": "2023-W11", "pnl": 30.0},
    ]
    assert payload["equity_curve"] == [
        {"week": "2023-W09", "equity": 100070.0},
        {"week": "2023-W10", "equity": 100050.0},
        {"week": "2023-W11", "equity": 100080.0},
    ]
    assert stats["trade_count"] == 5
    assert stats["long_count"] == 3
    assert stats["short_count"] == 2
    assert stats["win_count"] == 3
    assert stats["loss_count"] == 2
    assert stats["win_rate"] == pytest.approx(0.6)
    assert stats["total_profit"] == 80.0
    assert stats["avg_trade_pnl"] == 16.0
    assert stats["avg_win"] == pytest.approx(100.0 / 3.0)
    assert stats["avg_loss"] == 10.0
    assert stats["largest_win"] == 50.0
    assert stats["largest_loss"] == 10.0
    assert stats["gross_profit"] == 100.0
    assert stats["gross_loss"] == 20.0
    assert stats["profit_factor"] == 5.0
    assert stats["payoff_ratio"] == pytest.approx(10.0 / 3.0)
    assert stats["max_losing_streak"] == 2
    assert stats["underwater_weeks"] == 1
    assert stats["max_drawdown"] == 20.0
