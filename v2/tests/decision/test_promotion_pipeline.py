import json

from mqre_v2.decision.audit_log import read_decision_audit
from mqre_v2.decision.promotion_pipeline import (
    AutoPromotionConfig,
    run_auto_promotion_pipeline,
)


def _ranking_report(**overrides) -> dict:
    candidate = {
        "rank": 1,
        "strategy_name": "alpha",
        "score": 120.0,
        "total_test_net_profit": 50000.0,
        "pass_rate": 0.75,
        "max_test_mdd": 10000.0,
        "average_test_pf": 1.5,
    }
    candidate.update(overrides)
    return {
        "run_id": "20260506_alpha_batch001",
        "generated_at": "2026-05-06T00:00:00+00:00",
        "summary": {
            "total_strategies": 1,
            "valid_strategies": 1,
        },
        "top_10": [candidate],
        "all_results": [candidate],
    }


def test_pipeline_writes_recommendation_json(tmp_path) -> None:
    ranking_path = tmp_path / "ranking.json"
    recommendation_path = tmp_path / "recommendation.json"
    audit_path = tmp_path / "decision_audit_log.csv"
    ranking_path.write_text(json.dumps(_ranking_report()), encoding="utf-8")

    summary = run_auto_promotion_pipeline(
        AutoPromotionConfig(
            ranking_report_path=str(ranking_path),
            recommendation_output_path=str(recommendation_path),
            audit_log_path=str(audit_path),
        )
    )
    payload = json.loads(recommendation_path.read_text(encoding="utf-8"))

    assert recommendation_path.is_file()
    assert summary["recommend_promote"] is True
    assert payload["recommendation"]["strategy_name"] == "alpha"


def test_pipeline_writes_audit_log(tmp_path) -> None:
    ranking_path = tmp_path / "ranking.json"
    recommendation_path = tmp_path / "recommendation.json"
    audit_path = tmp_path / "decision_audit_log.csv"
    ranking_path.write_text(json.dumps(_ranking_report()), encoding="utf-8")

    run_auto_promotion_pipeline(
        AutoPromotionConfig(
            ranking_report_path=str(ranking_path),
            recommendation_output_path=str(recommendation_path),
            audit_log_path=str(audit_path),
        )
    )
    records = read_decision_audit(str(audit_path))

    assert len(records) == 1
    assert records[0].run_id == "20260506_alpha_batch001"
    assert records[0].strategy_name == "alpha"


def test_pipeline_summary_contains_review_fields(tmp_path) -> None:
    ranking_path = tmp_path / "ranking.json"
    recommendation_path = tmp_path / "recommendation.json"
    audit_path = tmp_path / "decision_audit_log.csv"
    ranking_path.write_text(json.dumps(_ranking_report()), encoding="utf-8")

    summary = run_auto_promotion_pipeline(
        AutoPromotionConfig(
            ranking_report_path=str(ranking_path),
            recommendation_output_path=str(recommendation_path),
            audit_log_path=str(audit_path),
        )
    )

    assert summary == {
        "recommendation_output_path": str(recommendation_path),
        "audit_log_path": str(audit_path),
        "recommend_promote": True,
        "strategy_name": "alpha",
        "score": 120.0,
        "reason": "candidate passed promotion thresholds",
        "risk_warnings": [],
        "requires_human_review": True,
    }


def test_pipeline_blocks_candidate_below_threshold(tmp_path) -> None:
    ranking_path = tmp_path / "ranking.json"
    recommendation_path = tmp_path / "recommendation.json"
    audit_path = tmp_path / "decision_audit_log.csv"
    ranking_path.write_text(
        json.dumps(_ranking_report(score=90.0)),
        encoding="utf-8",
    )

    summary = run_auto_promotion_pipeline(
        AutoPromotionConfig(
            ranking_report_path=str(ranking_path),
            recommendation_output_path=str(recommendation_path),
            audit_log_path=str(audit_path),
            min_score=100.0,
        )
    )

    assert summary["recommend_promote"] is False
    assert "score below minimum" in summary["risk_warnings"]
