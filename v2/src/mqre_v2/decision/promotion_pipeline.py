from __future__ import annotations

from dataclasses import dataclass

from mqre_v2.decision.recommendation import export_recommendation_report


@dataclass(frozen=True)
class AutoPromotionConfig:
    ranking_report_path: str
    recommendation_output_path: str
    audit_log_path: str
    min_score: float = 100.0
    min_pass_rate: float = 0.6
    max_mdd: float = 15000.0


def run_auto_promotion_pipeline(config: AutoPromotionConfig) -> dict:
    payload = export_recommendation_report(
        ranking_report_path=config.ranking_report_path,
        output_path=config.recommendation_output_path,
        min_score=config.min_score,
        min_pass_rate=config.min_pass_rate,
        max_mdd=config.max_mdd,
        audit_log_path=config.audit_log_path,
    )
    recommendation = payload["recommendation"]

    return {
        "recommendation_output_path": config.recommendation_output_path,
        "audit_log_path": config.audit_log_path,
        "recommend_promote": recommendation["recommend_promote"],
        "strategy_name": recommendation["strategy_name"],
        "score": recommendation["score"],
        "reason": recommendation["reason"],
        "risk_warnings": recommendation["risk_warnings"],
        "requires_human_review": recommendation["requires_human_review"],
    }
