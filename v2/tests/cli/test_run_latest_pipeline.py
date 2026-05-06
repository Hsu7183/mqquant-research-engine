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


def test_main_generates_detail_json_from_report_only_latest(tmp_path, capsys) -> None:
    base_dir = tmp_path / "runs"
    report_dir = base_dir / "latest" / "reports"
    report_dir.mkdir(parents=True)
    ranking_path = report_dir / "ranking.json"
    ranking_path.write_text(
        json.dumps(
            {
                "run_id": "latest",
                "generated_at": "2026-05-06T00:00:00+00:00",
                "summary": {
                    "total_strategies": 1,
                    "valid_strategies": 1,
                },
                "top_10": [
                    {
                        "rank": 1,
                        "strategy_name": "alpha",
                        "score": 90.0,
                        "total_test_net_profit": 120.0,
                        "pass_rate": 0.8,
                        "max_test_mdd": 10.0,
                        "average_test_pf": 1.5,
                    }
                ],
                "all_results": [
                    {
                        "rank": 1,
                        "strategy_name": "alpha",
                        "score": 90.0,
                        "total_test_net_profit": 120.0,
                        "pass_rate": 0.8,
                        "max_test_mdd": 10.0,
                        "average_test_pf": 1.5,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    main(["--base-dir", str(base_dir)])

    payload = json.loads(capsys.readouterr().out)
    detail_path = report_dir / "details" / "alpha.json"
    detail = json.loads(detail_path.read_text(encoding="utf-8"))
    assert payload["detail_json_count"] == 1
    assert payload["details_generated_from"] == "ranking_summary"
    assert detail_path.is_file()
    assert detail["strategy_name"] == "alpha"
    assert detail["equity_curve"] == []
    assert detail["weekly_pnl"] == []


def test_main_runs_txt_pipeline_for_latest_without_manifest(tmp_path, capsys) -> None:
    base_dir = tmp_path / "runs"
    txt_dir = base_dir / "latest" / "txt"
    txt_dir.mkdir(parents=True)
    _write_txt(str(base_dir / "latest"), "auto_demo")

    main(
        [
            "--base-dir",
            str(base_dir),
            "--start-date",
            date(2020, 1, 1).isoformat(),
            "--end-date",
            date(2024, 12, 31).isoformat(),
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    ranking_path = base_dir / "latest" / "reports" / "ranking.json"
    detail_path = base_dir / "latest" / "reports" / "details" / "auto_demo.json"
    detail = json.loads(detail_path.read_text(encoding="utf-8"))
    assert payload["details_generated_from"] == "txt"
    assert payload["total_strategies"] == 1
    assert payload["valid_txt"] == 1
    assert ranking_path.is_file()
    assert detail_path.is_file()
    assert detail["strategy_name"] == "auto_demo"
    assert detail["weekly_pnl"]


def test_main_raises_without_runs(tmp_path) -> None:
    base_dir = tmp_path / "runs"
    base_dir.mkdir()

    with pytest.raises(ValueError):
        main(["--base-dir", str(base_dir)])
