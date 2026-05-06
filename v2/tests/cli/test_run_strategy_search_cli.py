from __future__ import annotations

import json
from pathlib import Path

from mqre_v2.cli.run_strategy_search import main


def test_run_strategy_search_cli_outputs_family_summary(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    m1_path = tmp_path / "m1.txt"
    _write_m1_fixture(m1_path)

    exit_code = main(
        [
            "--m1-path",
            str(m1_path),
            "--num-strategies",
            "12",
            "--seed",
            "42",
            "--families",
            "trend_breakout,open_range_breakout,breakdown_momentum",
            "--start-date",
            "2023-01-01",
            "--end-date",
            "2023-12-31",
        ]
    )

    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["generated_count"] == 12
    assert payload["completed_backtests"] == 12
    assert payload["non_empty_trade_files"] > 0
    assert payload["ranking_json"] == str(Path("runs") / "latest" / "reports" / "ranking.json")
    assert payload["family_counts"]
    assert "best_family" in payload
    assert len(payload["top_5"]) <= 5
    assert list((tmp_path / "runs" / "latest" / "txt").glob("*.txt"))


def _write_m1_fixture(path: Path) -> None:
    lines = []
    for minute in range(90):
        hour = 8 + (45 + minute) // 60
        min_value = (45 + minute) % 60
        open_price = 100 + minute
        close_price = open_price + (3 if minute % 3 else -1)
        high = max(open_price, close_price) + 5
        low = min(open_price, close_price) - 5
        volume = 100 + minute
        lines.append(
            f"2023/03/01 {hour:02d}:{min_value:02d} {open_price} {high} {low} {close_price} {volume}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
