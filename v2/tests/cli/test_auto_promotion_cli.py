import json

from mqre_v2.cli.auto_promotion import main


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
                "score": 120.0,
                "total_test_net_profit": 50000.0,
                "pass_rate": 0.75,
                "max_test_mdd": 10000.0,
                "average_test_pf": 1.5,
            }
        ],
        "all_results": [],
    }


def test_auto_promotion_cli_outputs_json(tmp_path, capsys) -> None:
    ranking_path = tmp_path / "ranking.json"
    recommendation_path = tmp_path / "recommendation.json"
    audit_path = tmp_path / "decision_audit_log.csv"
    ranking_path.write_text(json.dumps(_ranking_report()), encoding="utf-8")

    exit_code = main(
        [
            "--ranking-report-path",
            str(ranking_path),
            "--recommendation-output-path",
            str(recommendation_path),
            "--audit-log-path",
            str(audit_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["recommend_promote"] is True
    assert payload["strategy_name"] == "alpha"
    assert recommendation_path.is_file()
    assert audit_path.is_file()


def test_auto_promotion_cli_outputs_false_when_threshold_fails(tmp_path, capsys) -> None:
    ranking_path = tmp_path / "ranking.json"
    recommendation_path = tmp_path / "recommendation.json"
    audit_path = tmp_path / "decision_audit_log.csv"
    ranking_path.write_text(json.dumps(_ranking_report()), encoding="utf-8")

    main(
        [
            "--ranking-report-path",
            str(ranking_path),
            "--recommendation-output-path",
            str(recommendation_path),
            "--audit-log-path",
            str(audit_path),
            "--min-score",
            "200",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert payload["recommend_promote"] is False
    assert "score below minimum" in payload["risk_warnings"]
