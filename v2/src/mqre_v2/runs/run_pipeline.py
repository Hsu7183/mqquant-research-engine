from __future__ import annotations

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
    export_json_report(
        {
            "run_id": manifest.run_id,
            "total_strategies": len(ranking),
            "valid_txt": len(validation.valid_txt),
            "top_10": ranking[:10],
            "ranking": ranking,
        },
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
