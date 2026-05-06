from datetime import datetime

import pytest

from mqre_v2.core import BarRecord
from mqre_v2.io import parse_m1_txt


def _write_m1(tmp_path, text: str) -> str:
    path = tmp_path / "m1.txt"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_parse_m1_txt_with_header(tmp_path) -> None:
    path = _write_m1(
        tmp_path,
        "date,time,open,high,low,close,volume\n"
        "2024/01/02,09:00,100,105,99,104,10\n",
    )

    bars = parse_m1_txt(path)

    assert bars == [
        BarRecord(
            ts=datetime(2024, 1, 2, 9, 0),
            open=100.0,
            high=105.0,
            low=99.0,
            close=104.0,
            volume=10,
        )
    ]


def test_parse_m1_txt_without_header(tmp_path) -> None:
    path = _write_m1(tmp_path, "20200102 084500 12044 12047 12040 12047\n")

    bars = parse_m1_txt(path)

    assert bars[0] == BarRecord(
        ts=datetime(2020, 1, 2, 8, 45),
        open=12044.0,
        high=12047.0,
        low=12040.0,
        close=12047.0,
    )


def test_parse_m1_txt_comma_delimited(tmp_path) -> None:
    path = _write_m1(tmp_path, "ts,open,high,low,close\n20240102090000,1,2,0.5,1.5\n")

    bars = parse_m1_txt(path)

    assert bars[0].ts == datetime(2024, 1, 2, 9, 0)
    assert bars[0].close == 1.5


def test_parse_m1_txt_space_delimited(tmp_path) -> None:
    path = _write_m1(tmp_path, "2024-01-02 09:00 100 101 99 100.5\n")

    bars = parse_m1_txt(path)

    assert bars[0].ts == datetime(2024, 1, 2, 9, 0)
    assert bars[0].open == 100.0


def test_parse_m1_txt_tab_delimited(tmp_path) -> None:
    path = _write_m1(
        tmp_path,
        "datetime\topen\thigh\tlow\tclose\n"
        "2024-01-02 09:00\t100\t101\t99\t100.5\n",
    )

    bars = parse_m1_txt(path)

    assert bars[0].ts == datetime(2024, 1, 2, 9, 0)
    assert bars[0].high == 101.0


def test_parse_m1_txt_yyyymmddhhmmss(tmp_path) -> None:
    path = _write_m1(tmp_path, "20240102090000 100 101 99 100.5\n")

    bars = parse_m1_txt(path)

    assert bars[0].ts == datetime(2024, 1, 2, 9, 0)


def test_parse_m1_txt_yyyymmddhhmmss_with_volume(tmp_path) -> None:
    path = _write_m1(tmp_path, "20240102090000 100 101 99 100.5 20\n")

    bars = parse_m1_txt(path)

    assert bars[0].ts == datetime(2024, 1, 2, 9, 0)
    assert bars[0].volume == 20


def test_parse_m1_txt_slash_datetime(tmp_path) -> None:
    path = _write_m1(tmp_path, "datetime open high low close\n2024/01/02 09:00 100 101 99 100.5\n")

    bars = parse_m1_txt(path)

    assert bars[0].ts == datetime(2024, 1, 2, 9, 0)
    assert bars[0].low == 99.0


def test_parse_m1_txt_missing_ohlc_raises(tmp_path) -> None:
    path = _write_m1(tmp_path, "date,time,open,high,close\n2024/01/02,09:00,100,101,100.5\n")

    with pytest.raises(ValueError, match="missing required M1 column: low"):
        parse_m1_txt(path)
