from __future__ import annotations

from dataclasses import asdict
from math import inf
from typing import Iterable

import pandas as pd

from mqre_v2.core.trades import TradeRecord

REQUIRED_COLUMNS = {
    "entry_time",
    "exit_time",
    "side",
    "entry_price",
    "exit_price",
    "qty",
    "slippage_points",
    "fee_points",
    "pnl_points",
    "pnl_after_cost_points",
}


def _to_dataframe(trades: Iterable[TradeRecord] | pd.DataFrame) -> pd.DataFrame:
    if isinstance(trades, pd.DataFrame):
        df = trades.copy()
    else:
        rows = []
        for trade in trades:
            if isinstance(trade, TradeRecord):
                rows.append(asdict(trade))
            elif isinstance(trade, dict):
                rows.append(trade)
            else:
                raise TypeError("trades must be TradeRecord list, dict list, or DataFrame")
        df = pd.DataFrame(rows)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"missing required trade columns: {sorted(missing)}")

    if df.empty:
        raise ValueError("trade records cannot be empty")

    return df


def _max_drawdown_from_series(pnl_after_cost: pd.Series) -> float:
    equity = pnl_after_cost.cumsum()
    running_peak = equity.cummax()
    drawdown = equity - running_peak
    return float(abs(drawdown.min()))


def evaluate_oos_trades(trades: Iterable[TradeRecord] | pd.DataFrame) -> dict[str, float | int]:
    """Evaluate OOS performance from pre-existing trade records.

    This function does NOT generate strategy signals or orders.
    """
    df = _to_dataframe(trades)

    total_trades = int(len(df))
    net_col = df["pnl_after_cost_points"].astype(float)
    gross_col = df["pnl_points"].astype(float)

    wins = int((net_col > 0).sum())
    win_rate = wins / total_trades

    gross_pnl_points = float(gross_col.sum())
    net_pnl_points = float(net_col.sum())
    avg_trade_points = float(net_col.mean())
    max_drawdown_points = _max_drawdown_from_series(net_col)

    gross_profit = float(net_col[net_col > 0].sum())
    gross_loss_abs = float(abs(net_col[net_col < 0].sum()))
    profit_factor = inf if gross_loss_abs == 0 else gross_profit / gross_loss_abs

    long_trades = int((df["side"] == "long").sum())
    short_trades = int((df["side"] == "short").sum())

    return {
        "total_trades": total_trades,
        "win_rate": win_rate,
        "gross_pnl_points": gross_pnl_points,
        "net_pnl_points": net_pnl_points,
        "avg_trade_points": avg_trade_points,
        "max_drawdown_points": max_drawdown_points,
        "profit_factor": profit_factor,
        "long_trades": long_trades,
        "short_trades": short_trades,
    }
