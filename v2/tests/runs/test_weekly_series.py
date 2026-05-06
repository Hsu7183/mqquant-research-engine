import math
from datetime import datetime

from mqre_v2.backtest.costs import CostConfig
from mqre_v2.core.trades import TradeRecord
from mqre_v2.runs.run_pipeline import build_trade_stats, build_weekly_series


def _trade(exit_time: str, pnl: float) -> TradeRecord:
    return TradeRecord(
        entry_time=datetime.fromisoformat(exit_time),
        exit_time=datetime.fromisoformat(exit_time),
        entry_price=100.0,
        exit_price=100.0 + pnl,
        direction=1,
        pnl=pnl,
    )


def test_build_weekly_series_groups_trades_by_iso_week() -> None:
    result = build_weekly_series(
        [
            _trade("2024-01-02T09:05:00", 500.0),
            _trade("2024-01-05T09:05:00", -100.0),
            _trade("2024-01-09T09:05:00", 700.0),
        ]
    )

    assert result["weekly_pnl"] == [
        {"week": "2024-W01", "pnl": 400.0},
        {"week": "2024-W02", "pnl": 700.0},
    ]


def test_build_weekly_series_accumulates_equity_curve() -> None:
    result = build_weekly_series(
        [
            _trade("2024-01-02T09:05:00", 500.0),
            _trade("2024-01-09T09:05:00", 700.0),
            _trade("2024-01-16T09:05:00", -200.0),
        ]
    )

    assert result["equity_curve"] == [
        {"week": "2024-W01", "equity": 100500.0},
        {"week": "2024-W02", "equity": 101200.0},
        {"week": "2024-W03", "equity": 101000.0},
    ]


def test_build_weekly_series_can_use_net_pnl_after_cost() -> None:
    result = build_weekly_series(
        [
            _trade("2024-01-02T09:05:00", 10.0),
            _trade("2024-01-05T09:05:00", 20.0),
        ],
        cost_config=CostConfig(slippage_points_per_side=1.0, tax_rate=0.0),
    )

    assert result["weekly_pnl"] == [{"week": "2024-W01", "pnl": 26.0}]
    assert result["equity_curve"] == [{"week": "2024-W01", "equity": 100026.0}]


def test_trade_stats_uses_weekly_equity_for_risk() -> None:
    trades = [
        _trade("2024-01-02T09:05:00", 500.0),
        _trade("2024-01-09T09:05:00", -700.0),
        _trade("2024-01-16T09:05:00", -100.0),
        _trade("2024-01-23T09:05:00", 900.0),
    ]
    weekly_series = build_weekly_series(trades)

    stats = build_trade_stats(trades, weekly_series)

    assert stats["underwater_weeks"] == 2
    assert stats["max_drawdown"] == 800.0
    assert stats["max_losing_streak"] == 2


def test_trade_stats_uses_infinity_for_no_loss_ratios() -> None:
    trades = [
        _trade("2024-01-02T09:05:00", 500.0),
        _trade("2024-01-09T09:05:00", 700.0),
    ]
    weekly_series = build_weekly_series(trades)

    stats = build_trade_stats(trades, weekly_series)

    assert math.isinf(stats["profit_factor"])
    assert math.isinf(stats["payoff_ratio"])
