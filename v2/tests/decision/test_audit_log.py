import csv
import json

from mqre_v2.decision.audit_log import (
    DecisionAuditRecord,
    append_decision_audit,
    read_decision_audit,
)
from mqre_v2.decision.recommendation import export_recommendation_report


def _record(strategy_name: str = "alpha") -> DecisionAuditRecord:
    return DecisionAuditRecord(
        timestamp="2026-05-06T00:00:00+00:00",
        run_id="20260506_alpha_batch001",
        strategy_name=strategy_name,
        score=120.0,
        recommend_promote=True,
        reason="candidate passed promotion thresholds",
        risk_warnings=["score below minimum", "pass_rate below minimum"],
        requires_human_review=True,
        source_report_path="reports/ranking.json",
    )


def _ranking_report() -> dict:
    return {
        "run_id": "20260506_alpha_batch001",
        "generated_at": "2026-05-06T00:00:00+00:00",
        "summary": {
            "total_strategies": 1,
            "valid_strategies": 1,
        },
        "top_10": [
            {
                "rank": 1,
                "strategy_name": "alpha",
                "score": 90.0,
                "total_test_net_profit": 50000.0,
                "pass_rate": 0.5,
                "max_test_mdd": 10000.0,
                "average_test_pf": 1.5,
            }
        ],
        "all_results": [],
    }


def test_append_decision_audit_creates_csv(tmp_path) -> None:
    csv_path = tmp_path / "decision_audit_log.csv"

    append_decision_audit(str(csv_path), _record())

    assert csv_path.is_file()
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert rows[0]["strategy_name"] == "alpha"


def test_read_decision_audit_reads_records(tmp_path) -> None:
    csv_path = tmp_path / "decision_audit_log.csv"
    append_decision_audit(str(csv_path), _record())

    records = read_decision_audit(str(csv_path))

    assert len(records) == 1
    assert records[0].strategy_name == "alpha"
    assert records[0].recommend_promote is True
    assert records[0].requires_human_review is True


def test_multiple_append_preserves_all_rows(tmp_path) -> None:
    csv_path = tmp_path / "decision_audit_log.csv"

    append_decision_audit(str(csv_path), _record("alpha"))
    append_decision_audit(str(csv_path), _record("beta"))
    records = read_decision_audit(str(csv_path))

    assert [record.strategy_name for record in records] == ["alpha", "beta"]


def test_risk_warnings_are_serialized_with_separator(tmp_path) -> None:
    csv_path = tmp_path / "decision_audit_log.csv"

    append_decision_audit(str(csv_path), _record())
    raw = csv_path.read_text(encoding="utf-8")
    records = read_decision_audit(str(csv_path))

    assert "score below minimum|pass_rate below minimum" in raw
    assert records[0].risk_warnings == [
        "score below minimum",
        "pass_rate below minimum",
    ]


def test_audit_log_integrates_with_recommendation_export(tmp_path) -> None:
    ranking_path = tmp_path / "ranking.json"
    recommendation_path = tmp_path / "promotion_recommendation.json"
    audit_path = tmp_path / "decision_audit_log.csv"
    ranking_path.write_text(json.dumps(_ranking_report()), encoding="utf-8")

    payload = export_recommendation_report(
        str(ranking_path),
        str(recommendation_path),
        min_score=100.0,
        min_pass_rate=0.6,
        audit_log_path=str(audit_path),
    )
    records = read_decision_audit(str(audit_path))

    assert payload["recommendation"]["recommend_promote"] is False
    assert len(records) == 1
    assert records[0].run_id == "20260506_alpha_batch001"
    assert records[0].strategy_name == "alpha"
    assert "score below minimum" in records[0].risk_warnings
    assert "pass_rate below minimum" in records[0].risk_warnings
