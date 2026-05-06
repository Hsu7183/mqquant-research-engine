from __future__ import annotations

import json
from pathlib import Path

from mqre_v2.cli.run_l1_l4_pipeline import main


def test_run_l1_l4_pipeline_cli_runs_full_flow(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    m1_path = tmp_path / "m1.txt"
    _write_m1_fixture(m1_path)

    exit_code = main(
        [
            "--m1-path",
            str(m1_path),
            "--strategy-name",
            "l1_l4_demo",
            "--start-date",
            "2020-01-01",
            "--end-date",
            "2024-12-31",
            "--output-ranking-json",
            "runs/latest/reports/ranking.json",
            "--forward-log-path",
            "reports/forward_test_log.csv",
            "--recommendation-output-path",
            "reports/auto_promotion_recommendation.json",
            "--audit-log-path",
            "reports/decision_audit_log.csv",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    ranking_path = tmp_path / "runs" / "latest" / "reports" / "ranking.json"
    detail_path = (
        tmp_path
        / "runs"
        / "latest"
        / "reports"
        / "details"
        / "l1_l4_demo.json"
    )
    forward_log_path = tmp_path / "reports" / "forward_test_log.csv"
    recommendation_path = tmp_path / "reports" / "auto_promotion_recommendation.json"
    audit_log_path = tmp_path / "reports" / "decision_audit_log.csv"

    assert exit_code == 0
    assert payload["strategy_name"] == "l1_l4_demo"
    assert payload["trades_generated"] == 1
    assert payload["ranking_json"] == "runs/latest/reports/ranking.json"
    assert payload["detail_reports_count"] == 1
    assert "recommend_promote" in payload
    assert "reason" in payload
    assert payload["requires_human_review"] is True
    assert ranking_path.is_file()
    assert detail_path.is_file()
    assert forward_log_path.is_file()
    assert recommendation_path.is_file()
    assert audit_log_path.is_file()

    ranking = json.loads(ranking_path.read_text(encoding="utf-8"))
    detail = json.loads(detail_path.read_text(encoding="utf-8"))
    recommendation = json.loads(recommendation_path.read_text(encoding="utf-8"))

    assert ranking["run_id"] == "latest"
    assert ranking["top_10"][0]["strategy_name"] == "l1_l4_demo"
    assert detail["strategy_name"] == "l1_l4_demo"
    assert detail["weekly_pnl"]
    assert recommendation["recommendation"]["strategy_name"] == "l1_l4_demo"
    assert "l1_l4_demo" in audit_log_path.read_text(encoding="utf-8")


def _write_m1_fixture(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "2023/03/01 08:48 100 115 100 115",
                "2023/03/01 08:49 100 100 100 100",
                "2023/03/01 08:50 130 130 130 130",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
