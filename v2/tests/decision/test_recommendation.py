import json

import pytest

from mqre_v2.decision.recommendation import (
    export_recommendation_report,
    generate_promotion_recommendation,
    recommendation_to_dict,
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


def test_high_score_candidate_recommends_promote() -> None:
    recommendation = generate_promotion_recommendation(_ranking_report())

    assert recommendation.recommend_promote is True
    assert recommendation.strategy_name == "alpha"
    assert recommendation.reason == "candidate passed promotion thresholds"
    assert recommendation.risk_warnings == []
    assert recommendation.requires_human_review is True


def test_score_below_threshold_blocks_promotion() -> None:
    recommendation = generate_promotion_recommendation(
        _ranking_report(score=90.0),
        min_score=100.0,
    )

    assert recommendation.recommend_promote is False
    assert "score below minimum" in recommendation.risk_warnings


def test_pass_rate_below_threshold_adds_warning() -> None:
    recommendation = generate_promotion_recommendation(
        _ranking_report(pass_rate=0.4),
        min_pass_rate=0.6,
    )

    assert recommendation.recommend_promote is False
    assert "pass_rate below minimum" in recommendation.risk_warnings


def test_mdd_above_threshold_adds_warning() -> None:
    recommendation = generate_promotion_recommendation(
        _ranking_report(max_test_mdd=20000.0),
        max_mdd=15000.0,
    )

    assert recommendation.recommend_promote is False
    assert "max_test_mdd above maximum" in recommendation.risk_warnings


def test_non_positive_profit_adds_warning() -> None:
    recommendation = generate_promotion_recommendation(
        _ranking_report(total_test_net_profit=0.0),
    )

    assert recommendation.recommend_promote is False
    assert "total_test_net_profit not positive" in recommendation.risk_warnings


def test_empty_top_10_raises() -> None:
    report = _ranking_report()
    report["top_10"] = []

    with pytest.raises(ValueError):
        generate_promotion_recommendation(report)


def test_recommendation_to_dict() -> None:
    recommendation = generate_promotion_recommendation(_ranking_report())
    payload = recommendation_to_dict(recommendation)

    assert payload["recommend_promote"] is True
    assert payload["requires_human_review"] is True


def test_export_recommendation_report_writes_json(tmp_path) -> None:
    ranking_path = tmp_path / "ranking.json"
    output_path = tmp_path / "promotion_recommendation.json"
    ranking_path.write_text(json.dumps(_ranking_report()), encoding="utf-8")

    payload = export_recommendation_report(
        str(ranking_path),
        str(output_path),
        min_score=100.0,
    )
    loaded = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["source_report"] == str(ranking_path)
    assert loaded["generated_at"]
    assert loaded["recommendation"]["recommend_promote"] is True
    assert loaded["recommendation"]["requires_human_review"] is True
