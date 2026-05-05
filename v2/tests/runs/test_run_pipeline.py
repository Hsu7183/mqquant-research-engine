import json
from datetime import date
from pathlib import Path

import pytest

from mqre_v2.runs.run_manager import (
    RunManifest,
    create_run_directory,
    load_manifest,
    write_manifest,
)
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


def _write_invalid_txt(run_path: str, stem: str) -> None:
    (Path(run_path) / "txt" / f"{stem}.txt").write_text(
        "not,a,trade,file\n1,2,3,4\n",
        encoding="utf-8",
    )


def test_run_pipeline_from_run_generates_ranking(tmp_path) -> None:
    run_path = _create_run(tmp_path)
    _write_xs(run_path, "alpha")
    _write_xs(run_path, "beta")
    _write_txt(run_path, "alpha", 100, 120)
    _write_txt(run_path, "beta", 100, 140)

    result = run_pipeline_from_run(
        run_path,
        start_date=date(2020, 1, 1),
        end_date=date(2023, 12, 31),
    )

    assert result.total_strategies == 2
    assert result.valid_txt == 2
    assert [item["rank"] for item in result.ranking] == [1, 2]
    assert {item["strategy_name"] for item in result.ranking} == {"alpha", "beta"}


def test_run_pipeline_from_run_writes_json_report(tmp_path) -> None:
    run_path = _create_run(tmp_path)
    _write_xs(run_path, "alpha")
    _write_txt(run_path, "alpha", 100, 120)

    result = run_pipeline_from_run(
        run_path,
        start_date=date(2020, 1, 1),
        end_date=date(2023, 12, 31),
        output_filename="custom_ranking.json",
    )
    payload = json.loads(Path(result.output_json_path).read_text(encoding="utf-8"))

    assert Path(result.output_json_path) == Path(run_path) / "reports" / "custom_ranking.json"
    assert payload["run_id"] == Path(run_path).name
    assert payload["total_strategies"] == 1
    assert payload["valid_txt"] == 1
    assert len(payload["ranking"]) == 1
    assert "generated_at" in payload


def test_run_pipeline_from_run_updates_manifest(tmp_path) -> None:
    run_path = _create_run(tmp_path)
    _write_xs(run_path, "alpha")
    _write_txt(run_path, "alpha", 100, 120)

    run_pipeline_from_run(
        run_path,
        start_date=date(2020, 1, 1),
        end_date=date(2023, 12, 31),
    )
    manifest = load_manifest(run_path)

    assert manifest.pipeline_completed is True
    assert manifest.pipeline_total == 1
    assert manifest.pipeline_valid == 1


def test_run_pipeline_from_run_raises_without_valid_txt(tmp_path) -> None:
    run_path = _create_run(tmp_path)
    _write_xs(run_path, "broken")
    _write_invalid_txt(run_path, "broken")

    with pytest.raises(ValueError):
        run_pipeline_from_run(
            run_path,
            start_date=date(2020, 1, 1),
            end_date=date(2023, 12, 31),
        )


def test_run_pipeline_from_run_sorts_ranking_desc(tmp_path) -> None:
    run_path = _create_run(tmp_path)
    _write_xs(run_path, "low")
    _write_xs(run_path, "high")
    _write_txt(run_path, "low", 100, 110)
    _write_txt(run_path, "high", 100, 150)

    result = run_pipeline_from_run(
        run_path,
        start_date=date(2020, 1, 1),
        end_date=date(2023, 12, 31),
    )
    scores = [float(item["score"]) for item in result.ranking]

    assert scores == sorted(scores, reverse=True)
    assert result.ranking[0]["strategy_name"] == "high"
