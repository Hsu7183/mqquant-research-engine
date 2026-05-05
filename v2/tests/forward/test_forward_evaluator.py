from __future__ import annotations

from datetime import date
from pathlib import Path

from mqre_v2.forward.forward_evaluator import (
    ForwardEvaluationConfig,
    run_forward_evaluation,
)
from mqre_v2.forward.forward_log import (
    ForwardTestRecord,
    append_forward_record,
    read_forward_records,
)


def test_forward_testing_strategy_is_evaluated(tmp_path: Path) -> None:
    txt_path = tmp_path / "alpha.txt"
    _write_sample_txt(txt_path)
    _append_record(tmp_path / "forward.csv", "alpha", txt_path)

    result = run_forward_evaluation(_config(tmp_path, promote=-1.0, reject=-2.0))

    assert result["total_checked"] == 1
    assert result["promoted"][0]["strategy_name"] == "alpha"


def test_high_score_promotes_strategy(tmp_path: Path) -> None:
    txt_path = tmp_path / "alpha.txt"
    log_path = tmp_path / "forward.csv"
    _write_sample_txt(txt_path)
    _append_record(log_path, "alpha", txt_path)

    result = run_forward_evaluation(_config(tmp_path, promote=-1.0, reject=-2.0))
    records = read_forward_records(str(log_path))

    assert result["promoted"][0]["status"] == "promoted"
    assert records[0].status == "promoted"


def test_low_score_rejects_strategy(tmp_path: Path) -> None:
    txt_path = tmp_path / "alpha.txt"
    log_path = tmp_path / "forward.csv"
    _write_sample_txt(txt_path)
    _append_record(log_path, "alpha", txt_path)

    result = run_forward_evaluation(_config(tmp_path, promote=999999.0, reject=999999.0))
    records = read_forward_records(str(log_path))

    assert result["rejected"][0]["status"] == "rejected"
    assert records[0].status == "rejected"


def test_middle_score_stays_forward_testing(tmp_path: Path) -> None:
    txt_path = tmp_path / "alpha.txt"
    log_path = tmp_path / "forward.csv"
    _write_sample_txt(txt_path)
    _append_record(log_path, "alpha", txt_path)

    result = run_forward_evaluation(_config(tmp_path, promote=999999.0, reject=-1.0))
    records = read_forward_records(str(log_path))

    assert result["still_testing"][0]["status"] == "forward_testing"
    assert records[0].status == "forward_testing"


def test_forward_log_is_updated_with_notes(tmp_path: Path) -> None:
    txt_path = tmp_path / "alpha.txt"
    log_path = tmp_path / "forward.csv"
    _write_sample_txt(txt_path)
    _append_record(log_path, "alpha", txt_path)

    run_forward_evaluation(_config(tmp_path, promote=-1.0, reject=-2.0))
    records = read_forward_records(str(log_path))

    assert records[0].status == "promoted"
    assert records[0].notes.startswith("forward evaluation score=")


def test_no_forward_testing_strategy_does_not_crash(tmp_path: Path) -> None:
    txt_path = tmp_path / "alpha.txt"
    log_path = tmp_path / "forward.csv"
    _write_sample_txt(txt_path)
    _append_record(log_path, "alpha", txt_path, status="candidate")

    result = run_forward_evaluation(_config(tmp_path, promote=-1.0, reject=-2.0))

    assert result == {
        "total_checked": 0,
        "promoted": [],
        "rejected": [],
        "still_testing": [],
    }


def _config(tmp_path: Path, promote: float, reject: float) -> ForwardEvaluationConfig:
    return ForwardEvaluationConfig(
        txt_folder=str(tmp_path),
        start_date=date(2020, 1, 1),
        end_date=date(2024, 12, 31),
        forward_log_path=str(tmp_path / "forward.csv"),
        promote_threshold_score=promote,
        reject_threshold_score=reject,
    )


def _append_record(
    log_path: Path,
    strategy_name: str,
    txt_path: Path,
    status: str = "forward_testing",
) -> None:
    append_forward_record(
        str(log_path),
        ForwardTestRecord(
            strategy_name=strategy_name,
            txt_path=str(txt_path),
            status=status,
            created_at="2026-05-05T00:00:00+00:00",
            updated_at="2026-05-05T00:00:00+00:00",
            source_score=100.0,
            source_pass_rate=1.0,
            source_total_test_net_profit=1000.0,
        ),
    )


def _write_sample_txt(path: Path) -> None:
    path.write_text(
        "entry_time,exit_time,side,entry_price,exit_price\n"
        "2023-03-01T09:00:00,2023-03-01T09:05:00,long,100,120\n"
        "2023-03-02T09:00:00,2023-03-02T09:05:00,long,120,110\n",
        encoding="utf-8",
    )
