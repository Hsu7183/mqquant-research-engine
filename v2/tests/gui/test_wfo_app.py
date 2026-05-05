from datetime import date

import pytest

from mqre_v2.forward.forward_log import ForwardTestRecord, append_forward_record
from mqre_v2.gui.wfo_app import (
    BATCH_RANKING_COLUMNS,
    OPTIMIZER_TABLE_COLUMNS,
    build_batch_ranking_dataframe,
    build_optimizer_dataframe,
    build_round_dataframe,
    create_run_manifest_from_config,
    generate_xs_into_run_from_config,
    generate_xs_batch_from_config,
    load_parameter_grid_preview,
    manage_forward_status_from_config,
    promote_registry_from_config,
    retire_strategy_from_config,
    run_batch_txt_ranking_from_config,
    run_baseline_challenger_from_config,
    run_pipeline_from_run_config,
    run_simple_optimizer,
    run_txt_wfo_from_config,
    validate_run_txt_from_config,
)


def _write_sample_txt(path) -> None:
    path.write_text(
        "entry_time,exit_time,side,entry_price,exit_price\n"
        "2023-03-01T09:00:00,2023-03-01T09:05:00,long,100,120\n"
        "2023-03-02T09:00:00,2023-03-02T09:05:00,long,120,110\n",
        encoding="utf-8",
    )


def _write_challenger_txt(path) -> None:
    path.write_text(
        "entry_time,exit_time,side,entry_price,exit_price\n"
        "2023-03-01T09:00:00,2023-03-01T09:05:00,long,100,140\n"
        "2023-03-02T09:00:00,2023-03-02T09:05:00,long,140,130\n",
        encoding="utf-8",
    )


def _write_broken_txt(path) -> None:
    path.write_text("not,a,valid,trade,file\n1,2,3,4\n", encoding="utf-8")


def _write_parameter_grid(path) -> None:
    path.write_text(
        """
strategy_name: demo-grid
parameters:
  A: [1, 2]
  B: [10, 20, 30]
""",
        encoding="utf-8",
    )


def _write_xs_template(path) -> None:
    path.write_text(
        "\n".join(
            [
                "EntryBufferPts={{EntryBufferPts}}",
                "DonBufferPts={{DonBufferPts}}",
                "ATRStopK={{ATRStopK}}",
                "ATRTakeProfitK={{ATRTakeProfitK}}",
                "TimeStopBars={{TimeStopBars}}",
            ]
        ),
        encoding="utf-8",
    )


def _write_xs_parameter_grid(path) -> None:
    path.write_text(
        """
strategy_name: gui-xs
parameters:
  EntryBufferPts: [0, 1]
  DonBufferPts: [2]
  ATRStopK: [1.0, 1.5]
  ATRTakeProfitK: [2.0]
  TimeStopBars: [20]
""",
        encoding="utf-8",
    )


def _write_forward_log(path, strategy_name: str = "alpha") -> None:
    append_forward_record(
        str(path),
        ForwardTestRecord(
            strategy_name=strategy_name,
            txt_path=f"{strategy_name}.txt",
            status="candidate",
            created_at="2026-05-05T00:00:00+00:00",
            updated_at="2026-05-05T00:00:00+00:00",
            source_score=88.5,
            source_pass_rate=0.75,
            source_total_test_net_profit=1234.0,
            notes="",
        ),
    )


def _config(txt_path) -> dict:
    return {
        "txt_path": str(txt_path),
        "strategy_name": "gui-strategy",
        "start_date": date(2023, 1, 1),
        "end_date": date(2023, 3, 31),
        "train_months": 1,
        "gap_months": 1,
        "test_months": 1,
        "step_months": 1,
        "min_test_trade_count": 1,
        "max_test_mdd": 15000.0,
        "min_test_pf": 1.05,
        "min_pass_rate": 0.6,
    }


def _comparison_config(baseline_path, challenger_path) -> dict:
    return {
        "baseline_txt_path": str(baseline_path),
        "baseline_name": "baseline",
        "challenger_txt_path": str(challenger_path),
        "challenger_name": "challenger",
        "start_date": date(2023, 1, 1),
        "end_date": date(2023, 3, 31),
        "train_months": 1,
        "gap_months": 1,
        "test_months": 1,
        "step_months": 1,
        "min_test_trade_count": 1,
        "max_test_mdd": 15000.0,
        "min_test_pf": 1.05,
        "min_pass_rate": 0.6,
        "min_improvement": 5.0,
    }


def _optimizer_config(txt_path) -> dict:
    return {
        "base_txt_path": str(txt_path),
        "strategy_name": "optimizer-strategy",
        "start_date": date(2023, 1, 1),
        "end_date": date(2023, 3, 31),
        "train_months": 1,
        "gap_months": 1,
        "test_months": 1,
        "step_months": 1,
        "min_test_trade_count": 1,
        "max_test_mdd": 15000.0,
        "min_pass_rate": 0.6,
        "slippage_points_range": "1,2",
        "fee_points_range": "0,1",
        "min_test_pf_range": "1.0,1.1",
    }


def _batch_config(folder_path) -> dict:
    return {
        "txt_folder_path": str(folder_path),
        "file_pattern": "*.txt",
        "start_date": date(2023, 1, 1),
        "end_date": date(2023, 3, 31),
        "train_months": 1,
        "gap_months": 1,
        "test_months": 1,
        "step_months": 1,
        "min_test_trade_count": 1,
        "max_test_mdd": 15000.0,
        "min_test_pf": 1.05,
        "min_pass_rate": 0.6,
    }


def test_run_txt_wfo_from_config_runs_sample_txt(tmp_path) -> None:
    txt_path = tmp_path / "trades.txt"
    _write_sample_txt(txt_path)

    payload = run_txt_wfo_from_config(_config(txt_path))

    assert payload["strategy_name"] == "gui-strategy"
    assert payload["summary"]["total_rounds"] == 1
    assert payload["summary"]["total_test_net_profit"] == pytest.approx(10.0)


def test_run_txt_wfo_from_config_returns_summary(tmp_path) -> None:
    txt_path = tmp_path / "trades.txt"
    _write_sample_txt(txt_path)

    payload = run_txt_wfo_from_config(_config(txt_path))

    assert "summary" in payload
    assert payload["summary"]["passed_rounds"] == 1


def test_run_txt_wfo_from_config_returns_round_results_and_passed(tmp_path) -> None:
    txt_path = tmp_path / "trades.txt"
    _write_sample_txt(txt_path)

    payload = run_txt_wfo_from_config(_config(txt_path))

    assert "round_results" in payload
    assert payload["round_results"][0]["strategy_name"] == "gui-strategy"
    assert payload["passed"] is True


def test_run_txt_wfo_from_config_invalid_txt_path_raises(tmp_path) -> None:
    missing_path = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        run_txt_wfo_from_config(_config(missing_path))


def test_run_baseline_challenger_from_config_runs_two_sample_txts(tmp_path) -> None:
    baseline_path = tmp_path / "baseline.txt"
    challenger_path = tmp_path / "challenger.txt"
    _write_sample_txt(baseline_path)
    _write_challenger_txt(challenger_path)

    payload = run_baseline_challenger_from_config(
        _comparison_config(baseline_path, challenger_path)
    )

    assert payload["baseline"]["strategy_name"] == "baseline"
    assert payload["challenger"]["strategy_name"] == "challenger"
    assert payload["baseline"]["summary"]["total_rounds"] == 1
    assert payload["challenger"]["summary"]["total_test_net_profit"] == pytest.approx(30.0)


def test_run_baseline_challenger_from_config_returns_required_sections(tmp_path) -> None:
    baseline_path = tmp_path / "baseline.txt"
    challenger_path = tmp_path / "challenger.txt"
    _write_sample_txt(baseline_path)
    _write_challenger_txt(challenger_path)

    payload = run_baseline_challenger_from_config(
        _comparison_config(baseline_path, challenger_path)
    )

    assert "baseline" in payload
    assert "challenger" in payload
    assert "decision" in payload
    assert "generated_at" in payload


def test_run_baseline_challenger_decision_contains_scores(tmp_path) -> None:
    baseline_path = tmp_path / "baseline.txt"
    challenger_path = tmp_path / "challenger.txt"
    _write_sample_txt(baseline_path)
    _write_challenger_txt(challenger_path)

    payload = run_baseline_challenger_from_config(
        _comparison_config(baseline_path, challenger_path)
    )
    decision = payload["decision"]

    assert "upgrade" in decision
    assert "reason" in decision
    assert "baseline_score" in decision
    assert "challenger_score" in decision
    assert decision["upgrade"] is True


def test_run_baseline_challenger_invalid_baseline_txt_path_raises(tmp_path) -> None:
    baseline_path = tmp_path / "missing_baseline.txt"
    challenger_path = tmp_path / "challenger.txt"
    _write_challenger_txt(challenger_path)

    with pytest.raises(FileNotFoundError):
        run_baseline_challenger_from_config(
            _comparison_config(baseline_path, challenger_path)
        )


def test_run_baseline_challenger_invalid_challenger_txt_path_raises(tmp_path) -> None:
    baseline_path = tmp_path / "baseline.txt"
    challenger_path = tmp_path / "missing_challenger.txt"
    _write_sample_txt(baseline_path)

    with pytest.raises(FileNotFoundError):
        run_baseline_challenger_from_config(
            _comparison_config(baseline_path, challenger_path)
        )


def test_build_round_dataframe_columns_and_cum_pnl() -> None:
    df = build_round_dataframe(
        [
            {
                "round_id": 1,
                "test_net_profit": 100.0,
                "test_mdd": 20.0,
                "test_pf": 1.5,
                "test_trade_count": 25,
            },
            {
                "round_id": 2,
                "test_net_profit": -40.0,
                "test_mdd": 60.0,
                "test_pf": 0.8,
                "test_trade_count": 18,
            },
            {
                "round_id": 3,
                "test_net_profit": 70.0,
                "test_mdd": 30.0,
                "test_pf": 1.2,
                "test_trade_count": 21,
            },
        ]
    )

    assert list(df.columns) == [
        "round_id",
        "test_net_profit",
        "test_mdd",
        "test_pf",
        "test_trade_count",
        "cum_pnl",
    ]
    assert df["round_id"].tolist() == [1, 2, 3]
    assert df["cum_pnl"].tolist() == pytest.approx([100.0, 60.0, 130.0])


def test_run_simple_optimizer_generates_multiple_results(tmp_path) -> None:
    txt_path = tmp_path / "trades.txt"
    _write_sample_txt(txt_path)

    results = run_simple_optimizer(_optimizer_config(txt_path))

    assert len(results) == 8
    assert len(results) > 0


def test_build_optimizer_dataframe_columns(tmp_path) -> None:
    txt_path = tmp_path / "trades.txt"
    _write_sample_txt(txt_path)

    results = run_simple_optimizer(_optimizer_config(txt_path))
    df = build_optimizer_dataframe(results)

    assert list(df.columns) == OPTIMIZER_TABLE_COLUMNS
    assert len(df) == 8


def test_run_simple_optimizer_sorts_by_score_desc(tmp_path) -> None:
    txt_path = tmp_path / "trades.txt"
    _write_sample_txt(txt_path)

    results = run_simple_optimizer(_optimizer_config(txt_path))
    scores = [result["score"] for result in results]

    assert scores == sorted(scores, reverse=True)
    assert results[0]["rank"] == 1
    assert results[0]["slippage"] == pytest.approx(1.0)
    assert results[0]["fee"] == pytest.approx(0.0)


def test_run_batch_txt_ranking_reads_multiple_txts(tmp_path) -> None:
    _write_sample_txt(tmp_path / "baseline.txt")
    _write_challenger_txt(tmp_path / "challenger.txt")

    results = run_batch_txt_ranking_from_config(_batch_config(tmp_path))

    assert len(results) == 2
    assert {result["strategy_name"] for result in results} == {"baseline", "challenger"}


def test_run_batch_txt_ranking_contains_score_and_sorted_desc(tmp_path) -> None:
    _write_sample_txt(tmp_path / "baseline.txt")
    _write_challenger_txt(tmp_path / "challenger.txt")

    results = run_batch_txt_ranking_from_config(_batch_config(tmp_path))
    scores = [result["score"] for result in results]

    assert all("score" in result for result in results)
    assert scores == sorted(scores, reverse=True)
    assert results[0]["strategy_name"] == "challenger"


def test_build_batch_ranking_dataframe_columns(tmp_path) -> None:
    _write_sample_txt(tmp_path / "baseline.txt")
    _write_challenger_txt(tmp_path / "challenger.txt")

    results = run_batch_txt_ranking_from_config(_batch_config(tmp_path))
    df = build_batch_ranking_dataframe(results)

    assert list(df.columns) == BATCH_RANKING_COLUMNS
    assert len(df) == 2


def test_run_batch_txt_ranking_invalid_folder_raises(tmp_path) -> None:
    missing_folder = tmp_path / "missing"

    with pytest.raises(NotADirectoryError):
        run_batch_txt_ranking_from_config(_batch_config(missing_folder))


def test_run_batch_txt_ranking_bad_file_does_not_interrupt(tmp_path) -> None:
    _write_sample_txt(tmp_path / "good.txt")
    _write_broken_txt(tmp_path / "bad.txt")

    results = run_batch_txt_ranking_from_config(_batch_config(tmp_path))
    by_name = {result["strategy_name"]: result for result in results}

    assert len(results) == 2
    assert by_name["good"]["passed"] is True
    assert by_name["bad"]["passed"] is False
    assert by_name["bad"]["score"] == 0.0
    assert by_name["bad"]["fail_reason"]


def test_load_parameter_grid_preview(tmp_path) -> None:
    path = tmp_path / "parameter_grid.yaml"
    _write_parameter_grid(path)

    preview = load_parameter_grid_preview(str(path))

    assert preview["strategy_name"] == "demo-grid"
    assert preview["total_combinations"] == 6
    assert preview["parameters"] == [
        {"name": "A", "candidate_count": 2},
        {"name": "B", "candidate_count": 3},
    ]


def test_generate_xs_batch_from_config(tmp_path) -> None:
    template_path = tmp_path / "template.xs"
    grid_path = tmp_path / "parameter_grid.yaml"
    output_dir = tmp_path / "xs_batch"
    _write_xs_template(template_path)
    _write_xs_parameter_grid(grid_path)

    result = generate_xs_batch_from_config(
        {
            "template_path": str(template_path),
            "parameter_grid_path": str(grid_path),
            "output_dir": str(output_dir),
        }
    )

    assert result["generated_count"] == 4
    assert len(result["paths"]) == 4
    assert result["filenames"][0] == "gui-xs_EB0_DB2_ATRS1_ATRTP2_TS20_IDX1.xs"


def test_create_run_manifest_from_config_creates_manifest_only(tmp_path) -> None:
    template_path = tmp_path / "template.xs"
    grid_path = tmp_path / "parameter_grid.yaml"
    base_dir = tmp_path / "runs"
    _write_xs_template(template_path)
    _write_xs_parameter_grid(grid_path)

    result = create_run_manifest_from_config(
        {
            "base_dir": str(base_dir),
            "strategy_name": "gui-xs",
            "parameter_grid_path": str(grid_path),
            "template_path": str(template_path),
        }
    )

    run_path = base_dir / result["run_id"]
    assert result["run_id"].endswith("gui-xs_batch001")
    assert result["total_param_combinations"] == 4
    assert (run_path / "manifest.json").is_file()
    assert (run_path / "xs").is_dir()
    assert list((run_path / "xs").iterdir()) == []


def test_generate_xs_into_run_from_config_writes_xs(tmp_path) -> None:
    template_path = tmp_path / "template.xs"
    grid_path = tmp_path / "parameter_grid.yaml"
    base_dir = tmp_path / "runs"
    _write_xs_template(template_path)
    _write_xs_parameter_grid(grid_path)
    run_result = create_run_manifest_from_config(
        {
            "base_dir": str(base_dir),
            "strategy_name": "gui-xs",
            "parameter_grid_path": str(grid_path),
            "template_path": str(template_path),
        }
    )

    xs_result = generate_xs_into_run_from_config(
        {
            "run_path": run_result["run_path"],
        }
    )

    assert xs_result["xs_count"] == 4
    assert xs_result["filenames"][:2] == [
        "gui-xs_EB0_DB2_ATRS1_ATRTP2_TS20_IDX1.xs",
        "gui-xs_EB0_DB2_ATRS1p5_ATRTP2_TS20_IDX2.xs",
    ]


def test_validate_run_txt_from_config_reports_counts(tmp_path) -> None:
    template_path = tmp_path / "template.xs"
    grid_path = tmp_path / "parameter_grid.yaml"
    base_dir = tmp_path / "runs"
    _write_xs_template(template_path)
    _write_xs_parameter_grid(grid_path)
    run_result = create_run_manifest_from_config(
        {
            "base_dir": str(base_dir),
            "strategy_name": "gui-xs",
            "parameter_grid_path": str(grid_path),
            "template_path": str(template_path),
        }
    )
    generate_xs_into_run_from_config({"run_path": run_result["run_path"]})
    txt_dir = tmp_path / "runs" / run_result["run_id"] / "txt"
    (txt_dir / "gui-xs_EB0_DB2_ATRS1_ATRTP2_TS20_IDX1.txt").write_text(
        "entry_time,exit_time,side,entry_price,exit_price\n"
        "2023-03-01T09:00:00,2023-03-01T09:05:00,long,100,120\n",
        encoding="utf-8",
    )

    result = validate_run_txt_from_config({"run_path": run_result["run_path"]})

    assert result["total_xs"] == 4
    assert result["total_txt"] == 1
    assert result["matched"] == 1
    assert len(result["missing_txt"]) == 3
    assert result["parse_failed"] == []
    assert result["valid_txt"] == ["gui-xs_EB0_DB2_ATRS1_ATRTP2_TS20_IDX1.txt"]


def test_run_pipeline_from_run_config_generates_ranking(tmp_path) -> None:
    template_path = tmp_path / "template.xs"
    grid_path = tmp_path / "parameter_grid.yaml"
    base_dir = tmp_path / "runs"
    _write_xs_template(template_path)
    _write_xs_parameter_grid(grid_path)
    run_result = create_run_manifest_from_config(
        {
            "base_dir": str(base_dir),
            "strategy_name": "gui-xs",
            "parameter_grid_path": str(grid_path),
            "template_path": str(template_path),
        }
    )
    generate_xs_into_run_from_config({"run_path": run_result["run_path"]})
    txt_dir = tmp_path / "runs" / run_result["run_id"] / "txt"
    (txt_dir / "gui-xs_EB0_DB2_ATRS1_ATRTP2_TS20_IDX1.txt").write_text(
        "entry_time,exit_time,side,entry_price,exit_price\n"
        "2023-03-01T09:00:00,2023-03-01T09:05:00,long,100,120\n",
        encoding="utf-8",
    )

    result = run_pipeline_from_run_config(
        {
            "run_path": run_result["run_path"],
            "start_date": date(2020, 1, 1),
            "end_date": date(2023, 12, 31),
        }
    )

    assert result["total_strategies"] == 1
    assert result["valid_txt"] == 1
    assert result["ranking"][0]["strategy_name"] == "gui-xs_EB0_DB2_ATRS1_ATRTP2_TS20_IDX1"
    assert result["output_json_path"].endswith("ranking.json")


def test_manage_forward_status_from_config_updates_status(tmp_path) -> None:
    forward_log_path = tmp_path / "forward_test_log.csv"
    _write_forward_log(forward_log_path, "alpha")

    records = manage_forward_status_from_config(
        {
            "forward_log_path": str(forward_log_path),
            "strategy_name": "alpha",
            "new_status": "forward_testing",
            "notes": "started paper observation",
        }
    )

    assert records[0]["strategy_name"] == "alpha"
    assert records[0]["status"] == "forward_testing"
    assert records[0]["notes"] == "started paper observation"


def test_manage_forward_status_from_config_missing_strategy_raises(tmp_path) -> None:
    forward_log_path = tmp_path / "forward_test_log.csv"
    _write_forward_log(forward_log_path, "alpha")

    with pytest.raises(ValueError):
        manage_forward_status_from_config(
            {
                "forward_log_path": str(forward_log_path),
                "strategy_name": "missing",
                "new_status": "rejected",
                "notes": "not found",
            }
        )


def test_promote_registry_from_config_imports_promoted_strategy(tmp_path) -> None:
    forward_log_path = tmp_path / "forward_test_log.csv"
    registry_path = tmp_path / "strategy_registry.csv"
    append_forward_record(
        str(forward_log_path),
        ForwardTestRecord(
            strategy_name="alpha",
            txt_path="alpha.txt",
            status="promoted",
            created_at="2026-05-06T00:00:00+00:00",
            updated_at="2026-05-06T00:00:00+00:00",
            source_score=120.0,
            source_pass_rate=0.8,
            source_total_test_net_profit=5000.0,
            notes="forward evaluation score=120.0",
        ),
    )

    records = promote_registry_from_config(
        {
            "forward_log_path": str(forward_log_path),
            "registry_csv_path": str(registry_path),
        }
    )

    assert len(records) == 1
    assert records[0]["strategy_name"] == "alpha"
    assert records[0]["status"] == "active"
    assert records[0]["source"] == "forward_log"


def test_retire_strategy_from_config_updates_registry(tmp_path) -> None:
    forward_log_path = tmp_path / "forward_test_log.csv"
    registry_path = tmp_path / "strategy_registry.csv"
    append_forward_record(
        str(forward_log_path),
        ForwardTestRecord(
            strategy_name="alpha",
            txt_path="alpha.txt",
            status="promoted",
            created_at="2026-05-06T00:00:00+00:00",
            updated_at="2026-05-06T00:00:00+00:00",
            source_score=120.0,
            source_pass_rate=0.8,
            source_total_test_net_profit=5000.0,
            notes="forward evaluation score=120.0",
        ),
    )
    promote_registry_from_config(
        {
            "forward_log_path": str(forward_log_path),
            "registry_csv_path": str(registry_path),
        }
    )

    records = retire_strategy_from_config(
        {
            "registry_csv_path": str(registry_path),
            "strategy_name": "alpha",
            "notes": "retired after review",
        }
    )

    assert records[0]["strategy_name"] == "alpha"
    assert records[0]["status"] == "retired"
    assert records[0]["notes"] == "retired after review"
