from datetime import date

import pytest

from mqre_v2.gui.wfo_app import (
    build_round_dataframe,
    run_baseline_challenger_from_config,
    run_txt_wfo_from_config,
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
