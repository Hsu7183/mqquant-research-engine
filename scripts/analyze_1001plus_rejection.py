from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "runs" / "latest"
OUTPUT_PATH = ROOT / "docs" / "strategy" / "1001plus_rejection_analysis_20260507.md"


def main() -> int:
    decision = _load_json(RUN_DIR / "decision_audit.json")
    ranking = _load_json(RUN_DIR / "ranking.json")
    oos_summary = _load_json(RUN_DIR / "oos_summary.json")
    wfo_summary = _load_json(RUN_DIR / "wfo_summary.json")
    risk_report = _load_json(RUN_DIR / "risk_report.json")

    if not isinstance(decision, dict):
        raise ValueError("decision_audit.json must be an object")
    if not isinstance(ranking, list) or not ranking:
        raise ValueError("ranking.json must be a non-empty list")

    checks = _collect_checks(
        decision=decision,
        ranking=ranking[0],
        oos_summary=oos_summary if isinstance(oos_summary, dict) else {},
        wfo_summary=wfo_summary if isinstance(wfo_summary, dict) else {},
        risk_report=risk_report if isinstance(risk_report, dict) else {},
    )
    failed, warnings, passed = _classify_checks(checks)
    bottleneck = _bottleneck(failed, warnings)
    report = _build_report(
        decision=decision,
        failed=failed,
        warnings=warnings,
        passed=passed,
        bottleneck=bottleneck,
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")
    print(f"wrote {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"bottleneck={bottleneck}")
    return 0


def _load_json(path: Path) -> Any:
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_checks(
    decision: dict[str, Any],
    ranking: dict[str, Any],
    oos_summary: dict[str, Any],
    wfo_summary: dict[str, Any],
    risk_report: dict[str, Any],
) -> list[dict[str, Any]]:
    audit_checks = decision.get("checks", {})
    rows: list[dict[str, Any]] = []

    rows.extend(
        [
            _min_check("ranking", "score", ranking.get("score"), _audit_threshold(audit_checks, "ranking", "min_score", 100.0)),
            _min_check("ranking", "profit_factor", ranking.get("profit_factor"), _audit_threshold(audit_checks, "ranking", "min_profit_factor", 1.1)),
            _min_check("ranking", "trade_count", ranking.get("trade_count"), _audit_threshold(audit_checks, "ranking", "min_trade_count", 30)),
            _min_check("oos", "oos_sharpe", oos_summary.get("oos_sharpe"), _audit_threshold(audit_checks, "oos", "min_oos_sharpe", 1.0)),
            _min_check("oos", "oos_return", oos_summary.get("oos_return"), _audit_threshold(audit_checks, "oos", "min_oos_return", 0.0)),
            _max_check("oos", "oos_mdd", oos_summary.get("oos_mdd"), _audit_threshold(audit_checks, "oos", "max_oos_mdd", 15000.0)),
            _min_check("wfo", "pass_rate", wfo_summary.get("pass_rate"), _audit_threshold(audit_checks, "wfo", "min_pass_rate", 0.6)),
            _min_check("wfo", "avg_sharpe", wfo_summary.get("avg_sharpe"), _audit_threshold(audit_checks, "wfo", "min_avg_sharpe", 1.0)),
            _min_check("wfo", "stability_score", wfo_summary.get("stability_score"), _audit_threshold(audit_checks, "wfo", "min_stability_score", 0.6)),
            _max_check("risk", "max_dd", risk_report.get("max_dd"), _audit_threshold(audit_checks, "risk", "max_risk_drawdown", 15000.0)),
            _max_check("risk", "ulcer_index", risk_report.get("ulcer_index"), _audit_threshold(audit_checks, "risk", "max_ulcer_index", 10.0)),
            _max_check("risk", "recovery_days", risk_report.get("recovery_days"), _audit_threshold(audit_checks, "risk", "max_recovery_days", 60)),
        ]
    )

    forward = audit_checks.get("forward", {}) if isinstance(audit_checks, dict) else {}
    if isinstance(forward, dict):
        rows.append(
            _min_check(
                "forward",
                "stability_score",
                forward.get("stability_score", decision.get("forward_score")),
                forward.get("min_forward_score", 60.0),
            )
        )
        rows.append(
            {
                "section": "forward",
                "check": "forward_status",
                "value": str(forward.get("forward_status", decision.get("forward_status", ""))),
                "threshold": "not bad",
                "direction": "status",
                "margin": "",
                "severity": "passed"
                if str(forward.get("forward_status", decision.get("forward_status", ""))) != "bad"
                else "failed",
            }
        )

    return rows


def _audit_threshold(
    checks: Any,
    section: str,
    key: str,
    fallback: float,
) -> float:
    if isinstance(checks, dict):
        section_data = checks.get(section, {})
        if isinstance(section_data, dict) and key in section_data:
            return _as_float(section_data[key])
    return fallback


def _min_check(
    section: str,
    name: str,
    value: Any,
    minimum: Any,
) -> dict[str, Any]:
    number = _as_float(value)
    threshold = _as_float(minimum)
    margin = number - threshold
    return {
        "section": section,
        "check": name,
        "value": number,
        "threshold": threshold,
        "direction": ">=",
        "margin": margin,
        "severity": _severity_min(number, threshold),
    }


def _max_check(
    section: str,
    name: str,
    value: Any,
    maximum: Any,
) -> dict[str, Any]:
    number = _as_float(value)
    threshold = _as_float(maximum)
    margin = threshold - number
    return {
        "section": section,
        "check": name,
        "value": number,
        "threshold": threshold,
        "direction": "<=",
        "margin": margin,
        "severity": _severity_max(number, threshold),
    }


def _severity_min(value: float, threshold: float) -> str:
    if value >= threshold:
        return "passed"
    if threshold == 0:
        return "failed"
    ratio = value / threshold
    return "warning" if ratio >= 0.8 else "failed"


def _severity_max(value: float, threshold: float) -> str:
    if value <= threshold:
        return "passed"
    if threshold == 0:
        return "failed"
    ratio = value / threshold
    return "warning" if ratio <= 1.2 else "failed"


def _classify_checks(
    checks: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    failed = [row for row in checks if row["severity"] == "failed"]
    warnings = [row for row in checks if row["severity"] == "warning"]
    passed = [row for row in checks if row["severity"] == "passed"]
    return failed, warnings, passed


def _bottleneck(
    failed: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> str:
    counts = {}
    for row in failed:
        counts[row["section"]] = counts.get(row["section"], 0) + 2
    for row in warnings:
        counts[row["section"]] = counts.get(row["section"], 0) + 1
    if not counts:
        return "none"
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ordered[0][0]


def _build_report(
    decision: dict[str, Any],
    failed: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    passed: list[dict[str, Any]],
    bottleneck: str,
) -> str:
    lines = [
        "# 1001plus Rejection Analysis",
        "",
        "## 1. Decision Summary",
        "",
        f"- challenger_strategy: `{decision.get('challenger_strategy', '')}`",
        f"- promotion_decision: `{decision.get('promotion_decision', '')}`",
        f"- reason: `{decision.get('reason', '')}`",
        f"- score: `{decision.get('score', '')}`",
        f"- forward_status: `{decision.get('forward_status', '')}`",
        f"- rejection_bottleneck: `{bottleneck}`",
        "",
        "## 2. Failed Checks Table",
        "",
        _checks_table(failed),
        "",
        "## 3. Warning Checks Table",
        "",
        _checks_table(warnings),
        "",
        "## 4. Passed Checks Table",
        "",
        _checks_table(passed),
        "",
        "## 5. 主要 Reject Bottleneck",
        "",
        *_bottleneck_notes(bottleneck, failed, warnings),
        "",
        "## 6. 下一步建議",
        "",
        *_next_steps(bottleneck, failed, warnings),
        "",
    ]
    return "\n".join(lines)


def _checks_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "無。"
    lines = [
        "| section | check | value | rule | threshold | margin | severity |",
        "|---|---|---:|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row['section']} | "
            f"{row['check']} | "
            f"{_fmt(row['value'])} | "
            f"{row['direction']} | "
            f"{_fmt(row['threshold'])} | "
            f"{_fmt(row['margin'])} | "
            f"{row['severity']} |"
        )
    return "\n".join(lines)


def _bottleneck_notes(
    bottleneck: str,
    failed: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> list[str]:
    related = [row for row in [*failed, *warnings] if row["section"] == bottleneck]
    if bottleneck == "none":
        return ["- 目前沒有明顯 failed / warning checks。"]
    lines = [f"- 主要瓶頸分類：`{bottleneck}`。"]
    for row in related:
        lines.append(
            f"- `{row['check']}` 未達標：value `{_fmt(row['value'])}`，"
            f"threshold `{_fmt(row['threshold'])}`，margin `{_fmt(row['margin'])}`。"
        )
    return lines


def _next_steps(
    bottleneck: str,
    failed: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> list[str]:
    sections = {row["section"] for row in [*failed, *warnings]}
    lines = []
    lines.append(
        "- risk 問題："
        + ("是，risk checks 有 failed/warning。" if "risk" in sections else "目前不是主要問題。")
    )
    lines.append(
        "- OOS 問題："
        + ("是，OOS checks 有 failed/warning。" if "oos" in sections else "目前 OOS checks 通過。")
    )
    lines.append(
        "- WFO 問題："
        + ("是，WFO checks 有 failed/warning。" if "wfo" in sections else "目前不是主要問題。")
    )
    lines.append(
        "- forward 問題："
        + ("是，forward checks 有 failed/warning。" if "forward" in sections else "目前 forward checks 通過。")
    )
    lines.append(
        "- generator / threshold："
        + _generator_threshold_advice(bottleneck, sections)
    )
    return lines


def _generator_threshold_advice(bottleneck: str, sections: set[str]) -> str:
    if bottleneck in {"wfo", "risk"}:
        return "建議先調整 generator 的風險與穩健性方向，不建議先放寬 decision threshold。"
    if "ranking" in sections:
        return "score / PF 不足，應先改善 generator 或成本後績效，不建議直接放寬升級門檻。"
    if sections == {"forward"}:
        return "可優先檢查 forward 記錄品質與樣本期，不急著調整 generator。"
    return "可維持目前 threshold，先累積更多 challenger 與 plateau 分析。"


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _fmt(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{number:.6f}".rstrip("0").rstrip(".")


if __name__ == "__main__":
    raise SystemExit(main())
