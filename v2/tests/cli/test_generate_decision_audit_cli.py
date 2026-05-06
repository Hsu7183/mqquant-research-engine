import json

from mqre_v2.cli.generate_decision_audit import main


def test_generate_decision_audit_cli_outputs_json(tmp_path, capsys) -> None:
    artifact_dir = tmp_path / "latest"
    artifact_dir.mkdir()
    (artifact_dir / "ranking.json").write_text(
        json.dumps(
            [
                {
                    "strategy_id": "1001plus_0001",
                    "score": 125.0,
                    "profit_factor": 1.7,
                    "trade_count": 120,
                    "max_drawdown": 9000.0,
                }
            ]
        ),
        encoding="utf-8",
    )
    (artifact_dir / "oos_summary.json").write_text(
        json.dumps({"oos_sharpe": 1.2, "oos_return": 0.08, "oos_mdd": 8000.0}),
        encoding="utf-8",
    )
    (artifact_dir / "wfo_summary.json").write_text(
        json.dumps({"avg_sharpe": 1.1, "pass_rate": 0.75, "stability_score": 0.7}),
        encoding="utf-8",
    )
    (artifact_dir / "risk_report.json").write_text(
        json.dumps({"max_dd": 8500.0, "ulcer_index": 3.5, "recovery_days": 12}),
        encoding="utf-8",
    )

    exit_code = main(["--artifact-dir", str(artifact_dir)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["promotion_decision"] == "promote"
    assert payload["recommend_promote"] is True
    assert (artifact_dir / "decision_audit.json").is_file()


def test_generate_decision_audit_cli_can_fail_threshold(tmp_path, capsys) -> None:
    artifact_dir = tmp_path / "latest"
    artifact_dir.mkdir()
    (artifact_dir / "ranking.json").write_text(
        json.dumps(
            [
                {
                    "strategy_id": "weak",
                    "score": 50.0,
                    "profit_factor": 0.9,
                    "trade_count": 10,
                    "max_drawdown": 30000.0,
                }
            ]
        ),
        encoding="utf-8",
    )
    (artifact_dir / "oos_summary.json").write_text(
        json.dumps({"oos_sharpe": 0.2, "oos_return": -0.01, "oos_mdd": 30000.0}),
        encoding="utf-8",
    )
    (artifact_dir / "wfo_summary.json").write_text(
        json.dumps({"avg_sharpe": 0.3, "pass_rate": 0.2, "stability_score": 0.2}),
        encoding="utf-8",
    )
    (artifact_dir / "risk_report.json").write_text(
        json.dumps({"max_dd": 30000.0, "ulcer_index": 12.0, "recovery_days": 90}),
        encoding="utf-8",
    )

    main(["--artifact-dir", str(artifact_dir)])
    payload = json.loads(capsys.readouterr().out)

    assert payload["promotion_decision"] == "reject"
    assert payload["recommend_promote"] is False
    assert "trade_count below minimum" in payload["risk_warnings"]
