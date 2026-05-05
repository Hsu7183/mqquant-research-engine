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
        if df.empty:
            raise ValueError("trades cannot be empty")
    else:
        trades_list = list(trades)
        if len(trades_list) == 0:
            raise ValueError("trades cannot be empty")
        df = pd.DataFrame([t.__dict__ for t in trades_list])

    required_cols = {
        "entry_time",
        "exit_time",
        "entry_price",
        "exit_price",
        "direction",
        "pnl",
    }

    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {missing}")

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
    if isinstance(trades, pd.DataFrame):
        prepared_trades = trades.copy()
        if not prepared_trades.empty:
            if "direction" not in prepared_trades.columns and "side" in prepared_trades.columns:
                prepared_trades["direction"] = prepared_trades["side"]
            if "pnl" not in prepared_trades.columns:
                if "pnl_after_cost_points" in prepared_trades.columns:
                    prepared_trades["pnl"] = prepared_trades["pnl_after_cost_points"]
                elif "pnl_points" in prepared_trades.columns:
                    prepared_trades["pnl"] = prepared_trades["pnl_points"]
    else:
        prepared_trades = trades

    df = _to_dataframe(prepared_trades)

    if "side" not in df.columns and "direction" in df.columns:
        df["side"] = df["direction"]
    if "pnl_after_cost_points" not in df.columns and "pnl" in df.columns:
        df["pnl_after_cost_points"] = df["pnl"]
    if "pnl_points" not in df.columns and "pnl" in df.columns:
        df["pnl_points"] = df["pnl"]

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
