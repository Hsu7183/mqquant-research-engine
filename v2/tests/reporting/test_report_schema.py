from copy import deepcopy

from mqre_v2.reporting.wfo_report import validate_report_schema


def _valid_report() -> dict:
    return {
        "run_id": "20260506_0313plus_batch001",
        "generated_at": "2026-05-06T00:00:00+00:00",
        "summary": {
            "total_strategies": 2,
            "valid_strategies": 2,
        },
        "top_10": [
            {
                "rank": 1,
                "strategy_name": "beta",
                "score": 89.3,
                "total_test_net_profit": 50.0,
                "pass_rate": 1.0,
                "max_test_mdd": 0.0,
                "average_test_pf": 5.0,
            }
        ],
        "all_results": [
            {
                "rank": 1,
                "strategy_name": "beta",
                "score": 89.3,
                "total_test_net_profit": 50.0,
                "pass_rate": 1.0,
                "max_test_mdd": 0.0,
                "average_test_pf": 5.0,
            },
            {
                "rank": 2,
                "strategy_name": "alpha",
                "score": 80.4,
                "total_test_net_profit": 20.0,
                "pass_rate": 1.0,
                "max_test_mdd": 0.0,
                "average_test_pf": 5.0,
            },
        ],
    }


def test_validate_report_schema_accepts_valid_json() -> None:
    assert validate_report_schema(_valid_report()) is True


def test_validate_report_schema_fails_when_required_field_missing() -> None:
    report = _valid_report()
    del report["summary"]

    assert validate_report_schema(report) is False


def test_validate_report_schema_fails_when_type_is_wrong() -> None:
    report = _valid_report()
    report["summary"]["total_strategies"] = "2"

    assert validate_report_schema(report) is False


def test_validate_report_schema_fails_when_ranking_item_field_missing() -> None:
    report = deepcopy(_valid_report())
    del report["top_10"][0]["score"]

    assert validate_report_schema(report) is False
