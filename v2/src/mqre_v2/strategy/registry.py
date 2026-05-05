from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

from mqre_v2.forward.forward_log import read_forward_records

VALID_STRATEGY_STATUSES = {
    "active",
    "retired",
}

STRATEGY_REGISTRY_FIELDNAMES = [
    "strategy_name",
    "txt_path",
    "status",
    "promoted_at",
    "source",
    "notes",
]


@dataclass(frozen=True)
class StrategyRegistryRecord:
    strategy_name: str
    txt_path: str
    status: str
    promoted_at: str
    source: str
    notes: str = ""


def append_strategy_registry_record(
    csv_path: str,
    record: StrategyRegistryRecord,
) -> None:
    _validate_status(record.status)
    target = Path(csv_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    should_write_header = not target.exists() or target.stat().st_size == 0

    with target.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=STRATEGY_REGISTRY_FIELDNAMES)
        if should_write_header:
            writer.writeheader()
        writer.writerow(asdict(record))


def read_strategy_registry(csv_path: str) -> list[StrategyRegistryRecord]:
    source = Path(csv_path)
    if not source.exists():
        return []

    with source.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [_row_to_record(row) for row in reader]


def retire_strategy(csv_path: str, strategy_name: str, notes: str = "") -> None:
    records = read_strategy_registry(csv_path)

    target_index = None
    for index in range(len(records) - 1, -1, -1):
        record = records[index]
        if record.strategy_name == strategy_name and record.status == "active":
            target_index = index
            break

    if target_index is None:
        raise ValueError(f"active strategy not found: {strategy_name}")

    records[target_index] = replace(
        records[target_index],
        status="retired",
        notes=notes,
    )
    _write_records(csv_path, records)


def promote_from_forward_log(
    forward_log_path: str,
    registry_csv_path: str,
) -> list[StrategyRegistryRecord]:
    registry = read_strategy_registry(registry_csv_path)
    active_strategy_names = {
        record.strategy_name for record in registry if record.status == "active"
    }
    added: list[StrategyRegistryRecord] = []

    for forward_record in read_forward_records(forward_log_path):
        if forward_record.status != "promoted":
            continue
        if forward_record.strategy_name in active_strategy_names:
            continue

        registry_record = StrategyRegistryRecord(
            strategy_name=forward_record.strategy_name,
            txt_path=forward_record.txt_path,
            status="active",
            promoted_at=_now_iso(),
            source="forward_log",
            notes=forward_record.notes,
        )
        append_strategy_registry_record(registry_csv_path, registry_record)
        active_strategy_names.add(registry_record.strategy_name)
        added.append(registry_record)

    return added


def _write_records(csv_path: str, records: list[StrategyRegistryRecord]) -> None:
    target = Path(csv_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=STRATEGY_REGISTRY_FIELDNAMES)
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))


def _row_to_record(row: dict[str, str]) -> StrategyRegistryRecord:
    status = row.get("status", "")
    _validate_status(status)
    return StrategyRegistryRecord(
        strategy_name=row.get("strategy_name", ""),
        txt_path=row.get("txt_path", ""),
        status=status,
        promoted_at=row.get("promoted_at", ""),
        source=row.get("source", ""),
        notes=row.get("notes", ""),
    )


def _validate_status(status: str) -> None:
    if status not in VALID_STRATEGY_STATUSES:
        raise ValueError(f"invalid strategy status: {status}")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
