import json
from datetime import date
from pathlib import Path

import pytest

from mqre_v2.cli.run_latest_pipeline import get_latest_run, main
from mqre_v2.runs.run_manager import RunManifest, create_run_directory, write_manifest


def _create_run(base_dir: Path, strategy_name: str) -> str:
    run_path = create_run_directory(str(base_dir), strategy_name)
    write_manifest(
        run_path,
        RunManifest(
            run_id=Path(run_path).name,
            strategy_name=strategy_name,
            created_at="2026-05-06T00:00:00+00:00",
            parameter_grid_path="grid.yaml",
            template_path="template.xs",
            total_param_combinations=1,
        ),
    )
    return run_path


def _write_xs(run_path: str, stem: str) -> None:
    (Path(run_path) / "xs" / f"{stem}.xs").write_text("value1;", encoding="utf-8")


def _write_txt(run_path: str, stem: str) -> None:
    (Path(run_path) / "txt" / f"{stem}.txt").write_text(
        "entry_time,exit_time,side,entry_price,exit_price\n"
        "2023-03-01T09:00:00,2023-03-01T09:05:00,long,100,120\n",
        encoding="utf-8",
    )


def test_get_latest_run_returns_latest_by_folder_name(tmp_path) -> None:
    base_dir = tmp_path / "runs"
    first = _create_run(base_dir, "alpha")
    second = _create_run(base_dir, "beta")

    assert get_latest_run(str(base_dir)) == second
    assert first != second


def test_get_latest_run_raises_when_no_run_exists(tmp_path) -> None:
    base_dir = tmp_path / "runs"
    base_dir.mkdir()

    with pytest.raises(ValueError):
        get_latest_run(str(base_dir))


def test_main_runs_pipeline_and_outputs_json(tmp_path, capsys) -> None:
    base_dir = tmp_path / "runs"
    run_path = _create_run(base_dir, "alpha")
    _write_xs(run_path, "alpha")
    _write_txt(run_path, "alpha")

    main(
        [
            "--base-dir",
            str(base_dir),
            "--start-date",
            date(2020, 1, 1).isoformat(),
            "--end-date",
            date(2023, 12, 31).isoformat(),
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["run_id"] == Path(run_path).name
    assert payload["total_strategies"] == 1
    assert payload["valid_txt"] == 1
    assert payload["top_10"][0]["strategy_name"] == "alpha"
    assert Path(payload["output_json_path"]).is_file()


def test_main_raises_without_runs(tmp_path) -> None:
    base_dir = tmp_path / "runs"
    base_dir.mkdir()

    with pytest.raises(ValueError):
        main(["--base-dir", str(base_dir)])
