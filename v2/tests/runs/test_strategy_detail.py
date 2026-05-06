import json
from datetime import date
from pathlib import Path

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
    (Path(run_path) / "txt" / f"{stem}.txt").write_text(
        "entry_time,exit_time,side,entry_price,exit_price\n"
        f"2023-03-01T09:00:00,2023-03-01T09:05:00,long,{entry_price},{exit_price}\n",
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


def test_strategy_detail_equity_curve_length_matches_rounds(tmp_path) -> None:
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
    assert payload["equity_curve"][0] == {"index": 1, "equity": 20.0}
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

    assert set(payload["kpi"]) == {"score", "profit", "pass_rate", "mdd", "pf"}
    assert payload["summary"]["score"] == payload["kpi"]["score"]
