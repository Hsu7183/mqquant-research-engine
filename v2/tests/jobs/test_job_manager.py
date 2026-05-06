import time
from datetime import date
from pathlib import Path

import pytest

from mqre_v2.jobs.job_manager import (
    JobStopped,
    create_job,
    is_stop_requested,
    request_stop,
    start_job,
    update_progress,
)
from mqre_v2.jobs.job_state import read_progress, read_status
from mqre_v2.runs.run_manager import RunManifest, create_run_directory, write_manifest
from mqre_v2.runs.run_pipeline import run_pipeline_from_run


def test_create_job_writes_status_and_progress(tmp_path) -> None:
    base_dir = str(tmp_path / "jobs")

    job_id = create_job(base_dir=base_dir)

    status = read_status(job_id, base_dir)
    progress = read_progress(job_id, base_dir)
    assert status["job_id"] == job_id
    assert status["status"] == "running"
    assert status["stop_requested"] is False
    assert progress == {"total": 0, "completed": 0, "current": "", "percent": 0.0}


def test_update_progress_writes_percent(tmp_path) -> None:
    base_dir = str(tmp_path / "jobs")
    job_id = create_job(base_dir=base_dir)

    update_progress(
        job_id,
        {"total": 300, "completed": 120, "current": "strategy_xxx"},
        base_dir=base_dir,
    )

    progress = read_progress(job_id, base_dir)
    assert progress["total"] == 300
    assert progress["completed"] == 120
    assert progress["current"] == "strategy_xxx"
    assert progress["percent"] == 40.0


def test_request_stop_sets_stop_flag(tmp_path) -> None:
    base_dir = str(tmp_path / "jobs")
    job_id = create_job(base_dir=base_dir)

    request_stop(job_id, base_dir=base_dir)

    assert is_stop_requested(job_id, base_dir=base_dir) is True
    assert read_status(job_id, base_dir)["stop_requested"] is True


def test_start_job_completes_background_function(tmp_path) -> None:
    base_dir = str(tmp_path / "jobs")

    def worker(job_id: str) -> str:
        update_progress(
            job_id,
            {"total": 1, "completed": 1, "current": "done"},
            base_dir=base_dir,
        )
        return "ok"

    job_id, future = start_job(worker, base_dir=base_dir)

    assert future.result(timeout=5) == "ok"
    assert read_status(job_id, base_dir)["status"] == "completed"
    assert read_progress(job_id, base_dir)["percent"] == 100.0


def test_run_pipeline_updates_progress_and_completes_job(tmp_path) -> None:
    run_path = _create_run(tmp_path)
    _write_xs(run_path, "alpha")
    _write_xs(run_path, "beta")
    _write_txt(run_path, "alpha", 100, 120)
    _write_txt(run_path, "beta", 100, 140)

    result = run_pipeline_from_run(
        run_path,
        start_date=date(2020, 1, 1),
        end_date=date(2023, 12, 31),
    )

    job_base_dir = str(Path(run_path).parent / "jobs")
    status = read_status(result.job_id, job_base_dir)
    progress = read_progress(result.job_id, job_base_dir)
    assert status["status"] == "completed"
    assert progress["total"] == 2
    assert progress["completed"] == 2
    assert progress["percent"] == 100.0


def test_run_pipeline_can_stop_before_next_strategy(tmp_path) -> None:
    run_path = _create_run(tmp_path)
    _write_xs(run_path, "alpha")
    _write_txt(run_path, "alpha", 100, 120)
    job_base_dir = str(Path(run_path).parent / "jobs")
    job_id = create_job(base_dir=job_base_dir)
    request_stop(job_id, base_dir=job_base_dir)

    with pytest.raises(JobStopped):
        run_pipeline_from_run(
            run_path,
            start_date=date(2020, 1, 1),
            end_date=date(2023, 12, 31),
            job_id=job_id,
            job_base_dir=job_base_dir,
        )

    assert read_status(job_id, job_base_dir)["status"] == "stopped"


def _create_run(tmp_path) -> str:
    run_path = create_run_directory(str(tmp_path / "runs"), "1001plus")
    write_manifest(
        run_path,
        RunManifest(
            run_id=Path(run_path).name,
            strategy_name="1001plus",
            created_at="2026-05-07T00:00:00+00:00",
            parameter_grid_path="grid.yaml",
            template_path="template.xs",
            total_param_combinations=0,
        ),
    )
    return run_path


def _write_xs(run_path: str, stem: str) -> None:
    (Path(run_path) / "xs" / f"{stem}.xs").write_text("value1;", encoding="utf-8")


def _write_txt(run_path: str, stem: str, entry_price: int, exit_price: int) -> None:
    (Path(run_path) / "txt" / f"{stem}.txt").write_text(
        "entry_time,exit_time,side,entry_price,exit_price\n"
        f"2023-03-01T09:00:00,2023-03-01T09:05:00,long,{entry_price},{exit_price}\n",
        encoding="utf-8",
    )
