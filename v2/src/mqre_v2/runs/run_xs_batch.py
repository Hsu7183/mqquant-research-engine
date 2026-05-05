from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from mqre_v2.optimizer.parameter_grid import expand_parameter_grid, load_parameter_grid
from mqre_v2.optimizer.xs_batch import _build_xs_filename
from mqre_v2.optimizer.xs_template import render_xs_template
from mqre_v2.runs.run_manager import load_manifest, write_manifest


def generate_xs_into_run(run_path: str, overwrite: bool = False) -> list[str]:
    manifest = load_manifest(run_path)
    xs_dir = Path(run_path) / "xs"
    xs_dir.mkdir(parents=True, exist_ok=True)

    existing_files = [path for path in xs_dir.iterdir() if path.is_file()]
    if existing_files and not overwrite:
        raise ValueError("xs folder is not empty; refusing to overwrite")

    grid = load_parameter_grid(manifest.parameter_grid_path)
    parameter_sets = expand_parameter_grid(grid)

    output_paths: list[str] = []
    for index, params in enumerate(parameter_sets, start=1):
        rendered = render_xs_template(manifest.template_path, params)
        filename = _build_xs_filename(manifest.strategy_name, params, index)
        output_path = xs_dir / filename
        output_path.write_text(rendered, encoding="utf-8")
        output_paths.append(str(output_path))

    updated_manifest = replace(
        manifest,
        xs_generated=True,
        xs_count=len(output_paths),
    )
    write_manifest(run_path, updated_manifest)

    return output_paths
