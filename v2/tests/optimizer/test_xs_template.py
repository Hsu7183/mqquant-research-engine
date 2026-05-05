import pytest

from mqre_v2.optimizer.xs_template import render_xs_template, write_rendered_xs


def _params() -> dict:
    return {
        "EntryBufferPts": 1,
        "DonBufferPts": 2,
        "ATRStopK": 1.5,
        "ATRTakeProfitK": 2.0,
        "TrailStartPctAnchor": 0.5,
        "TrailGivePctAnchor": 0.3,
        "TimeStopBars": 30,
        "AnchorBackPct": 0.2,
    }


def _write_template(path) -> None:
    path.write_text(
        "Inputs: EntryBufferPts({{EntryBufferPts}}), ATRStopK({{ATRStopK}});",
        encoding="utf-8",
    )


def test_render_xs_template() -> None:
    rendered = render_xs_template("templates/xs/0313plus_template.xs", _params())

    assert "{{EntryBufferPts}}" not in rendered
    assert "EntryBufferPts(1)" in rendered
    assert "ATRStopK(1.5)" in rendered
    assert "AnchorBackPct(0.2)" in rendered


def test_render_xs_template_missing_param_raises(tmp_path) -> None:
    template_path = tmp_path / "template.xs"
    _write_template(template_path)

    with pytest.raises(ValueError, match="EntryBufferPts"):
        render_xs_template(str(template_path), {"ATRStopK": 1.5})


def test_render_xs_template_ignores_extra_params(tmp_path) -> None:
    template_path = tmp_path / "template.xs"
    _write_template(template_path)

    rendered = render_xs_template(
        str(template_path),
        {"EntryBufferPts": 1, "ATRStopK": 1.5, "ExtraParam": 999},
    )

    assert "EntryBufferPts(1)" in rendered
    assert "ATRStopK(1.5)" in rendered
    assert "ExtraParam" not in rendered


def test_write_rendered_xs(tmp_path) -> None:
    template_path = tmp_path / "template.xs"
    output_path = tmp_path / "out" / "rendered.xs"
    _write_template(template_path)

    write_rendered_xs(
        str(template_path),
        {"EntryBufferPts": 1, "ATRStopK": 1.5},
        str(output_path),
    )

    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == (
        "Inputs: EntryBufferPts(1), ATRStopK(1.5);"
    )
