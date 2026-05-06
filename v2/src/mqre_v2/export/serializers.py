from __future__ import annotations

import csv
import json
import math
from datetime import date, datetime
from pathlib import Path
from typing import Any


def format_datetime(value: Any) -> str:
    """Return a dashboard-friendly timestamp string."""
    if isinstance(value, datetime):
        return value.replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day).strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, str):
        return _normalize_datetime_string(value)
    return str(value)


def write_json(path: str | Path, data: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(_json_safe(data), handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def write_csv(
    path: str | Path,
    rows: list[dict[str, Any]],
    fieldnames: list[str],
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: _csv_safe(row.get(name, "")) for name in fieldnames})


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return format_datetime(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _csv_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return format_datetime(value)
    if isinstance(value, float) and not math.isfinite(value):
        return ""
    return value


def _normalize_datetime_string(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return cleaned
    if "T" in cleaned:
        cleaned = cleaned.replace("T", " ")
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1]
    if "+" in cleaned:
        cleaned = cleaned.split("+", 1)[0].strip()
    if len(cleaned) >= 19:
        return cleaned[:19]
    return cleaned
