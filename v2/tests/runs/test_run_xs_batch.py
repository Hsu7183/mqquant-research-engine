import json
from pathlib import Path

import pytest

from mqre_v2.runs.run_manager import (
    RunManifest,
    create_run_directory,
    load_manifest,
    write_manifest,
)
from mqre_v2.runs.run_xs_batch import generate_xs_into_run


def _write_template(path: Path) -> None:
    path.write_text(
        "Inputs: "
        "EntryBufferPts({{EntryBufferPts}}), "
        "DonBufferPts({{DonBufferPts}}), "
        "ATRStopK({{ATRStopK}}), "
        "ATRTakeProfitK({{ATRTakeProfitK}}), "
        "TimeStopBars({{TimeStopBars}});",
        encoding="utf-8",
    )


def _write_grid(path: Path) -> None:
    path.write_text(
        """
strategy_name: "0313plus"
parameters:
  EntryBufferPts: [0, 1]
  DonBufferPts: [2]
  ATRStopK: [1.0]
  ATRTakeProfitK: [2.0]
  TimeStopBars: [20]
""",
        encoding="utf-8",
    )


def _create_run_with_manifest(tmp_path) -> str:
    grid_path = tmp_path / "grid.yaml"
    template_path = tmp_path / "template.xs"
    _write_grid(grid_path)
    _write_template(template_path)

    run_path = create_run_directory(str(tmp_path / "runs"), "0313plus")
    manifest = RunManifest(
        run_id=Path(run_path).name,
        strategy_name="0313plus",
        created_at="2026-05-06T00:00:00+00:00",
        parameter_grid_path=str(grid_path),
        template_path=str(template_path),
        total_param_combinations=2,
    )
    write_manifest(run_path, manifest)
    return run_path


def test_generate_xs_into_run_writes_xs_files(tmp_path) -> None:
    run_path = _create_run_with_manifest(tmp_path)

    output_paths = generate_xs_into_run(run_path)

    assert len(output_paths) == 2
    assert all(Path(path).parent == Path(run_path) / "xs" for path in output_paths)
    assert Path(output_paths[0]).name == "0313plus_EB0_DB2_ATRS1_ATRTP2_TS20_IDX1.xs"
    assert Path(output_paths[1]).name == "0313plus_EB1_DB2_ATRS1_ATRTP2_TS20_IDX2.xs"
    assert "{{EntryBufferPts}}" not in Path(output_paths[0]).read_text(encoding="utf-8")


def test_generate_xs_into_run_updates_manifest(tmp_path) -> None:
    run_path = _create_run_with_manifest(tmp_path)

    output_paths = generate_xs_into_run(run_path)
    manifest = load_manifest(run_path)
    payload = json.loads((Path(run_path) / "manifest.json").read_text(encoding="utf-8"))

    assert manifest.xs_generated is True
    assert manifest.xs_count == len(output_paths)
    assert payload["xs_generated"] is True
    assert payload["xs_count"] == 2


def test_generate_xs_into_run_refuses_to_overwrite_existing_files(tmp_path) -> None:
    run_path = _create_run_with_manifest(tmp_path)
    generate_xs_into_run(run_path)

    with pytest.raises(ValueError):
        generate_xs_into_run(run_path)
