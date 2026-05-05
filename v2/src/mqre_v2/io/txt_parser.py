from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable

from mqre_v2.core.trades import TradeRecord, TradeSide


_COLUMN_ALIASES = {
    "entry_time": "entry_time",
    "entrytime": "entry_time",
    "entry_datetime": "entry_time",
    "entry_date_time": "entry_time",
    "exit_time": "exit_time",
    "exittime": "exit_time",
    "exit_datetime": "exit_time",
    "exit_date_time": "exit_time",
    "side": "side",
    "direction": "side",
    "position": "side",
    "entry_price": "entry_price",
    "entryprice": "entry_price",
    "exit_price": "exit_price",
    "exitprice": "exit_price",
    "qty": "qty",
    "quantity": "qty",
    "contracts": "qty",
    "slippage_points": "slippage_points",
    "slippage": "slippage_points",
    "fee_points": "fee_points",
    "fee": "fee_points",
    "pnl_points": "pnl_points",
    "pnl": "pnl_points",
    "profit": "pnl_points",
    "pnl_after_cost_points": "pnl_after_cost_points",
    "pnl_after_cost": "pnl_after_cost_points",
    "net_pnl": "pnl_after_cost_points",
}

_REQUIRED_COLUMNS = {
    "entry_time",
    "exit_time",
    "side",
    "entry_price",
    "exit_price",
    "qty",
    "slippage_points",
    "fee_points",
    "pnl_points",
    "pnl_after_cost_points",
}


def parse_trade_txt(text: str) -> list[TradeRecord]:
    rows = list(_parse_rows(text))
    if not rows:
        raise ValueError("trade txt cannot be empty")

    records = [_row_to_trade_record(row) for row in rows]
    if not records:
        raise ValueError("trade txt contains no trade records")

    return records


def parse_trade_txt_file(path: str | Path, encoding: str = "utf-8-sig") -> list[TradeRecord]:
    return parse_trade_txt(Path(path).read_text(encoding=encoding))


def _parse_rows(text: str) -> Iterable[dict[str, str]]:
    lines = _meaningful_lines(text)
    if not lines:
        return []

    delimiter = _detect_delimiter(lines[0])
    if delimiter is None:
        return _parse_whitespace_rows(lines)

    return csv.DictReader(lines, delimiter=delimiter)


def _meaningful_lines(text: str) -> list[str]:
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _detect_delimiter(header: str) -> str | None:
    candidates = [",", "\t", "|", ";"]
    return max(candidates, key=header.count) if any(token in header for token in candidates) else None


def _parse_whitespace_rows(lines: list[str]) -> list[dict[str, str]]:
    headers = lines[0].split()
    return [dict(zip(headers, line.split(), strict=True)) for line in lines[1:]]


def _row_to_trade_record(row: dict[str, str]) -> TradeRecord:
    normalized = {_normalize_column(key): value.strip() for key, value in row.items() if key}
    missing = _REQUIRED_COLUMNS - set(normalized)
    if missing:
        raise ValueError(f"missing required trade columns: {sorted(missing)}")

    return TradeRecord(
        entry_time=_parse_datetime(normalized["entry_time"]),
        exit_time=_parse_datetime(normalized["exit_time"]),
        side=_parse_side(normalized["side"]),
        entry_price=_parse_float(normalized["entry_price"], "entry_price"),
        exit_price=_parse_float(normalized["exit_price"], "exit_price"),
        qty=_parse_int(normalized["qty"], "qty"),
        slippage_points=_parse_float(normalized["slippage_points"], "slippage_points"),
        fee_points=_parse_float(normalized["fee_points"], "fee_points"),
        pnl_points=_parse_float(normalized["pnl_points"], "pnl_points"),
        pnl_after_cost_points=_parse_float(
            normalized["pnl_after_cost_points"],
            "pnl_after_cost_points",
        ),
    )


def _normalize_column(column: str) -> str:
    key = column.strip().lower().replace(" ", "_").replace("-", "_")
    return _COLUMN_ALIASES.get(key, key)


def _parse_datetime(value: str) -> datetime:
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid datetime: {value}") from exc


def _parse_side(value: str) -> TradeSide:
    side = value.strip().lower()
    if side in {"long", "buy", "b"}:
        return "long"
    if side in {"short", "sell", "s"}:
        return "short"
    raise ValueError(f"invalid side: {value}")


def _parse_float(value: str, column: str) -> float:
    try:
        return float(value.replace(",", ""))
    except ValueError as exc:
        raise ValueError(f"invalid float for {column}: {value}") from exc


def _parse_int(value: str, column: str) -> int:
    try:
        return int(float(value.replace(",", "")))
    except ValueError as exc:
        raise ValueError(f"invalid int for {column}: {value}") from exc
