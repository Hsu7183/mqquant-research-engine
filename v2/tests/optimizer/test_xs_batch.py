from __future__ import annotations

from pathlib import Path

from mqre_v2.optimizer import generate_xs_batch


def test_generate_xs_batch_creates_multiple_files(tmp_path: Path) -> None:
    template_path = _write_template(tmp_path)
    grid_path = _write_grid(tmp_path)
    output_dir = tmp_path / "nested" / "xs"

    paths = generate_xs_batch(str(template_path), str(grid_path), str(output_dir))

    assert len(paths) == 4
    assert output_dir.is_dir()
    assert all(Path(path).is_file() for path in paths)


def test_generate_xs_batch_file_count_matches_grid(tmp_path: Path) -> None:
    paths = generate_xs_batch(
        str(_write_template(tmp_path)),
        str(_write_grid(tmp_path)),
        str(tmp_path / "xs"),
    )

    assert len(paths) == 4


def test_generate_xs_batch_filename_contains_params(tmp_path: Path) -> None:
    paths = generate_xs_batch(
        str(_write_template(tmp_path)),
        str(_write_grid(tmp_path)),
        str(tmp_path / "xs"),
    )
    filenames = [Path(path).name for path in paths]

    assert "demo_EB0_DB2_ATRS1_ATRTP2_TS20_IDX1.xs" in filenames
    assert any("ATRS1p5" in filename for filename in filenames)
    assert all(" " not in filename for filename in filenames)


def test_generate_xs_batch_creates_missing_output_dir(tmp_path: Path) -> None:
    output_dir = tmp_path / "missing" / "xs"

    generate_xs_batch(
        str(_write_template(tmp_path)),
        str(_write_grid(tmp_path)),
        str(output_dir),
    )

    assert output_dir.exists()


def test_generate_xs_batch_returns_all_paths(tmp_path: Path) -> None:
    paths = generate_xs_batch(
        str(_write_template(tmp_path)),
        str(_write_grid(tmp_path)),
        str(tmp_path / "xs"),
    )

    assert isinstance(paths, list)
    assert len(paths) == 4


def _write_template(tmp_path: Path) -> Path:
    template_path = tmp_path / "template.xs"
    template_path.write_text(
        "\n".join(
            [
                "EntryBufferPts={{EntryBufferPts}}",
                "DonBufferPts={{DonBufferPts}}",
                "ATRStopK={{ATRStopK}}",
                "ATRTakeProfitK={{ATRTakeProfitK}}",
                "TimeStopBars={{TimeStopBars}}",
            ]
        ),
        encoding="utf-8",
    )
    return template_path


def _write_grid(tmp_path: Path) -> Path:
    grid_path = tmp_path / "grid.yaml"
    grid_path.write_text(
        "\n".join(
            [
                'strategy_name: "demo"',
                "parameters:",
                "  EntryBufferPts: [0, 1]",
                "  DonBufferPts: [2]",
                "  ATRStopK: [1.0, 1.5]",
                "  ATRTakeProfitK: [2.0]",
                "  TimeStopBars: [20]",
            ]
        ),
        encoding="utf-8",
    )
    return grid_path
