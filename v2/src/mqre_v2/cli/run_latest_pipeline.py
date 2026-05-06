from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Sequence

from mqre_v2.runs.run_pipeline import (
    run_pipeline_from_run,
    write_ranking_summary_detail_reports,
)


def get_latest_run(base_dir: str) -> str:
    base_path = Path(base_dir)
    if not base_path.is_dir():
        raise ValueError(f"run base directory not found: {base_dir}")

    run_dirs = sorted(path for path in base_path.iterdir() if path.is_dir())
    if not run_dirs:
        raise ValueError(f"no run directories found in: {base_dir}")

    return str(run_dirs[-1])


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the latest mqquant pipeline.")
    parser.add_argument("--base-dir", default="runs")
    parser.add_argument("--start-date", default="2020-01-01")
    parser.add_argument("--end-date", default=date.today().isoformat())
    parser.add_argument("--output-filename", default="ranking.json")
    args = parser.parse_args(argv)

    run_path = get_latest_run(args.base_dir)
    manifest_path = Path(run_path) / "manifest.json"
    if not manifest_path.is_file():
        ranking_path = Path(run_path) / "reports" / args.output_filename
        if not ranking_path.is_file():
            raise FileNotFoundError(
                f"latest run has no manifest and no ranking report: {run_path}"
            )

        detail_paths = write_ranking_summary_detail_reports(str(ranking_path))
        report = json.loads(ranking_path.read_text(encoding="utf-8"))
        print(
            json.dumps(
                {
                    "run_id": report.get("run_id", Path(run_path).name),
                    "run_path": run_path,
                    "total_strategies": len(report.get("all_results", [])),
                    "valid_txt": 0,
                    "output_json_path": str(ranking_path),
                    "detail_json_count": len(detail_paths),
                    "details_generated_from": "ranking_summary",
                    "top_10": report.get("top_10", []),
                },
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            )
        )
        return

    result = run_pipeline_from_run(
        run_path=run_path,
        start_date=date.fromisoformat(args.start_date),
        end_date=date.fromisoformat(args.end_date),
        output_filename=args.output_filename,
    )

    print(
        json.dumps(
            {
                "run_id": result.run_id,
                "run_path": run_path,
                "total_strategies": result.total_strategies,
                "valid_txt": result.valid_txt,
                "output_json_path": result.output_json_path,
                "top_10": result.ranking[:10],
            },
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
