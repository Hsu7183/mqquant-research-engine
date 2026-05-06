from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"
STOPPED = "stopped"
VALID_STATUSES = {RUNNING, COMPLETED, FAILED, STOPPED}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def job_path(job_id: str, base_dir: str = "runs/jobs") -> Path:
    return Path(base_dir) / job_id


def status_path(job_id: str, base_dir: str = "runs/jobs") -> Path:
    return job_path(job_id, base_dir) / "status.json"


def progress_path(job_id: str, base_dir: str = "runs/jobs") -> Path:
    return job_path(job_id, base_dir) / "progress.json"


def build_status(
    job_id: str,
    status: str = RUNNING,
    start_time: str | None = None,
    end_time: str | None = None,
    error: str | None = None,
    stop_requested: bool = False,
) -> dict[str, Any]:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid job status: {status}")
    return {
        "job_id": job_id,
        "status": status,
        "start_time": start_time or utc_now(),
        "end_time": end_time,
        "error": error,
        "stop_requested": bool(stop_requested),
    }


def build_progress(
    total: int = 0,
    completed: int = 0,
    current: str = "",
    percent: float | None = None,
) -> dict[str, Any]:
    safe_total = max(0, int(total))
    safe_completed = max(0, int(completed))
    if percent is None:
        percent = (safe_completed / safe_total * 100.0) if safe_total else 0.0
    return {
        "total": safe_total,
        "completed": safe_completed,
        "current": str(current),
        "percent": round(float(percent), 4),
    }


def write_status(job_id: str, status: dict[str, Any], base_dir: str = "runs/jobs") -> None:
    _write_json(status_path(job_id, base_dir), status)


def read_status(job_id: str, base_dir: str = "runs/jobs") -> dict[str, Any]:
    path = status_path(job_id, base_dir)
    if not path.is_file():
        raise FileNotFoundError(f"job status not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_progress(
    job_id: str,
    progress: dict[str, Any],
    base_dir: str = "runs/jobs",
) -> None:
    _write_json(progress_path(job_id, base_dir), progress)


def read_progress(job_id: str, base_dir: str = "runs/jobs") -> dict[str, Any]:
    path = progress_path(job_id, base_dir)
    if not path.is_file():
        raise FileNotFoundError(f"job progress not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    last_error: OSError | None = None
    for _ in range(10):
        try:
            tmp_path.replace(path)
            return
        except OSError as exc:
            last_error = exc
            time.sleep(0.02)
    if last_error is not None:
        raise last_error
