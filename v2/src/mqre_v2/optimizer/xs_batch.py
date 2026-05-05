from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from mqre_v2.optimizer.parameter_grid import expand_parameter_grid, load_parameter_grid
from mqre_v2.optimizer.xs_template import render_xs_template

FILENAME_PARAM_NAMES = (
    "EntryBufferPts",
    "DonBufferPts",
    "ATRStopK",
    "ATRTakeProfitK",
    "TimeStopBars",
)


def generate_xs_batch(
    template_path: str,
    parameter_grid_path: str,
    output_dir: str,
) -> list[str]:
    grid = load_parameter_grid(parameter_grid_path)
    parameter_sets = expand_parameter_grid(grid)
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    output_paths: list[str] = []
    for index, params in enumerate(parameter_sets, start=1):
        rendered = render_xs_template(template_path, params)
        filename = _build_xs_filename(grid.strategy_name, params, index)
        output_path = target_dir / filename
        output_path.write_text(rendered, encoding="utf-8")
        output_paths.append(str(output_path))

    return output_paths


def _build_xs_filename(strategy_name: str, params: dict[str, Any], index: int) -> str:
    missing = [name for name in FILENAME_PARAM_NAMES if name not in params]
    if missing:
        raise ValueError(f"missing filename parameters: {missing}")

    parts = [
        _filename_token(strategy_name),
        f"EB{_format_value(params['EntryBufferPts'])}",
        f"DB{_format_value(params['DonBufferPts'])}",
        f"ATRS{_format_value(params['ATRStopK'])}",
        f"ATRTP{_format_value(params['ATRTakeProfitK'])}",
        f"TS{_format_value(params['TimeStopBars'])}",
        f"IDX{index}",
    ]
    return "_".join(parts) + ".xs"


def _format_value(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        text = str(int(value))
    else:
        text = str(value).strip()
        if text.endswith(".0"):
            text = text[:-2]

    text = text.replace("-", "m").replace(".", "p")
    return _filename_token(text)


def _filename_token(value: Any) -> str:
    text = str(value).strip().replace(" ", "")
    text = text.replace("/", "-").replace("\\", "-").replace(":", "-")
    return re.sub(r"[^A-Za-z0-9_.-]", "", text)
