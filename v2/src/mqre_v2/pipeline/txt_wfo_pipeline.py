from __future__ import annotations

import json
import math
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from mqre_v2.io.txt_parser import parse_xs_txt
from mqre_v2.validation.decision import score_wfo_summary
from mqre_v2.validation.wfo import (
    TxtWfoInput,
    WfoGateConfig,
    build_txt_evaluate_fn,
    default_optimize_fn,
    run_wfo,
)

WINDOW_CONFIG_KEYS = {
    "train_months",
    "gap_months",
    "test_months",
    "step_months",
}

GATE_CONFIG_KEYS = {
    "min_test_trade_count",
    "max_test_mdd",
    "min_test_pf",
    "min_pass_rate",
    "require_positive_total_profit",
}


def run_txt_wfo_pipeline(
    txt_folder: str,
    start_date: date,
    end_date: date,
    gate_config: dict,
) -> list[dict]:
    folder = Path(txt_folder)
    if not folder.is_dir():
        raise NotADirectoryError(f"txt_folder is not a directory: {folder}")

    results: list[dict] = []
    for txt_path in sorted(folder.glob("*.txt")):
        if not txt_path.is_file():
            continue

        strategy_name = txt_path.stem
        try:
            parse_xs_txt(txt_path.read_text(encoding="utf-8-sig"))
            wfo_result = run_wfo(
                start_date=start_date,
                end_date=end_date,
                strategy_name=strategy_name,
                optimize_fn=default_optimize_fn,
                evaluate_fn=build_txt_evaluate_fn(
                    TxtWfoInput(strategy_name=strategy_name, txt_path=str(txt_path))
                ),
                window_kwargs=_build_window_kwargs(gate_config),
                gate_config=_build_gate_config(gate_config),
            )
            summary = wfo_result.summary
            result = {
                "rank": 0,
                "strategy_name": strategy_name,
                "txt_path": str(txt_path),
                "total_test_net_profit": _safe_number(summary.total_test_net_profit),
                "pass_rate": _safe_number(summary.pass_rate),
                "max_test_mdd": _safe_number(summary.max_test_mdd),
                "average_test_pf": _safe_number(summary.average_test_pf),
                "score": _safe_number(score_wfo_summary(summary)),
                "passed": wfo_result.passed,
                "fail_reason": wfo_result.fail_reason,
            }
        except Exception as exc:
            result = _failed_result(
                strategy_name=strategy_name,
                txt_path=txt_path,
                fail_reason=str(exc),
            )

        results.append(result)

    results.sort(key=lambda item: float(item["score"]), reverse=True)
    for rank, result in enumerate(results, start=1):
        result["rank"] = rank
    return results


def export_pipeline_result(result: list[dict], output_path: str) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_strategies": len(result),
        "top_10": result[:10],
        "all_results": result,
    }
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )


def _build_window_kwargs(config: dict[str, Any]) -> dict[str, int]:
    window_kwargs: dict[str, int] = {}
    for key in WINDOW_CONFIG_KEYS:
        if key in config:
            window_kwargs[key] = int(config[key])
    return window_kwargs


def _build_gate_config(config: dict[str, Any]) -> WfoGateConfig:
    gate_kwargs = {key: config[key] for key in GATE_CONFIG_KEYS if key in config}
    if "min_test_trade_count" in gate_kwargs:
        gate_kwargs["min_test_trade_count"] = int(gate_kwargs["min_test_trade_count"])
    if "max_test_mdd" in gate_kwargs:
        gate_kwargs["max_test_mdd"] = float(gate_kwargs["max_test_mdd"])
    if "min_test_pf" in gate_kwargs:
        gate_kwargs["min_test_pf"] = float(gate_kwargs["min_test_pf"])
    if "min_pass_rate" in gate_kwargs:
        gate_kwargs["min_pass_rate"] = float(gate_kwargs["min_pass_rate"])
    if "require_positive_total_profit" in gate_kwargs:
        gate_kwargs["require_positive_total_profit"] = bool(
            gate_kwargs["require_positive_total_profit"]
        )
    return WfoGateConfig(**gate_kwargs)


def _failed_result(strategy_name: str, txt_path: Path, fail_reason: str) -> dict:
    return {
        "rank": 0,
        "strategy_name": strategy_name,
        "txt_path": str(txt_path),
        "total_test_net_profit": 0.0,
        "pass_rate": 0.0,
        "max_test_mdd": 0.0,
        "average_test_pf": 0.0,
        "score": 0.0,
        "passed": False,
        "fail_reason": fail_reason,
    }


def _safe_number(value: float | int) -> float | str:
    number = float(value)
    if math.isnan(number):
        return "NaN"
    if math.isinf(number):
        return "Infinity" if number > 0 else "-Infinity"
    return number
