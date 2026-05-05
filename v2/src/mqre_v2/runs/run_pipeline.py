from __future__ import annotations

import math
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path

from mqre_v2.pipeline.txt_wfo_pipeline import run_txt_wfo_pipeline
from mqre_v2.reporting.wfo_report import export_json_report
from mqre_v2.runs.run_manager import load_manifest, write_manifest
from mqre_v2.runs.run_txt_validator import validate_run_txt


@dataclass(frozen=True)
class RunPipelineResult:
    run_id: str
    total_strategies: int
    valid_txt: int
    ranking: list[dict]
    output_json_path: str


def run_pipeline_from_run(
    run_path: str,
    start_date: date,
    end_date: date,
    output_filename: str = "ranking.json",
) -> RunPipelineResult:
    validation = validate_run_txt(run_path)
    if len(validation.valid_txt) == 0:
        raise ValueError("no valid TXT files for run pipeline")

    manifest = load_manifest(run_path)
    root = Path(run_path)
    txt_folder = root / "txt"
    ranking = run_txt_wfo_pipeline(
        txt_folder=str(txt_folder),
        start_date=start_date,
        end_date=end_date,
        gate_config={},
        txt_filenames=validation.valid_txt,
    )

    output_path = root / "reports" / output_filename
    report_rows = [_to_report_row(item) for item in ranking]
    export_json_report(
        _build_report_payload(manifest.run_id, report_rows),
        str(output_path),
    )

    updated_manifest = replace(
        manifest,
        pipeline_completed=True,
        pipeline_total=len(ranking),
        pipeline_valid=len(validation.valid_txt),
    )
    write_manifest(run_path, updated_manifest)

    return RunPipelineResult(
        run_id=manifest.run_id,
        total_strategies=len(ranking),
        valid_txt=len(validation.valid_txt),
        ranking=ranking,
        output_json_path=str(output_path),
    )


def _build_report_payload(run_id: str, ranking: list[dict]) -> dict:
    return {
        "run_id": run_id,
        "summary": {
            "total_strategies": len(ranking),
            "valid_strategies": len(ranking),
        },
        "top_10": ranking[:10],
        "all_results": ranking,
    }


def _to_report_row(item: dict) -> dict:
    return {
        "rank": int(item["rank"]),
        "strategy_name": str(item["strategy_name"]),
        "score": _as_float(item["score"]),
        "total_test_net_profit": _as_float(item["total_test_net_profit"]),
        "pass_rate": _as_float(item["pass_rate"]),
        "max_test_mdd": _as_float(item["max_test_mdd"]),
        "average_test_pf": _as_float(item["average_test_pf"]),
    }


def _as_float(value: object) -> float:
    if isinstance(value, str) and value in {"Infinity", "-Infinity", "NaN"}:
        return 5.0 if value == "Infinity" else 0.0

    number = float(value)
    if not math.isfinite(number):
        return 5.0 if number > 0 else 0.0
    return number
