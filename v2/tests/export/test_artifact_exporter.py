import csv
import json
from datetime import datetime
from pathlib import Path

from mqre_v2.export.artifact_exporter import export_latest_run
from mqre_v2.export.serializers import format_datetime


EXPECTED_FILES = {
    "ranking.json",
    "strategy_detail.json",
    "equity_curve.csv",
    "trades.csv",
    "oos_summary.json",
    "wfo_summary.json",
    "risk_report.json",
    "forward_log.csv",
    "forward_report.json",
    "decision_audit.json",
}


def test_export_latest_run_writes_complete_artifact_set_with_fallback(tmp_path) -> None:
    output = tmp_path / "latest"

    written = export_latest_run({}, output_dir=str(output))

    assert {Path(path).name for path in written} == EXPECTED_FILES
    assert {path.name for path in output.iterdir()} == EXPECTED_FILES

    ranking = json.loads((output / "ranking.json").read_text(encoding="utf-8"))
    assert len(ranking) >= 5
    assert {"strategy_id", "score", "sharpe", "max_drawdown"} <= set(ranking[0])

    with (output / "equity_curve.csv").open(encoding="utf-8", newline="") as handle:
        equity_rows = list(csv.DictReader(handle))
    assert len(equity_rows) >= 200
    assert set(equity_rows[0]) == {"datetime", "equity", "drawdown"}


def test_export_latest_run_maps_partial_pipeline_result(tmp_path) -> None:
    output = tmp_path / "latest"
    result = {
        "ranking": [
            {
                "strategy_name": "alpha",
                "score": 88.0,
                "total_test_net_profit": 12000.0,
                "pass_rate": 0.75,
                "max_test_mdd": 4500.0,
                "average_test_pf": 1.8,
            }
        ],
        "equity_curve": [
            {"datetime": datetime(2024, 1, 1, 9, 0), "equity": 100100.0, "drawdown": 0.0}
        ],
        "trades": [
            {
                "datetime": datetime(2024, 1, 1, 9, 5),
                "price": 20010,
                "side": "buy",
                "pnl": 100.0,
            }
        ],
    }

    export_latest_run(result, output_dir=str(output))

    ranking = json.loads((output / "ranking.json").read_text(encoding="utf-8"))
    assert ranking[0]["strategy_id"] == "alpha"
    assert ranking[0]["max_drawdown"] == 4500.0
    assert ranking[0]["profit_factor"] == 1.8
    assert ranking[0]["wfo_pass_rate"] == 0.75

    audit = json.loads((output / "decision_audit.json").read_text(encoding="utf-8"))
    assert audit["challenger_strategy"] == "alpha"
    assert "recommend_promote" in audit
    assert "checks" in audit
    assert audit["checks"]["ranking"]["score"] == 88.0
    assert "forward_score" in audit
    assert "forward_report.json" in {path.name for path in output.iterdir()}

    with (output / "trades.csv").open(encoding="utf-8", newline="") as handle:
        trades = list(csv.DictReader(handle))
    assert trades[0]["datetime"] == "2024-01-01 09:05:00"
    assert trades[0]["cumulative_pnl"] == "100.0"


def test_format_datetime_uses_dashboard_format() -> None:
    assert format_datetime(datetime(2024, 1, 2, 3, 4, 5, 600)) == "2024-01-02 03:04:05"
