from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "runs" / "latest"
OUTPUT_PATH = ROOT / "docs" / "strategy" / "1001plus_wfo_failure_analysis_20260507.md"


def main() -> int:
    wfo_summary = _load_json(RUN_DIR / "wfo_summary.json")
    ranking = _load_json(RUN_DIR / "ranking.json")
    decision = _load_json(RUN_DIR / "decision_audit.json")

    if not isinstance(wfo_summary, dict):
        raise ValueError("wfo_summary.json must be an object")
    if not isinstance(ranking, list) or not ranking:
        raise ValueError("ranking.json must be a non-empty list")
    if not isinstance(decision, dict):
        raise ValueError("decision_audit.json must be an object")

    rounds = wfo_summary.get("rounds", [])
    if not isinstance(rounds, list) or not rounds:
        raise ValueError("wfo_summary.json must include non-empty rounds")

    report = build_report(
        wfo_summary=wfo_summary,
        top_strategy=ranking[0],
        decision=decision,
        rounds=rounds,
    )
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")

    print(f"wrote {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"pass_rate={_fmt(wfo_summary.get('pass_rate'))}")
    print(f"stability_score={_fmt(wfo_summary.get('stability_score'))}")
    print(f"failed_rounds={len(_failed_rounds(rounds))}/{len(rounds)}")
    print(f"failure_pattern={_failure_pattern(rounds, decision)}")
    return 0


def build_report(
    wfo_summary: dict[str, Any],
    top_strategy: dict[str, Any],
    decision: dict[str, Any],
    rounds: list[Any],
) -> str:
    failed = _failed_rounds(rounds)
    passed = _passed_rounds(rounds)
    wfo_checks = _wfo_checks(decision)
    pattern = _failure_pattern(rounds, decision)
    weakness_notes = _top_challenger_weaknesses(
        top_strategy=top_strategy,
        wfo_summary=wfo_summary,
        decision=decision,
        failed_rounds=failed,
    )

    lines = [
        "# 1001plus WFO Failure Analysis - 2026-05-07",
        "",
        "## 1. WFO Summary",
        "",
        f"- challenger_strategy: `{decision.get('challenger_strategy', top_strategy.get('strategy_id', ''))}`",
        f"- promotion_decision: `{decision.get('promotion_decision', '')}`",
        f"- decision_reason: `{decision.get('reason', '')}`",
        f"- WFO pass_rate: `{_fmt(wfo_summary.get('pass_rate'))}`",
        f"- WFO stability_score: `{_fmt(wfo_summary.get('stability_score'))}`",
        f"- WFO avg_sharpe: `{_fmt(wfo_summary.get('avg_sharpe'))}`",
        f"- failed_rounds: `{len(failed)}/{len(rounds)}`",
        "",
        "Decision WFO thresholds:",
        "",
        _wfo_threshold_table(wfo_checks),
        "",
        "## 2. Failed Rounds Table",
        "",
        _rounds_table(failed),
        "",
        "## 3. Passed Rounds Table",
        "",
        _rounds_table(passed),
        "",
        "## 4. Failure Pattern",
        "",
        f"- main_pattern: `{pattern}`",
        *_failure_pattern_notes(rounds, wfo_checks),
        "",
        "## 5. Interpretation",
        "",
        *weakness_notes,
        "",
        "The risk-constrained generator reduced portfolio-level risk metrics compared with the default 300-run, but WFO validation still failed. The failure is not caused by a single bad round only. Every WFO round is marked as failed, and most rounds have negative return. This means the current challenger set does not yet show stable cross-window behavior.",
        "",
        "The baseline should not be upgraded from this run. The correct next step is to inspect WFO round behavior and regime dependency, not to relax the promotion threshold.",
        "",
        "## 6. Next Steps",
        "",
        "1. Add WFO round-level diagnostics by year or market regime.",
        "2. Build regime buckets to separate trend, range, volatile breakout, and afternoon trend behavior.",
        "3. Check whether WFO failures cluster in specific years or specific volatility regimes.",
        "4. Narrow the generator range only after identifying which parameters are stable across rounds.",
        "5. Consider adding controlled exit variations such as time stop or trailing stop, while keeping the 1001plus entry structure anchored.",
        "6. Re-run risk-constrained candidates after WFO diagnostics, then compare pass_rate and stability_score before any baseline decision.",
        "",
    ]
    return "\n".join(lines)


def _load_json(path: Path) -> Any:
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _failed_rounds(rounds: list[Any]) -> list[dict[str, Any]]:
    return [row for row in rounds if isinstance(row, dict) and not bool(row.get("passed"))]


def _passed_rounds(rounds: list[Any]) -> list[dict[str, Any]]:
    return [row for row in rounds if isinstance(row, dict) and bool(row.get("passed"))]


def _wfo_checks(decision: dict[str, Any]) -> dict[str, Any]:
    checks = decision.get("checks", {})
    if isinstance(checks, dict):
        wfo = checks.get("wfo", {})
        if isinstance(wfo, dict):
            return wfo
    return {}


def _wfo_threshold_table(wfo_checks: dict[str, Any]) -> str:
    if not wfo_checks:
        return "No WFO threshold data found in decision_audit.json."
    rows = [
        ("pass_rate", wfo_checks.get("pass_rate"), ">=", wfo_checks.get("min_pass_rate")),
        ("avg_sharpe", wfo_checks.get("avg_sharpe"), ">=", wfo_checks.get("min_avg_sharpe")),
        (
            "stability_score",
            wfo_checks.get("stability_score"),
            ">=",
            wfo_checks.get("min_stability_score"),
        ),
    ]
    lines = [
        "| check | value | rule | threshold | status |",
        "|---|---:|---|---:|---|",
    ]
    for name, value, rule, threshold in rows:
        value_num = _to_float(value)
        threshold_num = _to_float(threshold)
        status = "pass" if value_num >= threshold_num else "fail"
        lines.append(
            f"| {name} | {_fmt(value_num)} | {rule} | {_fmt(threshold_num)} | {status} |"
        )
    return "\n".join(lines)


def _rounds_table(rounds: list[dict[str, Any]]) -> str:
    if not rounds:
        return "No rounds in this category."
    lines = [
        "| round_id | return | sharpe | max_dd | trade_count | passed |",
        "|---:|---:|---:|---:|---:|---|",
    ]
    for row in rounds:
        lines.append(
            "| "
            f"{row.get('round_id', '')} | "
            f"{_fmt(row.get('return'))} | "
            f"{_fmt(row.get('sharpe'))} | "
            f"{_fmt(row.get('max_drawdown'))} | "
            f"{row.get('trade_count', '')} | "
            f"{bool(row.get('passed'))} |"
        )
    return "\n".join(lines)


def _failure_pattern(rounds: list[Any], decision: dict[str, Any]) -> str:
    failed = _failed_rounds(rounds)
    negative_returns = [
        row for row in failed if _to_float(row.get("return")) < 0.0
    ]
    wfo = _wfo_checks(decision)
    pass_rate = _to_float(wfo.get("pass_rate"))
    stability = _to_float(wfo.get("stability_score"))
    avg_sharpe = _to_float(wfo.get("avg_sharpe"))

    if len(failed) == len(rounds) and len(negative_returns) >= len(rounds) - 1:
        return "all rounds failed; returns are negative in most WFO windows"
    if pass_rate == 0 and stability == 0:
        return "zero pass rate and zero stability score"
    if avg_sharpe < _to_float(wfo.get("min_avg_sharpe", 1.0)):
        return "average WFO sharpe below threshold"
    return "mixed WFO weakness"


def _failure_pattern_notes(
    rounds: list[Any],
    wfo_checks: dict[str, Any],
) -> list[str]:
    failed = _failed_rounds(rounds)
    negative = sum(1 for row in failed if _to_float(row.get("return")) < 0.0)
    positive = sum(1 for row in failed if _to_float(row.get("return")) > 0.0)
    trade_counts = [_to_float(row.get("trade_count")) for row in failed]
    max_dd_values = [_to_float(row.get("max_drawdown")) for row in failed]
    sharpe_values = [_to_float(row.get("sharpe")) for row in failed]

    notes = [
        f"- failed_round_count: `{len(failed)}`",
        f"- failed_rounds_with_negative_return: `{negative}`",
        f"- failed_rounds_with_positive_return: `{positive}`",
        f"- avg_failed_round_sharpe: `{_fmt(_avg(sharpe_values))}`",
        f"- avg_failed_round_max_dd: `{_fmt(_avg(max_dd_values))}`",
        f"- avg_failed_round_trade_count: `{_fmt(_avg(trade_counts))}`",
    ]
    if wfo_checks:
        notes.extend(
            [
                f"- pass_rate gap: `{_fmt(_to_float(wfo_checks.get('pass_rate')) - _to_float(wfo_checks.get('min_pass_rate')) )}`",
                f"- avg_sharpe gap: `{_fmt(_to_float(wfo_checks.get('avg_sharpe')) - _to_float(wfo_checks.get('min_avg_sharpe')) )}`",
                f"- stability_score gap: `{_fmt(_to_float(wfo_checks.get('stability_score')) - _to_float(wfo_checks.get('min_stability_score')) )}`",
            ]
        )
    return notes


def _top_challenger_weaknesses(
    top_strategy: dict[str, Any],
    wfo_summary: dict[str, Any],
    decision: dict[str, Any],
    failed_rounds: list[dict[str, Any]],
) -> list[str]:
    wfo = _wfo_checks(decision)
    notes = [
        f"- Top challenger: `{top_strategy.get('strategy_id', '')}`",
        f"- Ranking score is only `{_fmt(top_strategy.get('score'))}`, far below the promotion score threshold in decision_audit.",
        f"- WFO pass_rate is `{_fmt(wfo_summary.get('pass_rate'))}`, below the required `{_fmt(wfo.get('min_pass_rate', 0.6))}`.",
        f"- WFO stability_score is `{_fmt(wfo_summary.get('stability_score'))}`, below the required `{_fmt(wfo.get('min_stability_score', 0.6))}`.",
        f"- WFO avg_sharpe is `{_fmt(wfo_summary.get('avg_sharpe'))}`, below the required `{_fmt(wfo.get('min_avg_sharpe', 1.0))}`.",
    ]
    if failed_rounds:
        worst_return = min(failed_rounds, key=lambda row: _to_float(row.get("return")))
        worst_dd = max(failed_rounds, key=lambda row: _to_float(row.get("max_drawdown")))
        notes.extend(
            [
                f"- Worst return round: round `{worst_return.get('round_id')}` with return `{_fmt(worst_return.get('return'))}`.",
                f"- Worst drawdown round: round `{worst_dd.get('round_id')}` with max_dd `{_fmt(worst_dd.get('max_drawdown'))}`.",
            ]
        )
    return notes


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _fmt(value: Any) -> str:
    number = _to_float(value)
    if abs(number) >= 100:
        return f"{number:.4f}"
    return f"{number:.6f}".rstrip("0").rstrip(".")


if __name__ == "__main__":
    raise SystemExit(main())
