import math

import pandas as pd
import pytest

from mqre_v2.validation.oos.runner import evaluate_oos_trades


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "entry_time": "2026-01-02T09:01:00",
                "exit_time": "2026-01-02T09:05:00",
                "side": "long",
                "entry_price": 20000,
                "exit_price": 20010,
                "qty": 1,
                "slippage_points": 2,
                "fee_points": 1,
                "pnl_points": 10,
                "pnl_after_cost_points": 7,
            },
            {
                "entry_time": "2026-01-02T09:10:00",
                "exit_time": "2026-01-02T09:20:00",
                "side": "short",
                "entry_price": 20015,
                "exit_price": 20005,
                "qty": 1,
                "slippage_points": 2,
                "fee_points": 1,
                "pnl_points": 10,
                "pnl_after_cost_points": 7,
            },
            {
                "entry_time": "2026-01-02T09:30:00",
                "exit_time": "2026-01-02T09:35:00",
                "side": "long",
                "entry_price": 20020,
                "exit_price": 20012,
                "qty": 1,
                "slippage_points": 2,
                "fee_points": 1,
                "pnl_points": -8,
                "pnl_after_cost_points": -11,
            },
        ]
    )


def test_evaluate_oos_trades_normal_case() -> None:
    result = evaluate_oos_trades(_sample_df())
    assert result["total_trades"] == 3
    assert result["win_rate"] == pytest.approx(2 / 3)
    assert result["gross_pnl_points"] == pytest.approx(12.0)
    assert result["net_pnl_points"] == pytest.approx(3.0)
    assert result["avg_trade_points"] == pytest.approx(1.0)


def test_evaluate_oos_trades_empty_raises() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        evaluate_oos_trades(pd.DataFrame())


def test_long_short_trade_counts() -> None:
    result = evaluate_oos_trades(_sample_df())
    assert result["long_trades"] == 2
    assert result["short_trades"] == 1


def test_max_drawdown_points() -> None:
    result = evaluate_oos_trades(_sample_df())
    assert result["max_drawdown_points"] == pytest.approx(11.0)


def test_profit_factor() -> None:
    result = evaluate_oos_trades(_sample_df())
    assert result["profit_factor"] == pytest.approx(14 / 11)

    all_win_df = _sample_df().copy()
    all_win_df["pnl_after_cost_points"] = [3, 2, 1]
    all_win_df["pnl_points"] = [3, 2, 1]
    all_win_df["side"] = ["long", "short", "long"]
    all_win_result = evaluate_oos_trades(all_win_df)
    assert math.isinf(all_win_result["profit_factor"])
