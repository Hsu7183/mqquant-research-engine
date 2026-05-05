from __future__ import annotations

from pathlib import Path

import pytest

from mqre_v2.forward.forward_log import (
    ForwardTestRecord,
    append_forward_record,
    read_forward_records,
    update_forward_status,
)


def test_append_forward_record_creates_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "forward_test_log.csv"

    append_forward_record(str(csv_path), _record("alpha"))

    assert csv_path.exists()
    assert "strategy_name" in csv_path.read_text(encoding="utf-8").splitlines()[0]


def test_read_forward_records_reads_back_data(tmp_path: Path) -> None:
    csv_path = tmp_path / "forward_test_log.csv"
    append_forward_record(str(csv_path), _record("alpha"))

    records = read_forward_records(str(csv_path))

    assert len(records) == 1
    assert records[0].strategy_name == "alpha"
    assert records[0].source_score == pytest.approx(88.5)


def test_append_forward_record_invalid_status_raises(tmp_path: Path) -> None:
    csv_path = tmp_path / "forward_test_log.csv"

    with pytest.raises(ValueError):
        append_forward_record(str(csv_path), _record("alpha", status="watching"))


def test_update_forward_status_updates_latest_record(tmp_path: Path) -> None:
    csv_path = tmp_path / "forward_test_log.csv"
    append_forward_record(str(csv_path), _record("alpha", notes="old"))

    update_forward_status(
        str(csv_path),
        strategy_name="alpha",
        new_status="forward_testing",
        notes="paper tracking started",
    )

    records = read_forward_records(str(csv_path))
    assert records[0].status == "forward_testing"
    assert records[0].notes == "paper tracking started"
    assert records[0].updated_at != records[0].created_at


def test_update_forward_status_missing_strategy_raises(tmp_path: Path) -> None:
    csv_path = tmp_path / "forward_test_log.csv"
    append_forward_record(str(csv_path), _record("alpha"))

    with pytest.raises(ValueError):
        update_forward_status(str(csv_path), "missing", "rejected")


def test_read_forward_records_missing_csv_returns_empty(tmp_path: Path) -> None:
    assert read_forward_records(str(tmp_path / "missing.csv")) == []


def _record(strategy_name: str, status: str = "candidate", notes: str = ""):
    return ForwardTestRecord(
        strategy_name=strategy_name,
        txt_path=f"{strategy_name}.txt",
        status=status,
        created_at="2026-05-05T00:00:00+00:00",
        updated_at="2026-05-05T00:00:00+00:00",
        source_score=88.5,
        source_pass_rate=0.75,
        source_total_test_net_profit=1234.0,
        notes=notes,
    )
