import json
from datetime import date

from mqre_v2.reporting.wfo_report import (
    decision_result_to_dict,
    export_json_report,
    wfo_run_result_to_dict,
)
from mqre_v2.validation.decision import DecisionResult
from mqre_v2.validation.wfo import WfoRoundResult, WfoRunResult, WfoSummary, WfoWindow


def _wfo_run_result() -> WfoRunResult:
    window = WfoWindow(
        round_id=1,
        train_start=date(2023, 1, 1),
        train_end=date(2023, 1, 31),
        gap_start=date(2023, 2, 1),
        gap_end=date(2023, 2, 28),
        test_start=date(2023, 3, 1),
        test_end=date(2023, 3, 31),
    )
    round_result = WfoRoundResult(
        round_id=1,
        train_start=window.train_start,
        train_end=window.train_end,
        gap_start=window.gap_start,
        gap_end=window.gap_end,
        test_start=window.test_start,
        test_end=window.test_end,
        strategy_name="txt-strategy",
        params_hash="txt-import",
        train_net_profit=1000.0,
        train_mdd=100.0,
        train_pf=1.5,
        train_trade_count=30,
        test_net_profit=500.0,
        test_mdd=80.0,
        test_pf=1.8,
        test_trade_count=25,
        pass_flag=True,
        fail_reason="",
    )
    summary = WfoSummary(
        total_rounds=1,
        passed_rounds=1,
        failed_rounds=0,
        pass_rate=1.0,
        total_test_net_profit=500.0,
        average_test_net_profit=500.0,
        max_test_mdd=80.0,
        average_test_pf=1.8,
        total_test_trade_count=25,
    )
    return WfoRunResult(
        windows=[window],
        round_results=[round_result],
        summary=summary,
        passed=True,
        fail_reason="",
    )


def test_wfo_run_result_to_dict() -> None:
    payload = wfo_run_result_to_dict(_wfo_run_result())

    assert payload["generated_at"]
    assert payload["passed"] is True
    assert payload["fail_reason"] == ""
    assert payload["summary"]["total_rounds"] == 1
    assert payload["round_results"][0]["test_net_profit"] == 500.0
    assert payload["round_results"][0]["test_start"] == "2023-03-01"


def test_decision_result_to_dict() -> None:
    result = DecisionResult(
        upgrade=True,
        reason="challenger score improved significantly",
        baseline_score=100.0,
        challenger_score=110.0,
    )

    payload = decision_result_to_dict(result)

    assert payload == {
        "upgrade": True,
        "reason": "challenger score improved significantly",
        "baseline_score": 100.0,
        "challenger_score": 110.0,
    }


def test_export_json_report_writes_valid_json(tmp_path) -> None:
    output_path = tmp_path / "reports" / "wfo_report.json"
    payload = wfo_run_result_to_dict(_wfo_run_result())
    payload["decision"] = decision_result_to_dict(
        DecisionResult(
            upgrade=False,
            reason="no significant improvement",
            baseline_score=100.0,
            challenger_score=103.0,
        )
    )

    export_json_report(payload, str(output_path))

    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert loaded["generated_at"]
    assert loaded["summary"]["total_rounds"] == 1
    assert loaded["round_results"][0]["strategy_name"] == "txt-strategy"
    assert loaded["decision"]["upgrade"] is False


def test_export_json_report_adds_generated_at_when_missing(tmp_path) -> None:
    output_path = tmp_path / "wfo_report.json"

    export_json_report(
        {
            "summary": {"total_rounds": 1},
            "round_results": [],
            "decision": {"upgrade": False},
        },
        str(output_path),
    )

    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert loaded["generated_at"]
    assert loaded["summary"]["total_rounds"] == 1
    assert loaded["round_results"] == []
    assert loaded["decision"]["upgrade"] is False
