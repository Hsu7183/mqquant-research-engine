from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "v2" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mqre_v2.cli.run_latest_pipeline import run_latest_pipeline  # noqa: E402
from mqre_v2.backtest.trade_export import export_trades_to_xs_txt  # noqa: E402
from mqre_v2.io.m1_parser import parse_m1_txt  # noqa: E402
from mqre_v2.jobs.job_manager import create_job, fail_job, request_stop  # noqa: E402
from mqre_v2.jobs.job_state import read_progress, read_status  # noqa: E402
from mqre_v2.strategy.strategy_1001plus import (  # noqa: E402
    Strategy1001PlusParams,
    backtest_strategy_1001plus,
)
from mqre_v2.strategy.strategy_1001plus_generator import (  # noqa: E402
    generate_1001plus_strategies,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run latest pipeline with progress monitor.")
    parser.add_argument("--base-dir", default="runs")
    parser.add_argument("--start-date", default="2020-01-01")
    parser.add_argument("--end-date", default=date.today().isoformat())
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    parser.add_argument("--use-generator", choices=["1001plus"], default="")
    parser.add_argument("--generator-mode", choices=["default", "risk_constrained"], default="default")
    parser.add_argument("--m1-path", default="M1.txt")
    parser.add_argument("--num-strategies", type=int, default=300)
    parser.add_argument("--seed", type=int, default=1001)
    parser.add_argument("--sample-bars", type=int, default=0)
    args = parser.parse_args()

    job_base_dir = str(Path(args.base_dir) / "jobs")
    generation_summary: dict[str, Any] | None = None
    if args.use_generator == "1001plus":
        generation_summary = _generate_1001plus_challenger_txts(
            base_dir=args.base_dir,
            m1_path=args.m1_path,
            n=args.num_strategies,
            seed=args.seed,
            mode=args.generator_mode,
            start_date=date.fromisoformat(args.start_date),
            end_date=date.fromisoformat(args.end_date),
            sample_bars=args.sample_bars,
        )
        print(json.dumps(generation_summary, ensure_ascii=False, indent=2), flush=True)

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
    payload = result_box.get("result", {"job_id": job_id})
    if isinstance(payload, dict) and generation_summary is not None:
        payload = {**payload, "generation": generation_summary}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
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


def _generate_1001plus_challenger_txts(
    base_dir: str,
    m1_path: str,
    n: int,
    seed: int,
    mode: str,
    start_date: date,
    end_date: date,
    sample_bars: int,
) -> dict[str, Any]:
    print(f"1001plus challenger generator started: mode={mode}", flush=True)
    bars = [
        bar
        for bar in parse_m1_txt(m1_path)
        if start_date <= bar.ts.date() <= end_date
    ]
    if sample_bars < 0:
        raise ValueError("sample_bars must be >= 0")
    if sample_bars > 0:
        bars = bars[-sample_bars:]
    print(f"M1 bars loaded: {len(bars)}", flush=True)

    strategies = generate_1001plus_strategies(n=n, seed=seed, mode=mode)
    txt_dir = Path(base_dir) / "latest" / "txt"
    detail_dir = Path(base_dir) / "latest" / "reports" / "details"
    _clear_files(txt_dir, "*.txt")
    _clear_files(detail_dir, "*.json")

    generated_txt = 0
    empty_strategies = 0
    for index, strategy in enumerate(strategies, start=1):
        strategy_name = str(strategy["strategy_name"])
        params = Strategy1001PlusParams(
            strategy_name=strategy_name,
            **strategy["params"],
        )
        trades = backtest_strategy_1001plus(bars, params)
        if trades:
            export_trades_to_xs_txt(
                trades,
                str(txt_dir / f"{strategy_name}.txt"),
                strategy_name,
            )
            generated_txt += 1
        else:
            empty_strategies += 1
        if index == len(strategies) or index % 25 == 0:
            print(
                (
                    "1001plus generator progress: "
                    f"{index}/{len(strategies)} strategies, "
                    f"{generated_txt} trade files"
                ),
                flush=True,
            )

    return {
        "generator": "1001plus",
        "generator_mode": mode,
        "requested_strategies": n,
        "generated_strategies": len(strategies),
        "trade_files": generated_txt,
        "empty_strategies": empty_strategies,
        "txt_dir": str(txt_dir),
        "sample_bars": sample_bars,
    }


def _clear_files(folder: Path, pattern: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for path in folder.glob(pattern):
        if path.is_file():
            path.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
