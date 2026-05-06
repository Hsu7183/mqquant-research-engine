from __future__ import annotations

from datetime import datetime

from mqre_v2.backtest.trade_export import export_trades_to_xs_txt
from mqre_v2.core.trades import TradeRecord
from mqre_v2.io.txt_parser import parse_xs_txt_file


def test_export_trades_to_xs_txt_can_be_read_back(tmp_path) -> None:
    output_path = tmp_path / "trades.txt"
    trades = [
        TradeRecord(
            entry_time=datetime(2026, 1, 2, 8, 49),
            exit_time=datetime(2026, 1, 2, 8, 50),
            entry_price=100.0,
            exit_price=130.0,
            direction=1,
            pnl=30.0,
        ),
        TradeRecord(
            entry_time=datetime(2026, 1, 2, 9, 1),
            exit_time=datetime(2026, 1, 2, 9, 2),
            entry_price=120.0,
            exit_price=100.0,
            direction=-1,
            pnl=20.0,
        ),
    ]

    export_trades_to_xs_txt(
        trades=trades,
        output_path=str(output_path),
        strategy_name="demo_strategy",
    )

    text = output_path.read_text(encoding="utf-8")
    assert text.splitlines()[:3] == [
        "Strategy=demo_strategy,Version=backtest",
        "20260102084900 100 新買",
        "20260102085000 130 平賣",
    ]

    parsed = parse_xs_txt_file(output_path)
    assert parsed == trades
