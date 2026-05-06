from __future__ import annotations

import csv
from datetime import date, datetime as DateTime
from pathlib import Path
from typing import Any

DEFAULT_FORWARD_LOG_PATH = "runs/forward/forward_log.csv"

FORWARD_TRADE_FIELDNAMES = [
    "datetime",
    "strategy_id",
    "price",
    "pnl",
    "cumulative_pnl",
]


def log_forward_trade(
    strategy_id: str,
    datetime: str | DateTime | date,
    price: float,
    pnl: float,
    log_path: str = DEFAULT_FORWARD_LOG_PATH,
) -> dict[str, Any]:
    """Append one forward-test trade observation to the forward log CSV."""
    target = Path(log_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    cumulative_pnl = _latest_cumulative_pnl(target, strategy_id) + float(pnl)
    row = {
        "datetime": _format_datetime(datetime),
        "strategy_id": strategy_id,
        "price": float(price),
        "pnl": float(pnl),
        "cumulative_pnl": cumulative_pnl,
    }

    should_write_header = not target.exists() or target.stat().st_size == 0
    with target.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FORWARD_TRADE_FIELDNAMES)
        if should_write_header:
            writer.writeheader()
        writer.writerow(row)

    return row


def _latest_cumulative_pnl(path: Path, strategy_id: str) -> float:
    if not path.exists():
        return 0.0

    latest = 0.0
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("strategy_id") != strategy_id:
                continue
            latest = _as_float(row.get("cumulative_pnl"))
    return latest


def _format_datetime(value: str | DateTime | date) -> str:
    if isinstance(value, DateTime):
        return value.replace(microsecond=0).isoformat(sep=" ")
    if isinstance(value, date):
        return DateTime(value.year, value.month, value.day).isoformat(sep=" ")
    return str(value)


def _as_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
