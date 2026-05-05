from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

RISK_WARNING_SEPARATOR = "|"

DECISION_AUDIT_FIELDNAMES = [
    "timestamp",
    "run_id",
    "strategy_name",
    "score",
    "recommend_promote",
    "reason",
    "risk_warnings",
    "requires_human_review",
    "source_report_path",
]


@dataclass(frozen=True)
class DecisionAuditRecord:
    timestamp: str
    run_id: str
    strategy_name: str
    score: float
    recommend_promote: bool
    reason: str
    risk_warnings: list[str]
    requires_human_review: bool
    source_report_path: str


def append_decision_audit(csv_path: str, record: DecisionAuditRecord) -> None:
    target = Path(csv_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    should_write_header = not target.exists() or target.stat().st_size == 0

    with target.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=DECISION_AUDIT_FIELDNAMES)
        if should_write_header:
            writer.writeheader()
        writer.writerow(_record_to_row(record))


def read_decision_audit(csv_path: str) -> list[DecisionAuditRecord]:
    source = Path(csv_path)
    if not source.exists():
        return []

    with source.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [_row_to_record(row) for row in reader]


def _record_to_row(record: DecisionAuditRecord) -> dict:
    row = asdict(record)
    row["risk_warnings"] = RISK_WARNING_SEPARATOR.join(record.risk_warnings)
    return row


def _row_to_record(row: dict[str, str]) -> DecisionAuditRecord:
    risk_warnings = row.get("risk_warnings", "")
    return DecisionAuditRecord(
        timestamp=row.get("timestamp", ""),
        run_id=row.get("run_id", ""),
        strategy_name=row.get("strategy_name", ""),
        score=float(row.get("score", 0.0) or 0.0),
        recommend_promote=_parse_bool(row.get("recommend_promote", "False")),
        reason=row.get("reason", ""),
        risk_warnings=[
            warning
            for warning in risk_warnings.split(RISK_WARNING_SEPARATOR)
            if warning
        ],
        requires_human_review=_parse_bool(
            row.get("requires_human_review", "False"),
        ),
        source_report_path=row.get("source_report_path", ""),
    )


def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}
