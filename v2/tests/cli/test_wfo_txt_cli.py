import json

import pytest

from mqre_v2.cli.wfo_txt import main


def _write_sample_txt(path) -> None:
    path.write_text(
        "entry_time,exit_time,side,entry_price,exit_price\n"
        "2023-03-01T09:00:00,2023-03-01T09:05:00,long,100,120\n"
        "2023-03-02T09:00:00,2023-03-02T09:05:00,long,120,110\n",
        encoding="utf-8",
    )


def _argv(txt_path) -> list[str]:
    return [
        "--txt-path",
        str(txt_path),
        "--strategy-name",
        "txt-strategy",
        "--start-date",
        "2023-01-01",
        "--end-date",
        "2023-03-31",
        "--train-months",
        "1",
        "--gap-months",
        "1",
        "--test-months",
        "1",
        "--step-months",
        "1",
        "--min-test-trade-count",
        "1",
    ]


def test_cli_main_runs_sample_txt(capsys, tmp_path) -> None:
    txt_path = tmp_path / "trades.txt"
    _write_sample_txt(txt_path)

    exit_code = main(_argv(txt_path))

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["strategy_name"] == "txt-strategy"
    assert payload["total_rounds"] == 1
    assert payload["passed_rounds"] == 1
    assert payload["passed"] is True
    assert payload["total_test_net_profit"] == pytest.approx(10.0)
    assert payload["windows"][0]["test_start"] == "2023-03-01"
    assert payload["windows"][0]["test_end"] == "2023-03-31"


def test_cli_stdout_is_valid_json(capsys, tmp_path) -> None:
    txt_path = tmp_path / "trades.txt"
    _write_sample_txt(txt_path)

    main(_argv(txt_path))

    payload = json.loads(capsys.readouterr().out)
    assert "passed" in payload
    assert "total_rounds" in payload
    assert "total_test_net_profit" in payload


def test_cli_invalid_date_raises_system_exit(tmp_path) -> None:
    txt_path = tmp_path / "trades.txt"
    _write_sample_txt(txt_path)

    with pytest.raises(SystemExit):
        main(
            [
                "--txt-path",
                str(txt_path),
                "--strategy-name",
                "txt-strategy",
                "--start-date",
                "not-a-date",
                "--end-date",
                "2023-03-31",
            ]
        )
