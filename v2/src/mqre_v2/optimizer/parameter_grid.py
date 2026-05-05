from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ParameterGrid:
    strategy_name: str
    parameters: dict[str, list]


def load_parameter_grid(path: str) -> ParameterGrid:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("parameter grid yaml must be a mapping")

    strategy_name = data.get("strategy_name")
    if not strategy_name:
        raise ValueError("strategy_name is required")

    parameters = data.get("parameters")
    _validate_parameters(parameters)

    return ParameterGrid(
        strategy_name=str(strategy_name),
        parameters=dict(parameters),
    )


def expand_parameter_grid(grid: ParameterGrid) -> list[dict]:
    parameter_names = list(grid.parameters)
    value_lists = [grid.parameters[name] for name in parameter_names]
    return [
        dict(zip(parameter_names, values, strict=True))
        for values in product(*value_lists)
    ]


def _validate_parameters(parameters: Any) -> None:
    if not isinstance(parameters, dict) or not parameters:
        raise ValueError("parameters must be a non-empty mapping")

    for name, values in parameters.items():
        if not isinstance(values, list):
            raise ValueError(f"parameter {name} must be a list")
        if not values:
            raise ValueError(f"parameter {name} cannot be empty")
