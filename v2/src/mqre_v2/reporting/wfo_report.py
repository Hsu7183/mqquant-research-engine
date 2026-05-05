from __future__ import annotations

import json
import math
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from mqre_v2.validation.decision import DecisionResult
from mqre_v2.validation.wfo.runner import WfoRunResult


def wfo_run_result_to_dict(result: WfoRunResult) -> dict[str, Any]:
    return {
        "generated_at": _generated_at(),
        "windows": _json_safe(result.windows),
        "summary": _json_safe(result.summary),
        "round_results": _json_safe(result.round_results),
        "passed": result.passed,
        "fail_reason": result.fail_reason,
    }


def decision_result_to_dict(result: DecisionResult) -> dict[str, Any]:
    return _json_safe(result)


def export_json_report(payload: dict, output_path: str) -> None:
    report = dict(payload)
    report.setdefault("generated_at", _generated_at())

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(_json_safe(report), ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_safe(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_safe(asdict(value))
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            return None
        return "Infinity" if value > 0 else "-Infinity"
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    return value


__all__ = [
    "decision_result_to_dict",
    "export_json_report",
    "wfo_run_result_to_dict",
]
