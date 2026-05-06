from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from mqre_v2.forward.forward_log import (
    ForwardTestRecord,
    append_forward_record,
    read_forward_records,
)
from mqre_v2.pipeline.txt_wfo_pipeline import run_txt_wfo_pipeline


@dataclass(frozen=True)
class AutoResearchConfig:
    txt_folder: str
    start_date: date
    end_date: date
    output_json_path: str
    forward_log_path: str
    top_n: int = 10
    auto_add_top1_to_forward: bool = True
    min_score_to_forward: float = 0.0


def run_auto_research(config: AutoResearchConfig) -> dict[str, Any]:
    ranking = run_txt_wfo_pipeline(
        txt_folder=config.txt_folder,
        start_date=config.start_date,
        end_date=config.end_date,
        gate_config={},
    )
    if not ranking:
        raise ValueError("no strategy results generated")

    top_n_results = ranking[: config.top_n]
    top1 = ranking[0]
    _export_auto_research_json(
        output_path=config.output_json_path,
        ranking=ranking,
        top_n_results=top_n_results,
    )

    added_to_forward = False
    notes = ""

    if config.auto_add_top1_to_forward:
        top1_score = _to_float(top1["score"])
        if top1_score >= config.min_score_to_forward:
            if _forward_record_exists(
                config.forward_log_path,
                str(top1["strategy_name"]),
            ):
                notes = "duplicate skipped"
            else:
                append_forward_record(
                    config.forward_log_path,
                    _build_forward_record(top1),
                )
                added_to_forward = True
                notes = "top1 added to forward candidates"
        else:
            notes = "score below min_score_to_forward"
    else:
        notes = "auto forward disabled"

    return {
        "total_strategies": len(ranking),
        "top_n": top_n_results,
        "top1": top1,
        "output_json_path": config.output_json_path,
        "forward_log_path": config.forward_log_path,
        "added_to_forward": added_to_forward,
        "notes": notes,
    }


def _export_auto_research_json(
    output_path: str,
    ranking: list[dict[str, Any]],
    top_n_results: list[dict[str, Any]],
) -> None:
    payload = {
        "run_id": "latest",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_strategies": len(ranking),
            "valid_strategies": len(ranking),
        },
        "total_strategies": len(ranking),
        "top_n": top_n_results,
        "top_10": ranking[:10],
        "all_results": ranking,
    }
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )


def _forward_record_exists(forward_log_path: str, strategy_name: str) -> bool:
    return any(
        record.strategy_name == strategy_name
        for record in read_forward_records(forward_log_path)
    )


def _build_forward_record(result: dict[str, Any]) -> ForwardTestRecord:
    timestamp = datetime.now(timezone.utc).isoformat()
    return ForwardTestRecord(
        strategy_name=str(result["strategy_name"]),
        txt_path=str(result["txt_path"]),
        status="candidate",
        created_at=timestamp,
        updated_at=timestamp,
        source_score=_to_float(result["score"]),
        source_pass_rate=_to_float(result["pass_rate"]),
        source_total_test_net_profit=_to_float(result["total_test_net_profit"]),
        notes="auto research top1 candidate",
    )


def _to_float(value: Any) -> float:
    return float(value)
