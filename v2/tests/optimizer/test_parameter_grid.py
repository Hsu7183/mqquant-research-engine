import pytest

from mqre_v2.optimizer.parameter_grid import (
    ParameterGrid,
    expand_parameter_grid,
    load_parameter_grid,
)


def _write_yaml(path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_load_parameter_grid_from_yaml(tmp_path) -> None:
    path = tmp_path / "grid.yaml"
    _write_yaml(
        path,
        """
strategy_name: demo
parameters:
  A: [1, 2]
  B: [x, y]
""",
    )

    grid = load_parameter_grid(str(path))

    assert isinstance(grid, ParameterGrid)
    assert grid.strategy_name == "demo"
    assert grid.parameters == {"A": [1, 2], "B": ["x", "y"]}


def test_expand_parameter_grid() -> None:
    grid = ParameterGrid(
        strategy_name="demo",
        parameters={"A": [1, 2], "B": ["x", "y"]},
    )

    combos = expand_parameter_grid(grid)

    assert combos == [
        {"A": 1, "B": "x"},
        {"A": 1, "B": "y"},
        {"A": 2, "B": "x"},
        {"A": 2, "B": "y"},
    ]


def test_expand_parameter_grid_combination_count() -> None:
    grid = ParameterGrid(
        strategy_name="demo",
        parameters={"A": [1, 2, 3], "B": [10, 20], "C": [True, False]},
    )

    combos = expand_parameter_grid(grid)

    assert len(combos) == 12


def test_missing_strategy_name_raises(tmp_path) -> None:
    path = tmp_path / "grid.yaml"
    _write_yaml(
        path,
        """
parameters:
  A: [1]
""",
    )

    with pytest.raises(ValueError, match="strategy_name"):
        load_parameter_grid(str(path))


def test_empty_parameters_raises(tmp_path) -> None:
    path = tmp_path / "grid.yaml"
    _write_yaml(
        path,
        """
strategy_name: demo
parameters: {}
""",
    )

    with pytest.raises(ValueError, match="parameters"):
        load_parameter_grid(str(path))


def test_parameter_value_not_list_raises(tmp_path) -> None:
    path = tmp_path / "grid.yaml"
    _write_yaml(
        path,
        """
strategy_name: demo
parameters:
  A: 1
""",
    )

    with pytest.raises(ValueError, match="must be a list"):
        load_parameter_grid(str(path))


def test_empty_parameter_list_raises(tmp_path) -> None:
    path = tmp_path / "grid.yaml"
    _write_yaml(
        path,
        """
strategy_name: demo
parameters:
  A: []
""",
    )

    with pytest.raises(ValueError, match="cannot be empty"):
        load_parameter_grid(str(path))
