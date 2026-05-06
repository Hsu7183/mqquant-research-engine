"""Lightweight job progress and stop-flag helpers."""

from mqre_v2.jobs.job_manager import (
    complete_job,
    create_job,
    fail_job,
    is_stop_requested,
    request_stop,
    start_job,
    stop_job,
    update_progress,
)

__all__ = [
    "complete_job",
    "create_job",
    "fail_job",
    "is_stop_requested",
    "request_stop",
    "start_job",
    "stop_job",
    "update_progress",
]
