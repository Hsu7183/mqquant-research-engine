import json

import pytest

from mqre_v2.decision.artifact_decision import (
    ArtifactDecisionConfig,
    build_decision_audit,
    export_decision_audit_from_artifacts,
)


def _ranking(**overrides) -> list[dict]:
    row = {
        "strategy_id": "1001plus_0001",
        "score": 125.0,
        "sharpe": 1.4,
        "max_drawdown": 9000.0,
        "trade_count": 120,
        "profit_factor": 1.7,
        "wfo_pass_rate": 0.8,
        "oos_sharpe": 1.2,
    }
    row.update(overrides)
    return [row]


def _oos(**overrides) -> dict:
    payload = {
        "oos_periods": [],
        "oos_sharpe": 1.2,
        "oos_return": 0.08,
        "oos_mdd": 8000.0,
    }
    payload.update(overrides)
    return payload


def _wfo(**overrides) -> dict:
    payload = {
        "rounds": [],
        "avg_sharpe": 1.1,
        "pass_rate": 0.75,
        "stability_score": 0.7,
    }
    payload.update(overrides)
    return payload


def _risk(**overrides) -> dict:
    payload = {
        "max_dd": 8500.0,
        "ulcer_index": 3.5,
        "recovery_days": 12,
        "volatility": 0.2,
        "downside_volatility": 0.12,
    }
    payload.update(overrides)
    return payload


def test_build_decision_audit_promotes_when_all_thresholds_pass() -> None:
    audit = build_decision_audit(_ranking(), _oos(), _wfo(), _risk())

    assert audit["baseline_strategy"] == "1001plus_baseline"
    assert audit["challenger_strategy"] == "1001plus_0001"
    assert audit["promotion_decision"] == "promote"
    assert audit["recommend_promote"] is True
    assert audit["requires_human_review"] is True
    assert audit["risk_warnings"] == []
    assert audit["checks"]["wfo"]["pass_rate"] == 0.75


def test_build_decision_audit_watches_for_noncritical_warnings() -> None:
    audit = build_decision_audit(_ranking(score=95.0), _oos(), _wfo(), _risk())

    assert audit["promotion_decision"] == "watch"
    assert audit["recommend_promote"] is False
    assert "score below promotion threshold" in audit["risk_warnings"]


def test_build_decision_audit_rejects_for_critical_warnings() -> None:
    audit = build_decision_audit(
        _ranking(trade_count=10),
        _oos(oos_sharpe=0.4),
        _wfo(pass_rate=0.2),
        _risk(max_dd=30000.0),
    )

    assert audit["promotion_decision"] == "reject"
    assert audit["recommend_promote"] is False
    assert "trade_count below minimum" in audit["risk_warnings"]
    assert "wfo_pass_rate below promotion threshold" in audit["risk_warnings"]
    assert "risk max drawdown above maximum" in audit["risk_warnings"]


def test_build_decision_audit_rejects_when_forward_bad() -> None:
    audit = build_decision_audit(
        _ranking(),
        _oos(),
        _wfo(),
        _risk(),
        forward_report={
            "stability_score": 20.0,
            "forward_status": "bad",
            "total_pnl": -500.0,
            "vs_backtest_diff": -10000.0,
            "is_deviating": True,
        },
    )

    assert audit["promotion_decision"] == "reject"
    assert audit["forward_score"] == 20.0
    assert audit["forward_status"] == "bad"
    assert "forward_status bad" in audit["risk_warnings"]
    assert "forward performance deviates from backtest" in audit["risk_warnings"]


def test_build_decision_audit_accepts_ranking_report_shape() -> None:
    audit = build_decision_audit(
        {"top_10": _ranking(strategy_id="alpha")},
        _oos(),
        _wfo(),
        _risk(),
        config=ArtifactDecisionConfig(baseline_strategy="baseline_alpha"),
    )

    assert audit["baseline_strategy"] == "baseline_alpha"
    assert audit["challenger_strategy"] == "alpha"


def test_build_decision_audit_raises_when_ranking_empty() -> None:
    with pytest.raises(ValueError):
        build_decision_audit([], _oos(), _wfo(), _risk())


def test_export_decision_audit_from_artifacts_writes_json(tmp_path) -> None:
    ranking_path = tmp_path / "ranking.json"
    oos_path = tmp_path / "oos_summary.json"
    wfo_path = tmp_path / "wfo_summary.json"
    risk_path = tmp_path / "risk_report.json"
    output_path = tmp_path / "decision_audit.json"

    ranking_path.write_text(json.dumps(_ranking()), encoding="utf-8")
    oos_path.write_text(json.dumps(_oos()), encoding="utf-8")
    wfo_path.write_text(json.dumps(_wfo()), encoding="utf-8")
    risk_path.write_text(json.dumps(_risk()), encoding="utf-8")

    payload = export_decision_audit_from_artifacts(
        str(ranking_path),
        str(oos_path),
        str(wfo_path),
        str(risk_path),
        str(output_path),
    )
    loaded = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["promotion_decision"] == "promote"
    assert loaded["source_artifacts"]["ranking"] == str(ranking_path)
    assert loaded["checks"]["risk"]["max_dd"] == 8500.0
