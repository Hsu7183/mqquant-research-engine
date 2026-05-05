from datetime import datetime

import pytest

from mqre_v2.core.trades import TradeRecord
from mqre_v2.io.txt_parser import parse_trade_txt, parse_trade_txt_file


def test_parse_trade_txt_csv_format() -> None:
    text = """entry_time,exit_time,side,entry_price,exit_price,qty,slippage_points,fee_points,pnl_points,pnl_after_cost_points
2026-01-02T09:01:00,2026-01-02T09:05:00,long,20000,20010,1,2,1,10,7
2026-01-02T09:10:00,2026-01-02T09:20:00,short,20015,20005,1,2,1,10,7
"""

    records = parse_trade_txt(text)

    assert len(records) == 2
    assert records[0] == TradeRecord(
        entry_time=datetime(2026, 1, 2, 9, 1),
        exit_time=datetime(2026, 1, 2, 9, 5),
        side="long",
        entry_price=20000.0,
        exit_price=20010.0,
        qty=1,
        slippage_points=2.0,
        fee_points=1.0,
        pnl_points=10.0,
        pnl_after_cost_points=7.0,
    )
    assert records[1].side == "short"


def test_parse_trade_txt_tab_format_with_aliases() -> None:
    text = """entry_time\texit_time\tdirection\tentry_price\texit_price\tquantity\tslippage\tfee\tpnl\tnet_pnl
2026-01-02 09:01:00\t2026-01-02 09:05:00\tbuy\t20000\t20010\t1\t2\t1\t10\t7
"""

    records = parse_trade_txt(text)

    assert len(records) == 1
    assert records[0].side == "long"
    assert records[0].pnl_after_cost_points == 7.0


def test_parse_trade_txt_whitespace_format() -> None:
    text = """entry_time exit_time side entry_price exit_price qty slippage_points fee_points pnl_points pnl_after_cost_points
2026-01-02T09:01:00 2026-01-02T09:05:00 long 20000 20010 1 2 1 10 7
"""

    records = parse_trade_txt(text)

    assert records[0].entry_time == datetime(2026, 1, 2, 9, 1)
    assert records[0].exit_time == datetime(2026, 1, 2, 9, 5)


def test_parse_trade_txt_file(tmp_path) -> None:
    path = tmp_path / "trades.txt"
    path.write_text(
        "entry_time,exit_time,side,entry_price,exit_price,qty,slippage_points,fee_points,pnl_points,pnl_after_cost_points\n"
        "2026-01-02T09:01:00,2026-01-02T09:05:00,long,20000,20010,1,2,1,10,7\n",
        encoding="utf-8",
    )

    records = parse_trade_txt_file(path)

    assert len(records) == 1
    assert records[0].exit_price == 20010.0


def test_parse_trade_txt_empty_raises() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        parse_trade_txt("")


def test_parse_trade_txt_missing_columns_raises() -> None:
    text = """entry_time,exit_time,side
2026-01-02T09:01:00,2026-01-02T09:05:00,long
"""

    with pytest.raises(ValueError, match="missing required trade columns"):
        parse_trade_txt(text)


def test_parse_trade_txt_invalid_side_raises() -> None:
    text = """entry_time,exit_time,side,entry_price,exit_price,qty,slippage_points,fee_points,pnl_points,pnl_after_cost_points
2026-01-02T09:01:00,2026-01-02T09:05:00,flat,20000,20010,1,2,1,10,7
"""

    with pytest.raises(ValueError, match="invalid side"):
        parse_trade_txt(text)
