from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Sequence

from mqre_v2.backtest.costs import CostConfig
from mqre_v2.pipeline.txt_wfo_pipeline import run_txt_wfo_pipeline
from mqre_v2.reporting.wfo_report import export_json_report
from mqre_v2.runs.run_pipeline import (
    _build_report_payload,
    _to_report_row,
    _write_strategy_detail_reports,
    export_dashboard_artifacts_from_ranking,
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


def run_latest_pipeline(
    base_dir: str = "runs",
    start_date: date | None = None,
    end_date: date | None = None,
    output_filename: str = "ranking.json",
    cost_config: CostConfig | None = None,
    strategy_quality: dict | None = None,
) -> dict:
    start = start_date or date(2020, 1, 1)
    end = end_date or date.today()
    effective_cost = cost_config or CostConfig()

    run_path = get_latest_run(base_dir)
    manifest_path = Path(run_path) / "manifest.json"
    if not manifest_path.is_file():
        txt_dir = Path(run_path) / "txt"
        if txt_dir.is_dir() and any(txt_dir.glob("*.txt")):
            ranking = run_txt_wfo_pipeline(
                txt_folder=str(txt_dir),
                start_date=start,
                end_date=end,
                gate_config={},
                include_wfo_details=True,
                cost_config=effective_cost,
                strategy_quality=strategy_quality,
            )
            ranking_path = Path(run_path) / "reports" / output_filename
            report_rows = [_to_report_row(item) for item in ranking]
            detail_paths = _write_strategy_detail_reports(
                Path(run_path),
                Path(run_path).name,
                ranking,
                effective_cost,
            )
            artifact_paths = export_dashboard_artifacts_from_ranking(
                root=Path(run_path),
                run_id=Path(run_path).name,
                ranking=ranking,
                cost_config=effective_cost,
            )
            export_json_report(
                _build_report_payload(Path(run_path).name, report_rows),
                str(ranking_path),
            )
            return {
                "run_id": Path(run_path).name,
                "run_path": run_path,
                "total_strategies": len(ranking),
                "valid_txt": len(ranking),
                "output_json_path": str(ranking_path),
                "detail_json_count": len(detail_paths),
                "artifact_count": len(artifact_paths),
                "details_generated_from": "txt",
                "top_10": ranking[:10],
            }

        ranking_path = Path(run_path) / "reports" / output_filename
        if not ranking_path.is_file():
            raise FileNotFoundError(
                f"latest run has no manifest and no ranking report: {run_path}"
            )

        detail_paths = write_ranking_summary_detail_reports(str(ranking_path))
        report = json.loads(ranking_path.read_text(encoding="utf-8"))
        ranking = report.get("all_results", []) or report.get("top_10", [])
        artifact_paths = export_dashboard_artifacts_from_ranking(
            root=Path(run_path),
            run_id=str(report.get("run_id", Path(run_path).name)),
            ranking=ranking,
            cost_config=effective_cost,
        )
        return {
            "run_id": report.get("run_id", Path(run_path).name),
            "run_path": run_path,
            "total_strategies": len(report.get("all_results", [])),
            "valid_txt": 0,
            "output_json_path": str(ranking_path),
            "detail_json_count": len(detail_paths),
            "artifact_count": len(artifact_paths),
            "details_generated_from": "ranking_summary",
            "top_10": report.get("top_10", []),
        }

    result = run_pipeline_from_run(
        run_path=run_path,
        start_date=start,
        end_date=end,
        output_filename=output_filename,
        cost_config=effective_cost,
    )

    return {
        "run_id": result.run_id,
        "run_path": run_path,
        "total_strategies": result.total_strategies,
        "valid_txt": result.valid_txt,
        "output_json_path": result.output_json_path,
        "artifact_count": 9,
        "top_10": result.ranking[:10],
    }


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the latest mqquant pipeline.")
    parser.add_argument("--base-dir", default="runs")
    parser.add_argument("--start-date", default="2020-01-01")
    parser.add_argument("--end-date", default=date.today().isoformat())
    parser.add_argument("--output-filename", default="ranking.json")
    parser.add_argument("--slippage-points", type=float, default=2.0)
    parser.add_argument("--fee-money", type=float, default=0.0)
    parser.add_argument("--tax-rate", type=float, default=0.00002)
    parser.add_argument("--point-value", type=float, default=50.0)
    parser.add_argument("--qty", type=int, default=1)
    args = parser.parse_args(argv)

    result = run_latest_pipeline(
        base_dir=args.base_dir,
        start_date=date.fromisoformat(args.start_date),
        end_date=date.fromisoformat(args.end_date),
        output_filename=args.output_filename,
        cost_config=CostConfig(
            slippage_points_per_side=args.slippage_points,
            fee_money_per_side=args.fee_money,
            tax_rate=args.tax_rate,
            point_value=args.point_value,
            qty=args.qty,
        ),
    )
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
