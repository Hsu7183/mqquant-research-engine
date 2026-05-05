from datetime import date

import pytest

from mqre_v2.gui.wfo_app import run_txt_wfo_from_config


def _write_sample_txt(path) -> None:
    path.write_text(
        "entry_time,exit_time,side,entry_price,exit_price\n"
        "2023-03-01T09:00:00,2023-03-01T09:05:00,long,100,120\n"
        "2023-03-02T09:00:00,2023-03-02T09:05:00,long,120,110\n",
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
