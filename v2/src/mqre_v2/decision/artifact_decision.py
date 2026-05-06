from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ArtifactDecisionConfig:
    baseline_strategy: str = "1001plus_baseline"
    min_score: float = 100.0
    min_profit_factor: float = 1.1
    min_trade_count: int = 30
    min_oos_sharpe: float = 1.0
    min_oos_return: float = 0.0
    max_oos_mdd: float = 15000.0
    min_wfo_pass_rate: float = 0.6
    min_wfo_avg_sharpe: float = 1.0
    min_wfo_stability_score: float = 0.6
    max_risk_drawdown: float = 15000.0
    max_ulcer_index: float = 10.0
    max_recovery_days: int = 60


@dataclass(frozen=True)
class ArtifactDecisionAudit:
    baseline_strategy: str
    challenger_strategy: str
    promotion_decision: str
    reason: str
    timestamp: str
    recommend_promote: bool
    requires_human_review: bool
    score: float
    risk_warnings: list[str]
    checks: dict[str, dict[str, Any]]


def build_decision_audit(
    ranking: Any,
    oos_summary: dict[str, Any],
    wfo_summary: dict[str, Any],
    risk_report: dict[str, Any],
    config: ArtifactDecisionConfig | None = None,
) -> dict[str, Any]:
    cfg = config or ArtifactDecisionConfig()
    candidate = _top_candidate(ranking)

    strategy_id = str(
        candidate.get("strategy_id")
        or candidate.get("strategy_name")
        or "unknown_challenger",
    )
    score = _as_float(candidate.get("score"))
    profit_factor = _as_float(candidate.get("profit_factor", candidate.get("average_test_pf")))
    trade_count = int(_as_float(candidate.get("trade_count", candidate.get("total_test_trade_count"))))
    ranking_mdd = _as_float(candidate.get("max_drawdown", candidate.get("max_test_mdd")))

    oos_sharpe = _as_float(oos_summary.get("oos_sharpe", candidate.get("oos_sharpe")))
    oos_return = _as_float(oos_summary.get("oos_return"))
    oos_mdd = _as_float(oos_summary.get("oos_mdd"), ranking_mdd)

    wfo_pass_rate = _as_float(wfo_summary.get("pass_rate", candidate.get("wfo_pass_rate")))
    wfo_avg_sharpe = _as_float(wfo_summary.get("avg_sharpe"))
    wfo_stability = _as_float(wfo_summary.get("stability_score"))

    risk_max_dd = _as_float(risk_report.get("max_dd"), ranking_mdd)
    ulcer_index = _as_float(risk_report.get("ulcer_index"))
    recovery_days = int(_as_float(risk_report.get("recovery_days")))

    warnings: list[str] = []
    critical = False

    def warn(message: str, is_critical: bool = False) -> None:
        nonlocal critical
        warnings.append(message)
        critical = critical or is_critical

    if score < cfg.min_score:
        warn("score below promotion threshold", score < cfg.min_score * 0.8)
    if profit_factor < cfg.min_profit_factor:
        warn("profit_factor below promotion threshold")
    if trade_count < cfg.min_trade_count:
        warn("trade_count below minimum", True)
    if oos_sharpe < cfg.min_oos_sharpe:
        warn("oos_sharpe below promotion threshold", oos_sharpe < cfg.min_oos_sharpe * 0.5)
    if oos_return <= cfg.min_oos_return:
        warn("oos_return not positive")
    if oos_mdd > cfg.max_oos_mdd:
        warn("oos_mdd above maximum", oos_mdd > cfg.max_oos_mdd * 1.5)
    if wfo_pass_rate < cfg.min_wfo_pass_rate:
        warn("wfo_pass_rate below promotion threshold", wfo_pass_rate < cfg.min_wfo_pass_rate * 0.67)
    if wfo_avg_sharpe < cfg.min_wfo_avg_sharpe:
        warn("wfo_avg_sharpe below promotion threshold")
    if wfo_stability < cfg.min_wfo_stability_score:
        warn("wfo_stability_score below promotion threshold")
    if risk_max_dd > cfg.max_risk_drawdown:
        warn("risk max drawdown above maximum", risk_max_dd > cfg.max_risk_drawdown * 1.5)
    if ulcer_index > cfg.max_ulcer_index:
        warn("ulcer_index above maximum")
    if recovery_days > cfg.max_recovery_days:
        warn("recovery_days above maximum")

    if not warnings:
        promotion_decision = "promote"
        reason = "candidate passed ranking, OOS, WFO, and risk thresholds"
    elif critical:
        promotion_decision = "reject"
        reason = "candidate failed critical promotion thresholds"
    else:
        promotion_decision = "watch"
        reason = "candidate requires watchlist review before promotion"

    payload = ArtifactDecisionAudit(
        baseline_strategy=cfg.baseline_strategy,
        challenger_strategy=strategy_id,
        promotion_decision=promotion_decision,
        reason=reason,
        timestamp=datetime.now(timezone.utc).isoformat(),
        recommend_promote=promotion_decision == "promote",
        requires_human_review=True,
        score=round(score, 6),
        risk_warnings=warnings,
        checks={
            "ranking": {
                "score": round(score, 6),
                "min_score": cfg.min_score,
                "profit_factor": round(profit_factor, 6),
                "min_profit_factor": cfg.min_profit_factor,
                "trade_count": trade_count,
                "min_trade_count": cfg.min_trade_count,
            },
            "oos": {
                "oos_sharpe": round(oos_sharpe, 6),
                "min_oos_sharpe": cfg.min_oos_sharpe,
                "oos_return": round(oos_return, 6),
                "min_oos_return": cfg.min_oos_return,
                "oos_mdd": round(oos_mdd, 6),
                "max_oos_mdd": cfg.max_oos_mdd,
            },
            "wfo": {
                "pass_rate": round(wfo_pass_rate, 6),
                "min_pass_rate": cfg.min_wfo_pass_rate,
                "avg_sharpe": round(wfo_avg_sharpe, 6),
                "min_avg_sharpe": cfg.min_wfo_avg_sharpe,
                "stability_score": round(wfo_stability, 6),
                "min_stability_score": cfg.min_wfo_stability_score,
            },
            "risk": {
                "max_dd": round(risk_max_dd, 6),
                "max_risk_drawdown": cfg.max_risk_drawdown,
                "ulcer_index": round(ulcer_index, 6),
                "max_ulcer_index": cfg.max_ulcer_index,
                "recovery_days": recovery_days,
                "max_recovery_days": cfg.max_recovery_days,
            },
        },
    )
    return asdict(payload)


def export_decision_audit_from_artifacts(
    ranking_path: str,
    oos_summary_path: str,
    wfo_summary_path: str,
    risk_report_path: str,
    output_path: str,
    config: ArtifactDecisionConfig | None = None,
) -> dict[str, Any]:
    payload = build_decision_audit(
        _read_json(ranking_path),
        _read_json(oos_summary_path),
        _read_json(wfo_summary_path),
        _read_json(risk_report_path),
        config=config,
    )
    payload["source_artifacts"] = {
        "ranking": ranking_path,
        "oos_summary": oos_summary_path,
        "wfo_summary": wfo_summary_path,
        "risk_report": risk_report_path,
    }

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return payload


def _read_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _top_candidate(ranking: Any) -> dict[str, Any]:
    if isinstance(ranking, dict):
        rows = ranking.get("top_10") or ranking.get("all_results") or ranking.get("ranking")
    else:
        rows = ranking

    if not isinstance(rows, list) or not rows:
        raise ValueError("ranking must contain at least one strategy")

    candidates = [row for row in rows if isinstance(row, dict)]
    if not candidates:
        raise ValueError("ranking must contain at least one strategy row")

    return max(candidates, key=lambda row: _as_float(row.get("score")))


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return number
