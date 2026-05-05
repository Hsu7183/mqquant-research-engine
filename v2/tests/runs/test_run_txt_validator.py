import json
from pathlib import Path

from mqre_v2.runs.run_manager import (
    RunManifest,
    create_run_directory,
    load_manifest,
    write_manifest,
)
from mqre_v2.runs.run_txt_validator import validate_run_txt


def _write_manifest(run_path: str) -> None:
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


def _write_xs(run_path: str, stem: str) -> None:
    (Path(run_path) / "xs" / f"{stem}.xs").write_text("value1;", encoding="utf-8")


def _write_valid_txt(run_path: str, stem: str) -> None:
    (Path(run_path) / "txt" / f"{stem}.txt").write_text(
        "entry_time,exit_time,side,entry_price,exit_price\n"
        "2023-03-01T09:00:00,2023-03-01T09:05:00,long,100,120\n",
        encoding="utf-8",
    )


def _write_invalid_txt(run_path: str, stem: str) -> None:
    (Path(run_path) / "txt" / f"{stem}.txt").write_text(
        "not,a,trade,file\n1,2,3,4\n",
        encoding="utf-8",
    )


def _create_run(tmp_path) -> str:
    run_path = create_run_directory(str(tmp_path / "runs"), "0313plus")
    _write_manifest(run_path)
    return run_path


def test_validate_run_txt_all_matched(tmp_path) -> None:
    run_path = _create_run(tmp_path)
    _write_xs(run_path, "alpha")
    _write_xs(run_path, "beta")
    _write_valid_txt(run_path, "alpha")
    _write_valid_txt(run_path, "beta")

    result = validate_run_txt(run_path)

    assert result.total_xs == 2
    assert result.total_txt == 2
    assert result.matched == 2
    assert result.missing_txt == []
    assert result.extra_txt == []
    assert result.parse_failed == []
    assert result.valid_txt == ["alpha.txt", "beta.txt"]


def test_validate_run_txt_reports_missing_txt(tmp_path) -> None:
    run_path = _create_run(tmp_path)
    _write_xs(run_path, "alpha")
    _write_xs(run_path, "beta")
    _write_valid_txt(run_path, "alpha")

    result = validate_run_txt(run_path)

    assert result.matched == 1
    assert result.missing_txt == ["beta.txt"]
    assert result.valid_txt == ["alpha.txt"]


def test_validate_run_txt_reports_extra_txt(tmp_path) -> None:
    run_path = _create_run(tmp_path)
    _write_xs(run_path, "alpha")
    _write_valid_txt(run_path, "alpha")
    _write_valid_txt(run_path, "extra")

    result = validate_run_txt(run_path)

    assert result.total_txt == 2
    assert result.extra_txt == ["extra.txt"]
    assert result.missing_txt == []


def test_validate_run_txt_reports_parse_failed(tmp_path) -> None:
    run_path = _create_run(tmp_path)
    _write_xs(run_path, "alpha")
    _write_xs(run_path, "broken")
    _write_valid_txt(run_path, "alpha")
    _write_invalid_txt(run_path, "broken")

    result = validate_run_txt(run_path)

    assert result.matched == 2
    assert result.valid_txt == ["alpha.txt"]
    assert result.parse_failed == ["broken.txt"]


def test_validate_run_txt_updates_manifest(tmp_path) -> None:
    run_path = _create_run(tmp_path)
    _write_xs(run_path, "alpha")
    _write_xs(run_path, "missing")
    _write_valid_txt(run_path, "alpha")

    validate_run_txt(run_path)
    manifest = load_manifest(run_path)
    payload = json.loads((Path(run_path) / "manifest.json").read_text(encoding="utf-8"))

    assert manifest.txt_validated is True
    assert manifest.txt_matched == 1
    assert manifest.txt_missing == 1
    assert manifest.txt_parse_failed == 0
    assert payload["txt_validated"] is True
    assert payload["txt_matched"] == 1
    assert payload["txt_missing"] == 1
    assert payload["txt_parse_failed"] == 0
