from __future__ import annotations

import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Callable

from mqre_v2.jobs.job_state import (
    COMPLETED,
    FAILED,
    RUNNING,
    STOPPED,
    build_progress,
    build_status,
    job_path,
    read_status,
    utc_now,
    write_progress,
    write_status,
)


_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="mqre-job")


class JobStopped(RuntimeError):
    """Raised when a job stops because its stop flag was requested."""


def create_job(base_dir: str = "runs/jobs") -> str:
    job_id = _new_job_id()
    job_path(job_id, base_dir).mkdir(parents=True, exist_ok=False)
    write_status(job_id, build_status(job_id, status=RUNNING), base_dir)
    write_progress(job_id, build_progress(), base_dir)
    return job_id


def start_job(
    fn: Callable[..., Any],
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
    base_dir: str = "runs/jobs",
) -> tuple[str, Future]:
    job_id = create_job(base_dir=base_dir)

    def runner() -> Any:
        try:
            result = fn(job_id, *(args or ()), **(kwargs or {}))
        except JobStopped:
            stop_job(job_id, base_dir=base_dir)
            raise
        except Exception as exc:
            fail_job(job_id, str(exc), base_dir=base_dir)
            raise
        else:
            if is_stop_requested(job_id, base_dir=base_dir):
                stop_job(job_id, base_dir=base_dir)
            else:
                complete_job(job_id, base_dir=base_dir)
            return result

    return job_id, _EXECUTOR.submit(runner)


def update_progress(
    job_id: str,
    progress: dict[str, Any],
    base_dir: str = "runs/jobs",
) -> None:
    write_progress(
        job_id,
        build_progress(
            total=int(progress.get("total", 0)),
            completed=int(progress.get("completed", 0)),
            current=str(progress.get("current", "")),
            percent=progress.get("percent"),
        ),
        base_dir,
    )


def complete_job(job_id: str, base_dir: str = "runs/jobs") -> None:
    status = _existing_or_new_status(job_id, base_dir)
    status.update({"status": COMPLETED, "end_time": utc_now(), "error": None})
    write_status(job_id, status, base_dir)


def fail_job(job_id: str, error: str, base_dir: str = "runs/jobs") -> None:
    status = _existing_or_new_status(job_id, base_dir)
    status.update({"status": FAILED, "end_time": utc_now(), "error": str(error)})
    write_status(job_id, status, base_dir)


def stop_job(job_id: str, base_dir: str = "runs/jobs") -> None:
    status = _existing_or_new_status(job_id, base_dir)
    status.update({"status": STOPPED, "end_time": utc_now()})
    write_status(job_id, status, base_dir)


def request_stop(job_id: str, base_dir: str = "runs/jobs") -> None:
    status = _existing_or_new_status(job_id, base_dir)
    status["stop_requested"] = True
    write_status(job_id, status, base_dir)


def is_stop_requested(job_id: str, base_dir: str = "runs/jobs") -> bool:
    try:
        status = read_status(job_id, base_dir)
    except FileNotFoundError:
        return False
    return bool(status.get("stop_requested"))


def _existing_or_new_status(job_id: str, base_dir: str) -> dict[str, Any]:
    try:
        return read_status(job_id, base_dir)
    except FileNotFoundError:
        return build_status(job_id, status=RUNNING)


def _new_job_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{timestamp}_{uuid.uuid4().hex[:8]}"
