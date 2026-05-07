from __future__ import annotations

import json

from mqre_v2.cli.backtest_m1 import main
from mqre_v2.io.txt_parser import parse_xs_txt_file


def test_backtest_m1_cli_writes_trade_txt(tmp_path, capsys) -> None:
    m1_path = tmp_path / "m1.txt"
    output_path = tmp_path / "trades.txt"
    m1_path.write_text(
        "\n".join(
            [
                "2026/01/02 08:48 100 115 100 115",
                "2026/01/02 08:49 120 120 120 120",
                "2026/01/02 08:50 150 150 150 150",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--m1-path",
            str(m1_path),
            "--output-trade-txt",
            str(output_path),
            "--strategy-name",
            "cli_demo",
            "--entry-buffer",
            "10",
            "--take-profit",
            "20",
            "--stop-loss",
            "50",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["strategy_name"] == "cli_demo"
    assert payload["bars_count"] == 3
    assert payload["trades_count"] == 1
    assert payload["total_pnl"] == 30.0
    assert output_path.is_file()
    assert parse_xs_txt_file(output_path)[0].pnl == 30.0


def test_backtest_m1_cli_can_run_1001plus(tmp_path, capsys) -> None:
    m1_path = tmp_path / "m1_1001plus.txt"
    output_path = tmp_path / "trades_1001plus.txt"
    rows = []
    for minute in range(24):
        price = 100 + minute
        rows.append(
            f"2026/01/02 09:{minute:02d} {price} {price + 2} {price - 1} {price + 1} 100"
        )
    rows.append("2026/01/02 09:24 200 200 200 200 100")
    m1_path.write_text(
        "\n".join(rows)
        + "\n",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--m1-path",
            str(m1_path),
            "--output-trade-txt",
            str(output_path),
            "--strategy-name",
            "1001plus_cli",
            "--strategy",
            "1001plus",
        ]
    )

    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["strategy"] == "1001plus"
    assert payload["trades_count"] == 1
    assert output_path.is_file()
    assert parse_xs_txt_file(output_path)[0].entry_price > 0
