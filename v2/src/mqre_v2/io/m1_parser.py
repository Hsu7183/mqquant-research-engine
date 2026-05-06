from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from mqre_v2.core.bars import BarRecord

_DATETIME_ALIASES = {
    "ts",
    "timestamp",
    "datetime",
    "date_time",
    "datatime",
    "time_stamp",
}
_DATE_ALIASES = {"date", "day", "trading_date"}
_TIME_ALIASES = {"time", "hhmm", "hhmmss"}
_OPEN_ALIASES = {"open", "o"}
_HIGH_ALIASES = {"high", "h"}
_LOW_ALIASES = {"low", "l"}
_CLOSE_ALIASES = {"close", "c"}
_VOLUME_ALIASES = {"volume", "vol", "qty", "quantity"}
def parse_m1_txt(filepath: str) -> list[BarRecord]:
    text = Path(filepath).read_text(encoding="utf-8-sig")
    lines = _meaningful_lines(text)
    if not lines:
        raise ValueError("M1 TXT cannot be empty")

    delimiter = _detect_delimiter(lines[0])
    rows = [_split_line(line, delimiter) for line in lines]
    if not rows:
        raise ValueError("M1 TXT contains no rows")

    if _looks_like_header(rows[0]):
        header = [_normalize_column(token) for token in rows[0]]
        data_rows = rows[1:]
        if not data_rows:
            raise ValueError("M1 TXT contains header but no bars")
        bars = [_row_with_header_to_bar(header, row) for row in data_rows]
    else:
        bars = [_row_without_header_to_bar(row) for row in rows]

    if not bars:
        raise ValueError("M1 TXT contains no bars")
    return bars


def _meaningful_lines(text: str) -> list[str]:
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _detect_delimiter(line: str) -> str | None:
    candidates = [",", "\t", "|", ";"]
    return max(candidates, key=line.count) if any(token in line for token in candidates) else None


def _split_line(line: str, delimiter: str | None) -> list[str]:
    if delimiter is None:
        return line.split()
    return [token.strip() for token in next(csv.reader([line], delimiter=delimiter))]


def _looks_like_header(tokens: list[str]) -> bool:
    normalized = [_normalize_column(token) for token in tokens]
    return any(token in _OPEN_ALIASES for token in normalized) and any(
        token in _CLOSE_ALIASES for token in normalized
    )


def _normalize_column(column: str) -> str:
    return column.strip().lower().replace(" ", "_").replace("-", "_")


def _row_with_header_to_bar(header: list[str], row: list[str]) -> BarRecord:
    aligned = _align_header_row(header, row)
    data = dict(zip(header, aligned, strict=True))

    open_value = _find_value(data, _OPEN_ALIASES, "open")
    high_value = _find_value(data, _HIGH_ALIASES, "high")
    low_value = _find_value(data, _LOW_ALIASES, "low")
    close_value = _find_value(data, _CLOSE_ALIASES, "close")
    volume_value = _find_optional_value(data, _VOLUME_ALIASES)

    datetime_value = _find_optional_value(data, _DATETIME_ALIASES)
    if datetime_value is not None:
        ts = _parse_datetime(datetime_value)
    else:
        date_value = _find_value(data, _DATE_ALIASES, "date")
        time_value = _find_value(data, _TIME_ALIASES, "time")
        ts = _parse_datetime(f"{date_value} {time_value}")

    return BarRecord(
        ts=ts,
        open=_parse_float(open_value, "open"),
        high=_parse_float(high_value, "high"),
        low=_parse_float(low_value, "low"),
        close=_parse_float(close_value, "close"),
        volume=_parse_volume(volume_value),
    )


def _align_header_row(header: list[str], row: list[str]) -> list[str]:
    if len(row) == len(header):
        return row

    if len(row) == len(header) + 1 and header and header[0] in _DATETIME_ALIASES:
        return [f"{row[0]} {row[1]}"] + row[2:]

    raise ValueError(
        f"M1 row has {len(row)} columns but header has {len(header)} columns: {row}"
    )


def _row_without_header_to_bar(row: list[str]) -> BarRecord:
    if len(row) >= 6:
        try:
            ts = _parse_datetime(f"{row[0]} {row[1]}")
        except ValueError:
            ts = _parse_datetime(row[0])
            offset = 1
        else:
            offset = 2
    elif len(row) >= 5:
        ts = _parse_datetime(row[0])
        offset = 1
    else:
        raise ValueError(f"M1 row must contain datetime and OHLC columns: {row}")

    return BarRecord(
        ts=ts,
        open=_parse_float(row[offset], "open"),
        high=_parse_float(row[offset + 1], "high"),
        low=_parse_float(row[offset + 2], "low"),
        close=_parse_float(row[offset + 3], "close"),
        volume=_parse_volume(row[offset + 4] if len(row) > offset + 4 else None),
    )


def _find_value(data: dict[str, str], aliases: set[str], name: str) -> str:
    value = _find_optional_value(data, aliases)
    if value is None:
        raise ValueError(f"missing required M1 column: {name}")
    return value


def _find_optional_value(data: dict[str, str], aliases: set[str]) -> str | None:
    for alias in aliases:
        if alias in data and data[alias] != "":
            return data[alias]
    return None


def _parse_datetime(value: str) -> datetime:
    cleaned = value.strip()
    compact = cleaned.replace(" ", "")
    for fmt in (
        "%Y%m%d%H%M%S",
        "%Y%m%d%H%M",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            pass
        try:
            return datetime.strptime(compact, fmt)
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(cleaned)
    except ValueError as exc:
        raise ValueError(f"invalid M1 datetime: {value}") from exc


def _parse_float(value: str, column: str) -> float:
    try:
        return float(value.replace(",", ""))
    except ValueError as exc:
        raise ValueError(f"invalid M1 float for {column}: {value}") from exc


def _parse_volume(value: str | None) -> float | int | None:
    if value is None:
        return None
    number = _parse_float(value, "volume")
    return int(number) if number.is_integer() else number


__all__ = ["parse_m1_txt"]
