from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from mqre_v2.backtest.costs import CostConfig
from mqre_v2.pipeline.txt_wfo_pipeline import (
    export_pipeline_result,
    run_txt_wfo_pipeline,
)


def test_run_txt_wfo_pipeline_runs_multiple_txts(tmp_path: Path) -> None:
    _write_sample_txt(tmp_path / "baseline.txt")
    _write_challenger_txt(tmp_path / "challenger.txt")

    results = run_txt_wfo_pipeline(
        txt_folder=str(tmp_path),
        start_date=date(2023, 1, 1),
        end_date=date(2023, 3, 31),
        gate_config=_gate_config(),
    )

    assert len(results) == 2
    assert {result["strategy_name"] for result in results} == {"baseline", "challenger"}


def test_run_txt_wfo_pipeline_generates_ranking(tmp_path: Path) -> None:
    _write_sample_txt(tmp_path / "baseline.txt")
    _write_challenger_txt(tmp_path / "challenger.txt")

    results = run_txt_wfo_pipeline(
        txt_folder=str(tmp_path),
        start_date=date(2023, 1, 1),
        end_date=date(2023, 3, 31),
        gate_config=_gate_config(),
    )

    assert all("score" in result for result in results)
    assert [result["rank"] for result in results] == [1, 2]
    assert results[0]["strategy_name"] == "challenger"


def test_run_txt_wfo_pipeline_sorts_by_score_desc(tmp_path: Path) -> None:
    _write_sample_txt(tmp_path / "baseline.txt")
    _write_challenger_txt(tmp_path / "challenger.txt")

    results = run_txt_wfo_pipeline(
        txt_folder=str(tmp_path),
        start_date=date(2023, 1, 1),
        end_date=date(2023, 3, 31),
        gate_config=_gate_config(),
    )
    scores = [float(result["score"]) for result in results]

    assert scores == sorted(scores, reverse=True)


def test_run_txt_wfo_pipeline_uses_net_pnl_for_ranking_metrics(tmp_path: Path) -> None:
    _write_sample_txt(tmp_path / "baseline.txt")

    results = run_txt_wfo_pipeline(
        txt_folder=str(tmp_path),
        start_date=date(2023, 1, 1),
        end_date=date(2023, 3, 31),
        gate_config=_gate_config(),
        cost_config=CostConfig(slippage_points_per_side=2.0, tax_rate=0.0),
        include_wfo_details=True,
    )

    result = results[0]
    assert result["raw_total_profit"] == 10.0
    assert result["net_total_profit"] == 2.0
    assert result["total_cost"] == 8.0
    assert result["summary"]["total_test_net_profit"] == 2.0


def test_export_pipeline_result_writes_json(tmp_path: Path) -> None:
    _write_sample_txt(tmp_path / "baseline.txt")
    _write_challenger_txt(tmp_path / "challenger.txt")
    output_path = tmp_path / "reports" / "pipeline.json"
    results = run_txt_wfo_pipeline(
        txt_folder=str(tmp_path),
        start_date=date(2023, 1, 1),
        end_date=date(2023, 3, 31),
        gate_config=_gate_config(),
    )

    export_pipeline_result(results, str(output_path))

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["total_strategies"] == 2
    assert len(payload["top_10"]) == 2
    assert len(payload["all_results"]) == 2
    assert "generated_at" in payload


def test_run_txt_wfo_pipeline_bad_file_does_not_interrupt(tmp_path: Path) -> None:
    _write_sample_txt(tmp_path / "good.txt")
    _write_broken_txt(tmp_path / "bad.txt")

    results = run_txt_wfo_pipeline(
        txt_folder=str(tmp_path),
        start_date=date(2023, 1, 1),
        end_date=date(2023, 3, 31),
        gate_config=_gate_config(),
    )
    by_name = {result["strategy_name"]: result for result in results}

    assert len(results) == 2
    assert by_name["good"]["passed"] is True
    assert by_name["bad"]["passed"] is False
    assert by_name["bad"]["score"] == 0.0
    assert by_name["bad"]["fail_reason"]


def _gate_config() -> dict:
    return {
        "train_months": 1,
        "gap_months": 1,
        "test_months": 1,
        "step_months": 1,
        "min_test_trade_count": 1,
        "max_test_mdd": 15000.0,
        "min_test_pf": 1.05,
        "min_pass_rate": 0.6,
    }


def _write_sample_txt(path: Path) -> None:
    path.write_text(
        "entry_time,exit_time,side,entry_price,exit_price\n"
        "2023-03-01T09:00:00,2023-03-01T09:05:00,long,100,120\n"
        "2023-03-02T09:00:00,2023-03-02T09:05:00,long,120,110\n",
        encoding="utf-8",
    )


def _write_challenger_txt(path: Path) -> None:
    path.write_text(
        "entry_time,exit_time,side,entry_price,exit_price\n"
        "2023-03-01T09:00:00,2023-03-01T09:05:00,long,100,140\n"
        "2023-03-02T09:00:00,2023-03-02T09:05:00,long,140,130\n",
        encoding="utf-8",
    )


def _write_broken_txt(path: Path) -> None:
    path.write_text("not,a,valid,trade,file\n1,2,3,4\n", encoding="utf-8")
