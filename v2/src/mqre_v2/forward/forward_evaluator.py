from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from mqre_v2.forward.forward_log import (
    ForwardTestRecord,
    read_forward_records,
    update_forward_status,
)
from mqre_v2.pipeline.txt_wfo_pipeline import run_txt_wfo_pipeline


@dataclass(frozen=True)
class ForwardEvaluationConfig:
    txt_folder: str
    start_date: date
    end_date: date
    forward_log_path: str
    promote_threshold_score: float = 100.0
    reject_threshold_score: float = 50.0


def run_forward_evaluation(config: ForwardEvaluationConfig) -> dict[str, Any]:
    records = [
        record
        for record in read_forward_records(config.forward_log_path)
        if record.status == "forward_testing"
    ]

    promoted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    still_testing: list[dict[str, Any]] = []

    for record in records:
        evaluation = _evaluate_forward_record(record, config)
        score = float(evaluation["score"])

        if score >= config.promote_threshold_score:
            update_forward_status(
                config.forward_log_path,
                record.strategy_name,
                "promoted",
                notes=f"forward evaluation score={score}",
            )
            evaluation["status"] = "promoted"
            promoted.append(evaluation)
        elif score < config.reject_threshold_score:
            update_forward_status(
                config.forward_log_path,
                record.strategy_name,
                "rejected",
                notes=f"forward evaluation score={score}",
            )
            evaluation["status"] = "rejected"
            rejected.append(evaluation)
        else:
            evaluation["status"] = "forward_testing"
            still_testing.append(evaluation)

    return {
        "total_checked": len(records),
        "promoted": promoted,
        "rejected": rejected,
        "still_testing": still_testing,
    }


def _evaluate_forward_record(
    record: ForwardTestRecord,
    config: ForwardEvaluationConfig,
) -> dict[str, Any]:
    txt_path = _resolve_txt_path(record, config.txt_folder)
    result = _run_pipeline_for_strategy(record.strategy_name, txt_path, config)
    return {
        "strategy_name": record.strategy_name,
        "txt_path": str(txt_path),
        "score": float(result["score"]),
        "passed": result["passed"],
        "fail_reason": result["fail_reason"],
    }


def _run_pipeline_for_strategy(
    strategy_name: str,
    txt_path: Path,
    config: ForwardEvaluationConfig,
) -> dict[str, Any]:
    results = run_txt_wfo_pipeline(
        txt_folder=str(txt_path.parent),
        start_date=config.start_date,
        end_date=config.end_date,
        gate_config={},
    )
    resolved_txt_path = txt_path.resolve()
    for result in results:
        result_path = Path(str(result["txt_path"]))
        if result_path.exists() and result_path.resolve() == resolved_txt_path:
            return result
        if result["strategy_name"] == strategy_name:
            return result

    raise ValueError(f"strategy txt not found in pipeline results: {strategy_name}")


def _resolve_txt_path(record: ForwardTestRecord, txt_folder: str) -> Path:
    raw_path = Path(record.txt_path)
    candidates = []
    if raw_path.is_absolute():
        candidates.append(raw_path)
    else:
        folder = Path(txt_folder)
        candidates.extend(
            [
                folder / raw_path,
                folder / raw_path.name,
            ]
        )

    candidates.append(Path(txt_folder) / f"{record.strategy_name}.txt")

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]
