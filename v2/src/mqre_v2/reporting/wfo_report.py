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


def validate_report_schema(data: dict) -> bool:
    if not isinstance(data, dict):
        return False

    required_root = {"run_id", "generated_at", "summary", "top_10", "all_results"}
    if not required_root <= set(data):
        return False
    if not isinstance(data["run_id"], str):
        return False
    if not isinstance(data["generated_at"], str):
        return False
    if not _valid_summary(data["summary"]):
        return False
    if not isinstance(data["top_10"], list):
        return False
    if not isinstance(data["all_results"], list):
        return False

    return all(_valid_ranking_item(item) for item in data["top_10"]) and all(
        _valid_ranking_item(item) for item in data["all_results"]
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


def _valid_summary(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    required = {"total_strategies", "valid_strategies"}
    if not required <= set(value):
        return False
    return _is_int(value["total_strategies"]) and _is_int(value["valid_strategies"])


def _valid_ranking_item(value: Any) -> bool:
    if not isinstance(value, dict):
        return False

    required = {
        "rank",
        "strategy_name",
        "score",
        "total_test_net_profit",
        "pass_rate",
        "max_test_mdd",
        "average_test_pf",
    }
    if not required <= set(value):
        return False
    if not _is_int(value["rank"]):
        return False
    if not isinstance(value["strategy_name"], str):
        return False

    numeric_fields = required - {"rank", "strategy_name"}
    return all(_is_number(value[field]) for field in numeric_fields)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


__all__ = [
    "decision_result_to_dict",
    "export_json_report",
    "validate_report_schema",
    "wfo_run_result_to_dict",
]
