import json
import re

from mqre_v2.runs.run_manager import (
    RunManifest,
    create_run_directory,
    load_manifest,
    write_manifest,
)


def test_create_run_directory_creates_expected_structure(tmp_path) -> None:
    run_path = create_run_directory(str(tmp_path / "runs"), "alpha")
    run_dir = tmp_path / "runs" / re.match(r".*[\\/](.+)$", run_path).group(1)

    assert run_dir.exists()
    assert re.match(r"\d{8}_alpha_batch001", run_dir.name)
    assert (run_dir / "xs").is_dir()
    assert (run_dir / "txt").is_dir()
    assert (run_dir / "reports").is_dir()
    assert (run_dir / "logs").is_dir()


def test_create_run_directory_increments_run_id(tmp_path) -> None:
    base_dir = tmp_path / "runs"

    first_path = create_run_directory(str(base_dir), "alpha")
    second_path = create_run_directory(str(base_dir), "alpha")

    assert first_path.endswith("alpha_batch001")
    assert second_path.endswith("alpha_batch002")


def test_write_and_load_manifest(tmp_path) -> None:
    run_path = create_run_directory(str(tmp_path / "runs"), "alpha")
    run_id = run_path.split("\\")[-1].split("/")[-1]
    manifest = RunManifest(
        run_id=run_id,
        strategy_name="alpha",
        created_at="2026-05-06T00:00:00+00:00",
        parameter_grid_path="configs/parameter_grid_0313.yaml",
        template_path="templates/xs/0313plus_template.xs",
        total_param_combinations=324,
        notes="v2 run container",
    )

    write_manifest(run_path, manifest)
    loaded = load_manifest(run_path)

    assert (tmp_path / "runs" / run_id / "manifest.json").is_file()
    assert loaded == manifest


def test_manifest_json_contains_expected_payload(tmp_path) -> None:
    run_path = create_run_directory(str(tmp_path / "runs"), "alpha")
    run_id = run_path.split("\\")[-1].split("/")[-1]
    manifest = RunManifest(
        run_id=run_id,
        strategy_name="alpha",
        created_at="2026-05-06T00:00:00+00:00",
        parameter_grid_path="grid.yaml",
        template_path="template.xs",
        total_param_combinations=2,
    )

    write_manifest(run_path, manifest)
    payload = json.loads((tmp_path / "runs" / run_id / "manifest.json").read_text())

    assert payload["run_id"] == run_id
    assert payload["strategy_name"] == "alpha"
    assert payload["total_param_combinations"] == 2
