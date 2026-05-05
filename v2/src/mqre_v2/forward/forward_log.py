from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

VALID_FORWARD_STATUSES = {
    "candidate",
    "forward_testing",
    "promoted",
    "rejected",
}

FORWARD_FIELDNAMES = [
    "strategy_name",
    "txt_path",
    "status",
    "created_at",
    "updated_at",
    "source_score",
    "source_pass_rate",
    "source_total_test_net_profit",
    "notes",
]


@dataclass(frozen=True)
class ForwardTestRecord:
    strategy_name: str
    txt_path: str
    status: str
    created_at: str
    updated_at: str
    source_score: float
    source_pass_rate: float
    source_total_test_net_profit: float
    notes: str = ""


def append_forward_record(csv_path: str, record: ForwardTestRecord) -> None:
    _validate_status(record.status)
    target = Path(csv_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    should_write_header = not target.exists() or target.stat().st_size == 0

    with target.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FORWARD_FIELDNAMES)
        if should_write_header:
            writer.writeheader()
        writer.writerow(asdict(record))


def read_forward_records(csv_path: str) -> list[ForwardTestRecord]:
    source = Path(csv_path)
    if not source.exists():
        return []

    with source.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [_row_to_record(row) for row in reader]


def update_forward_status(
    csv_path: str,
    strategy_name: str,
    new_status: str,
    notes: str = "",
) -> None:
    _validate_status(new_status)
    records = read_forward_records(csv_path)

    target_index = None
    for index in range(len(records) - 1, -1, -1):
        if records[index].strategy_name == strategy_name:
            target_index = index
            break

    if target_index is None:
        raise ValueError(f"strategy not found: {strategy_name}")

    records[target_index] = replace(
        records[target_index],
        status=new_status,
        updated_at=_now_iso(),
        notes=notes,
    )
    _write_records(csv_path, records)


def _write_records(csv_path: str, records: list[ForwardTestRecord]) -> None:
    target = Path(csv_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FORWARD_FIELDNAMES)
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))


def _row_to_record(row: dict[str, str]) -> ForwardTestRecord:
    status = row.get("status", "")
    _validate_status(status)
    return ForwardTestRecord(
        strategy_name=row.get("strategy_name", ""),
        txt_path=row.get("txt_path", ""),
        status=status,
        created_at=row.get("created_at", ""),
        updated_at=row.get("updated_at", ""),
        source_score=float(row.get("source_score", 0.0) or 0.0),
        source_pass_rate=float(row.get("source_pass_rate", 0.0) or 0.0),
        source_total_test_net_profit=float(
            row.get("source_total_test_net_profit", 0.0) or 0.0
        ),
        notes=row.get("notes", ""),
    )


def _validate_status(status: str) -> None:
    if status not in VALID_FORWARD_STATUSES:
        raise ValueError(f"invalid forward status: {status}")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
