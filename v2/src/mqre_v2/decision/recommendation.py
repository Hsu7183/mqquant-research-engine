from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class PromotionRecommendation:
    recommend_promote: bool
    strategy_name: str
    score: float
    reason: str
    risk_warnings: list[str]
    requires_human_review: bool = True


def generate_promotion_recommendation(
    ranking_report: dict,
    min_score: float = 100.0,
    min_pass_rate: float = 0.6,
    max_mdd: float = 15000.0,
) -> PromotionRecommendation:
    top_10 = ranking_report.get("top_10")
    if not top_10:
        raise ValueError("ranking report top_10 cannot be empty")

    candidate = top_10[0]
    strategy_name = str(candidate["strategy_name"])
    score = float(candidate["score"])
    pass_rate = float(candidate["pass_rate"])
    max_test_mdd = float(candidate["max_test_mdd"])
    total_test_net_profit = float(candidate["total_test_net_profit"])

    risk_warnings: list[str] = []
    if score < min_score:
        risk_warnings.append("score below minimum")
    if pass_rate < min_pass_rate:
        risk_warnings.append("pass_rate below minimum")
    if max_test_mdd > max_mdd:
        risk_warnings.append("max_test_mdd above maximum")
    if total_test_net_profit <= 0:
        risk_warnings.append("total_test_net_profit not positive")

    recommend_promote = not risk_warnings
    reason = (
        "candidate passed promotion thresholds"
        if recommend_promote
        else "candidate did not pass promotion thresholds"
    )

    return PromotionRecommendation(
        recommend_promote=recommend_promote,
        strategy_name=strategy_name,
        score=score,
        reason=reason,
        risk_warnings=risk_warnings,
    )


def recommendation_to_dict(rec: PromotionRecommendation) -> dict:
    return asdict(rec)


def export_recommendation_report(
    ranking_report_path: str,
    output_path: str,
    min_score: float = 100.0,
    min_pass_rate: float = 0.6,
    max_mdd: float = 15000.0,
) -> dict:
    source = Path(ranking_report_path)
    ranking_report = json.loads(source.read_text(encoding="utf-8"))
    recommendation = generate_promotion_recommendation(
        ranking_report,
        min_score=min_score,
        min_pass_rate=min_pass_rate,
        max_mdd=max_mdd,
    )
    payload = {
        "generated_at": _generated_at(),
        "source_report": ranking_report_path,
        "recommendation": recommendation_to_dict(recommendation),
    }

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    return payload


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat()
