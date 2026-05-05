from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from mqre_v2.automation.auto_research import AutoResearchConfig, run_auto_research
from mqre_v2.forward.forward_log import read_forward_records


def test_run_auto_research_runs_multiple_txts(tmp_path: Path) -> None:
    _write_sample_txt(tmp_path / "baseline.txt")
    _write_challenger_txt(tmp_path / "challenger.txt")

    summary = run_auto_research(_config(tmp_path))

    assert summary["total_strategies"] == 2
    assert len(summary["top_n"]) == 2
    assert summary["top1"]["strategy_name"] in {"baseline", "challenger"}


def test_run_auto_research_outputs_json(tmp_path: Path) -> None:
    _write_sample_txt(tmp_path / "baseline.txt")
    _write_challenger_txt(tmp_path / "challenger.txt")
    config = _config(tmp_path)

    run_auto_research(config)

    payload = json.loads(Path(config.output_json_path).read_text(encoding="utf-8"))
    assert payload["total_strategies"] == 2
    assert len(payload["all_results"]) == 2


def test_run_auto_research_adds_top1_to_forward_log(tmp_path: Path) -> None:
    _write_sample_txt(tmp_path / "baseline.txt")
    _write_challenger_txt(tmp_path / "challenger.txt")
    config = _config(tmp_path)

    summary = run_auto_research(config)
    records = read_forward_records(config.forward_log_path)

    assert summary["added_to_forward"] is True
    assert len(records) == 1
    assert records[0].strategy_name == summary["top1"]["strategy_name"]
    assert records[0].status == "candidate"


def test_run_auto_research_duplicate_top1_is_skipped(tmp_path: Path) -> None:
    _write_sample_txt(tmp_path / "baseline.txt")
    _write_challenger_txt(tmp_path / "challenger.txt")
    config = _config(tmp_path)

    first = run_auto_research(config)
    second = run_auto_research(config)
    records = read_forward_records(config.forward_log_path)

    assert first["added_to_forward"] is True
    assert second["added_to_forward"] is False
    assert second["notes"] == "duplicate skipped"
    assert len(records) == 1


def test_run_auto_research_no_strategy_results_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        run_auto_research(_config(tmp_path))


def _config(folder: Path) -> AutoResearchConfig:
    return AutoResearchConfig(
        txt_folder=str(folder),
        start_date=date(2020, 1, 1),
        end_date=date(2024, 12, 31),
        output_json_path=str(folder / "auto_research.json"),
        forward_log_path=str(folder / "forward_test_log.csv"),
        top_n=10,
        auto_add_top1_to_forward=True,
        min_score_to_forward=0.0,
    )


def _write_sample_txt(path: Path) -> None:
    path.write_text(
        "entry_time,exit_time,side,entry_price,exit_price\n"
        "2023-03-01T09:00:00,2023-03-01T09:05:00,long,100,120\n"
        "2023-03-02T09:00:00,2023-03-02T09:05:00,long,120,110\n",
        encoding="utf-8",
    )


def _write_challenger_txt(path: Path) -> None:
    path.write_text(
        "entry_time,exit_time,side,entry_price,exit_price\n"
        "2023-03-01T09:00:00,2023-03-01T09:05:00,long,100,140\n"
        "2023-03-02T09:00:00,2023-03-02T09:05:00,long,140,130\n",
        encoding="utf-8",
    )
