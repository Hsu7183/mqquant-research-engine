from datetime import datetime

import pytest

from mqre_v2.core.trades import ExtendedTradeRecord, TradeRecord
from mqre_v2.io.txt_parser import (
    parse_trade_txt,
    parse_trade_txt_file,
    parse_xs_txt,
    parse_xs_txt_extended,
)
from mqre_v2.validation.oos.runner import evaluate_oos_trades


def test_parse_xs_txt_csv_format_returns_core_trade_records() -> None:
    text = """entry_time,exit_time,side,entry_price,exit_price,qty,slippage_points,fee_points,pnl_points,pnl_after_cost_points
2026-01-02T09:01:00,2026-01-02T09:05:00,long,20000,20010,1,2,1,10,7
2026-01-02T09:10:00,2026-01-02T09:20:00,short,20015,20005,1,2,1,10,7
"""

    records = parse_xs_txt(text)

    assert len(records) == 2
    assert records[0] == TradeRecord(
        entry_time=datetime(2026, 1, 2, 9, 1),
        exit_time=datetime(2026, 1, 2, 9, 5),
        entry_price=20000.0,
        exit_price=20010.0,
        direction=1,
        pnl=10.0,
    )
    assert records[1].direction == -1
    assert records[1].pnl == 10.0


def test_parse_trade_txt_keeps_compatibility_alias() -> None:
    text = """entry_time,exit_time,side,entry_price,exit_price
2026-01-02T09:01:00,2026-01-02T09:05:00,long,20000,20010
"""

    records = parse_trade_txt(text)

    assert records[0].direction == 1
    assert records[0].pnl == 10.0


def test_parse_xs_txt_tab_format_with_direction_aliases() -> None:
    text = """entry_time\texit_time\tdirection\tentry_price\texit_price\tquantity\tslippage\tfee\tpnl\tnet_pnl
2026-01-02 09:01:00\t2026-01-02 09:05:00\tbuy\t20000\t20010\t1\t2\t1\t10\t7
"""

    records = parse_xs_txt(text)

    assert len(records) == 1
    assert records[0].direction == 1
    assert records[0].pnl == 10.0


def test_parse_xs_txt_whitespace_format() -> None:
    text = """entry_time exit_time side entry_price exit_price qty slippage_points fee_points pnl_points pnl_after_cost_points
2026-01-02T09:01:00 2026-01-02T09:05:00 long 20000 20010 1 2 1 10 7
"""

    records = parse_xs_txt(text)

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


def test_xs_side_mapping_to_direction() -> None:
    text = """entry_time,exit_time,side,entry_price,exit_price
2026-01-02T09:01:00,2026-01-02T09:05:00,新買,20000,20010
2026-01-02T09:10:00,2026-01-02T09:20:00,新賣,20015,20005
"""

    records = parse_xs_txt(text)

    assert [record.direction for record in records] == [1, -1]
    assert [record.pnl for record in records] == [10.0, 10.0]


def test_pnl_is_pure_price_difference_without_costs() -> None:
    text = """entry_time,exit_time,side,entry_price,exit_price,qty,slippage_points,fee_points,pnl_after_cost_points
2026-01-02T09:01:00,2026-01-02T09:05:00,新買,20000,20010,1,2,1,7
"""

    records = parse_xs_txt(text)

    assert records[0].pnl == 10.0


def test_parse_xs_txt_extended_calculates_cost_layer() -> None:
    text = """entry_time,exit_time,side,entry_price,exit_price,qty,slippage_points,fee_points,pnl_after_cost_points
2026-01-02T09:01:00,2026-01-02T09:05:00,新買,20000,20010,2,2,1,17
"""

    records = parse_xs_txt_extended(text)

    assert len(records) == 1
    assert isinstance(records[0], ExtendedTradeRecord)
    assert records[0].base.pnl == 10.0
    assert records[0].qty == 2
    assert records[0].slippage_points == 2.0
    assert records[0].fee_points == 1.0
    assert records[0].pnl_after_cost == 17.0


def test_parse_xs_txt_can_feed_oos_evaluator() -> None:
    text = """entry_time,exit_time,side,entry_price,exit_price
2026-01-02T09:01:00,2026-01-02T09:05:00,新買,20000,20010
2026-01-02T09:10:00,2026-01-02T09:20:00,新賣,20015,20005
"""

    result = evaluate_oos_trades(parse_xs_txt(text))

    assert result["total_trades"] == 2
    assert result["gross_pnl_points"] == pytest.approx(20.0)
    assert result["net_pnl_points"] == pytest.approx(20.0)
    assert result["long_trades"] == 1
    assert result["short_trades"] == 1


def test_parse_xs_txt_empty_raises() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        parse_xs_txt("")


def test_parse_xs_txt_missing_columns_raises() -> None:
    text = """entry_time,exit_time,side
2026-01-02T09:01:00,2026-01-02T09:05:00,long
"""

    with pytest.raises(ValueError, match="missing required trade columns"):
        parse_xs_txt(text)


def test_parse_xs_txt_invalid_direction_raises() -> None:
    text = """entry_time,exit_time,side,entry_price,exit_price
2026-01-02T09:01:00,2026-01-02T09:05:00,flat,20000,20010
"""

    with pytest.raises(ValueError, match="invalid direction"):
        parse_xs_txt(text)
