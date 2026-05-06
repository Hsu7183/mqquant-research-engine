from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable

from mqre_v2.core.trades import ExtendedTradeRecord, TradeRecord


_COLUMN_ALIASES = {
    "entry_time": "entry_time",
    "entrytime": "entry_time",
    "entry_datetime": "entry_time",
    "entry_date_time": "entry_time",
    "exit_time": "exit_time",
    "exittime": "exit_time",
    "exit_datetime": "exit_time",
    "exit_date_time": "exit_time",
    "side": "direction",
    "direction": "direction",
    "position": "direction",
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
    "pnl_points": "pnl",
    "pnl": "pnl",
    "profit": "pnl",
    "pnl_after_cost_points": "pnl_after_cost",
    "pnl_after_cost": "pnl_after_cost",
    "net_pnl": "pnl_after_cost",
}

_BASE_REQUIRED_COLUMNS = {
    "entry_time",
    "exit_time",
    "direction",
    "entry_price",
    "exit_price",
}

_EXTENDED_REQUIRED_COLUMNS = {
    "qty",
    "slippage_points",
    "fee_points",
}

_ENTRY_ACTIONS = {"新買": 1, "新賣": -1}
_EXIT_ACTIONS = {"平賣": 1, "平買": -1}


def parse_xs_txt(text: str) -> list[TradeRecord]:
    lines = _meaningful_lines(text)
    if not lines:
        raise ValueError("trade txt cannot be empty")
    if _looks_like_action_log(lines):
        return _parse_action_log(lines)

    rows = list(_parse_rows(text))
    if not rows:
        raise ValueError("trade txt cannot be empty")

    records = [_row_to_trade_record(row) for row in rows]
    if not records:
        raise ValueError("trade txt contains no trade records")

    return records


def parse_xs_txt_extended(text: str) -> list[ExtendedTradeRecord]:
    rows = list(_parse_rows(text))
    if not rows:
        raise ValueError("trade txt cannot be empty")

    records = [_row_to_extended_trade_record(row) for row in rows]
    if not records:
        raise ValueError("trade txt contains no trade records")

    return records


def parse_xs_txt_file(path: str | Path, encoding: str = "utf-8-sig") -> list[TradeRecord]:
    return parse_xs_txt(Path(path).read_text(encoding=encoding))


def parse_xs_txt_extended_file(
    path: str | Path,
    encoding: str = "utf-8-sig",
) -> list[ExtendedTradeRecord]:
    return parse_xs_txt_extended(Path(path).read_text(encoding=encoding))


def parse_trade_txt(text: str) -> list[TradeRecord]:
    return parse_xs_txt(text)


def parse_trade_txt_file(path: str | Path, encoding: str = "utf-8-sig") -> list[TradeRecord]:
    return parse_xs_txt_file(path, encoding=encoding)


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


def _looks_like_action_log(lines: list[str]) -> bool:
    if lines[0].lower().startswith("strategy="):
        return True
    for line in lines[:3]:
        tokens = line.split()
        if tokens and tokens[-1] in (_ENTRY_ACTIONS | _EXIT_ACTIONS):
            return True
    return False


def _parse_action_log(lines: list[str]) -> list[TradeRecord]:
    event_lines = [
        line
        for line in lines
        if not line.lower().startswith("strategy=")
        and not line.lower().startswith("version=")
    ]
    if not event_lines:
        raise ValueError("trade txt contains no trade records")

    records: list[TradeRecord] = []
    open_trade: dict[str, object] | None = None

    for line in event_lines:
        tokens = line.split()
        if len(tokens) != 3:
            raise ValueError(f"invalid action trade row: {line}")

        timestamp_raw, price_raw, action = tokens
        timestamp = _parse_datetime(timestamp_raw)
        price = _parse_float(price_raw, "price")

        if action in _ENTRY_ACTIONS:
            if open_trade is not None:
                raise ValueError("new entry encountered before previous trade exit")
            open_trade = {
                "entry_time": timestamp,
                "entry_price": price,
                "direction": _ENTRY_ACTIONS[action],
            }
            continue

        if action in _EXIT_ACTIONS:
            if open_trade is None:
                raise ValueError("exit encountered without an open trade")
            direction = int(open_trade["direction"])
            if _EXIT_ACTIONS[action] != direction:
                raise ValueError("exit action does not match open trade direction")

            entry_price = float(open_trade["entry_price"])
            records.append(
                TradeRecord(
                    entry_time=open_trade["entry_time"],  # type: ignore[arg-type]
                    exit_time=timestamp,
                    entry_price=entry_price,
                    exit_price=price,
                    direction=direction,
                    pnl=_calculate_pure_pnl(entry_price, price, direction),
                )
            )
            open_trade = None
            continue

        raise ValueError(f"invalid trade action: {action}")

    if open_trade is not None:
        raise ValueError("trade txt ended with an open trade")
    if not records:
        raise ValueError("trade txt contains no trade records")
    return records


def _detect_delimiter(header: str) -> str | None:
    candidates = [",", "\t", "|", ";"]
    return max(candidates, key=header.count) if any(token in header for token in candidates) else None


def _parse_whitespace_rows(lines: list[str]) -> list[dict[str, str]]:
    headers = lines[0].split()
    return [dict(zip(headers, line.split(), strict=True)) for line in lines[1:]]


def _row_to_trade_record(row: dict[str, str]) -> TradeRecord:
    normalized = _normalize_row(row)
    _validate_columns(normalized, _BASE_REQUIRED_COLUMNS)

    entry_price = _parse_float(normalized["entry_price"], "entry_price")
    exit_price = _parse_float(normalized["exit_price"], "exit_price")
    direction = _parse_direction(normalized["direction"])

    return TradeRecord(
        entry_time=_parse_datetime(normalized["entry_time"]),
        exit_time=_parse_datetime(normalized["exit_time"]),
        entry_price=entry_price,
        exit_price=exit_price,
        direction=direction,
        pnl=_calculate_pure_pnl(entry_price, exit_price, direction),
    )


def _row_to_extended_trade_record(row: dict[str, str]) -> ExtendedTradeRecord:
    normalized = _normalize_row(row)
    _validate_columns(normalized, _BASE_REQUIRED_COLUMNS | _EXTENDED_REQUIRED_COLUMNS)

    base = _row_to_trade_record(row)
    qty = _parse_int(normalized["qty"], "qty")
    slippage_points = _parse_float(normalized["slippage_points"], "slippage_points")
    fee_points = _parse_float(normalized["fee_points"], "fee_points")

    return ExtendedTradeRecord(
        base=base,
        qty=qty,
        slippage_points=slippage_points,
        fee_points=fee_points,
        pnl_after_cost=(base.pnl * qty) - slippage_points - fee_points,
    )


def _normalize_row(row: dict[str, str]) -> dict[str, str]:
    return {_normalize_column(key): value.strip() for key, value in row.items() if key}


def _normalize_column(column: str) -> str:
    key = column.strip().lower().replace(" ", "_").replace("-", "_")
    return _COLUMN_ALIASES.get(key, key)


def _validate_columns(row: dict[str, str], required: set[str]) -> None:
    missing = required - set(row)
    if missing:
        raise ValueError(f"missing required trade columns: {sorted(missing)}")


def _parse_datetime(value: str) -> datetime:
    for fmt in (
        "%Y%m%d%H%M%S",
        "%Y%m%d%H%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid datetime: {value}") from exc


def _parse_direction(value: str) -> int:
    direction = value.strip().lower()
    if direction in {"1", "long", "buy", "b", "新買"}:
        return 1
    if direction in {"-1", "short", "sell", "s", "新賣", "新卖"}:
        return -1
    raise ValueError(f"invalid direction: {value}")


def _calculate_pure_pnl(entry_price: float, exit_price: float, direction: int) -> float:
    return (exit_price - entry_price) * direction


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
