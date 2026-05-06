from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import mqre_v2.cli.run_strategy_search as strategy_search
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

    captured = capsys.readouterr()
    payload = _extract_json(captured.out)

    assert exit_code == 0
    assert payload["generated_count"] == 12
    assert payload["completed_backtests"] == 12
    assert payload["non_empty_trade_files"] > 0
    assert payload["ranking_json"] == str(Path("runs") / "latest" / "reports" / "ranking.json")
    assert payload["family_counts"]
    assert "best_family" in payload
    assert payload["cost"]["slippage_points_per_side"] == 2.0
    assert "策略搜尋啟動" in captured.out
    assert "策略搜尋完成" in captured.out
    assert len(payload["top_5"]) <= 5
    assert list((tmp_path / "runs" / "latest" / "txt").glob("*.txt"))


def test_run_strategy_search_workers_1_runs(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    m1_path = tmp_path / "m1.txt"
    _write_m1_fixture(m1_path)

    exit_code = main(
        [
            "--m1-path",
            str(m1_path),
            "--num-strategies",
            "5",
            "--seed",
            "42",
            "--families",
            "trend_breakout,open_range_breakout",
            "--start-date",
            "2023-01-01",
            "--end-date",
            "2023-12-31",
            "--workers",
            "1",
            "--progress-every",
            "2",
        ]
    )

    payload = _extract_json(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["workers"] == 1
    assert payload["completed_backtests"] == 5


def test_run_strategy_search_workers_2_runs_fixture(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    m1_path = tmp_path / "m1.txt"
    _write_m1_fixture(m1_path)

    exit_code = main(
        [
            "--m1-path",
            str(m1_path),
            "--num-strategies",
            "4",
            "--seed",
            "42",
            "--families",
            "trend_breakout,open_range_breakout",
            "--start-date",
            "2023-01-01",
            "--end-date",
            "2023-12-31",
            "--workers",
            "2",
            "--progress-every",
            "2",
        ]
    )

    payload = _extract_json(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["workers"] == 2
    assert payload["completed_backtests"] == 4


def test_run_strategy_search_sample_bars_limits_input(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    m1_path = tmp_path / "m1.txt"
    _write_m1_fixture(m1_path)

    main(
        [
            "--m1-path",
            str(m1_path),
            "--num-strategies",
            "3",
            "--seed",
            "42",
            "--start-date",
            "2023-01-01",
            "--end-date",
            "2023-12-31",
            "--workers",
            "1",
            "--sample-bars",
            "20",
        ]
    )

    output = capsys.readouterr().out
    payload = _extract_json(output)

    assert "快速測試模式：只使用最後 20 根 bars" in output
    assert payload["sample_bars"] == 20


def test_run_strategy_search_dry_run_generates_only(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    m1_path = tmp_path / "m1.txt"
    _write_m1_fixture(m1_path)

    main(
        [
            "--m1-path",
            str(m1_path),
            "--num-strategies",
            "6",
            "--seed",
            "42",
            "--start-date",
            "2023-01-01",
            "--end-date",
            "2023-12-31",
            "--dry-run",
        ]
    )

    payload = _extract_json(capsys.readouterr().out)

    assert payload["dry_run"] is True
    assert payload["generated_count"] == 6
    assert payload["completed_backtests"] == 0
    assert not (tmp_path / "runs" / "latest" / "txt").exists()


def test_worker_error_does_not_crash_search(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    m1_path = tmp_path / "m1.txt"
    _write_m1_fixture(m1_path)

    def broken_backtest(*args, **kwargs):
        raise RuntimeError("worker boom")

    monkeypatch.setattr(
        strategy_search,
        "backtest_generated_intraday_strategy",
        broken_backtest,
    )

    payload = strategy_search.run_strategy_search(
        m1_path=str(m1_path),
        num_strategies=3,
        seed=42,
        families=["trend_breakout"],
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        workers=1,
    )

    assert payload["completed_backtests"] == 3
    assert payload["error_count"] == 3
    assert payload["errors"][0]["error"] == "worker boom"


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


def _extract_json(output: str) -> dict:
    decoder = json.JSONDecoder()
    for index, char in enumerate(output):
        if char != "{":
            continue
        try:
            payload, _ = decoder.raw_decode(output[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and "generated_count" in payload:
            return payload
    raise AssertionError(f"no JSON payload found in output: {output}")
