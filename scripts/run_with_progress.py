from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "v2" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mqre_v2.cli.run_latest_pipeline import run_latest_pipeline  # noqa: E402
from mqre_v2.jobs.job_manager import create_job, fail_job, request_stop  # noqa: E402
from mqre_v2.jobs.job_state import read_progress, read_status  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run latest pipeline with progress monitor.")
    parser.add_argument("--base-dir", default="runs")
    parser.add_argument("--start-date", default="2020-01-01")
    parser.add_argument("--end-date", default=date.today().isoformat())
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    args = parser.parse_args()

    job_base_dir = str(Path(args.base_dir) / "jobs")
    job_id = create_job(base_dir=job_base_dir)
    result_box: dict[str, object] = {}

    def runner() -> None:
        try:
            result_box["result"] = run_latest_pipeline(
                base_dir=args.base_dir,
                start_date=date.fromisoformat(args.start_date),
                end_date=date.fromisoformat(args.end_date),
                job_id=job_id,
            )
        except Exception as exc:
            result_box["error"] = str(exc)
            try:
                fail_job(job_id, str(exc), base_dir=job_base_dir)
            except Exception:
                pass

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    print(f"job_id={job_id}", flush=True)

    try:
        while thread.is_alive():
            _print_job_progress(job_id, job_base_dir)
            time.sleep(max(0.1, args.poll_seconds))
    except KeyboardInterrupt:
        request_stop(job_id, base_dir=job_base_dir)
        print("stop requested; waiting for pipeline to stop...", flush=True)
        thread.join()

    thread.join()
    _print_job_progress(job_id, job_base_dir)
    if "error" in result_box:
        print(json.dumps({"job_id": job_id, "error": result_box["error"]}, ensure_ascii=False))
        return 1
    print(json.dumps(result_box.get("result", {"job_id": job_id}), ensure_ascii=False, indent=2))
    return 0


def _print_job_progress(job_id: str, job_base_dir: str) -> None:
    status = read_status(job_id, job_base_dir)
    progress = read_progress(job_id, job_base_dir)
    print(
        (
            f"status={status['status']} "
            f"completed={progress['completed']}/{progress['total']} "
            f"percent={progress['percent']:.2f}% "
            f"current={progress['current']}"
        ),
        flush=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())
