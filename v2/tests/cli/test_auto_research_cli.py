from __future__ import annotations

import json
from pathlib import Path

from mqre_v2.cli.auto_research import main


def test_auto_research_cli_outputs_json(tmp_path: Path, capsys) -> None:
    _write_sample_txt(tmp_path / "baseline.txt")
    _write_challenger_txt(tmp_path / "challenger.txt")

    exit_code = main(
        [
            "--txt-folder",
            str(tmp_path),
            "--start-date",
            "2020-01-01",
            "--end-date",
            "2024-12-31",
            "--output-json-path",
            str(tmp_path / "auto_research.json"),
            "--forward-log-path",
            str(tmp_path / "forward_test_log.csv"),
            "--top-n",
            "2",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["total_strategies"] == 2
    assert len(payload["top_n"]) == 2
    assert "top1" in payload


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
