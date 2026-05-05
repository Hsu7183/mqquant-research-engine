from __future__ import annotations

from dataclasses import asdict
from math import inf
from typing import Any, Iterable

import pandas as pd

from mqre_v2.core.trades import ExtendedTradeRecord, TradeRecord

REQUIRED_COLUMNS = {
    "entry_time",
    "exit_time",
    "entry_price",
    "exit_price",
    "direction",
    "pnl",
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
        df = pd.DataFrame([_trade_to_row(trade) for trade in trades_list])

    df = _normalize_trade_columns(df)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {missing}")

    return df


def _trade_to_row(trade: Any) -> dict[str, Any]:
    if isinstance(trade, ExtendedTradeRecord):
        row = asdict(trade.base)
        row["pnl_after_cost"] = trade.pnl_after_cost
        return row
    if isinstance(trade, TradeRecord):
        return asdict(trade)
    if isinstance(trade, dict):
        return dict(trade)
    raise TypeError("trades must contain TradeRecord, ExtendedTradeRecord, dict, or DataFrame")


def _normalize_trade_columns(df: pd.DataFrame) -> pd.DataFrame:
    if "direction" not in df.columns and "side" in df.columns:
        df["direction"] = df["side"]
    if "pnl" not in df.columns:
        if "pnl_points" in df.columns:
            df["pnl"] = df["pnl_points"]
        elif "pnl_after_cost_points" in df.columns:
            df["pnl"] = df["pnl_after_cost_points"]

    if "pnl_after_cost" not in df.columns:
        if "pnl_after_cost_points" in df.columns:
            df["pnl_after_cost"] = df["pnl_after_cost_points"]
        elif "pnl" in df.columns:
            df["pnl_after_cost"] = df["pnl"]

    if "direction" in df.columns:
        df["direction"] = df["direction"].map(_normalize_direction)

    return df


def _normalize_direction(value: Any) -> int:
    if value in {1, 1.0}:
        return 1
    if value in {-1, -1.0}:
        return -1

    direction = str(value).strip().lower()
    if direction in {"1", "long", "buy", "b", "新買"}:
        return 1
    if direction in {"-1", "short", "sell", "s", "新賣", "新卖"}:
        return -1
    raise ValueError(f"invalid direction: {value}")


def _max_drawdown_from_series(pnl: pd.Series) -> float:
    equity = pnl.cumsum()
    running_peak = equity.cummax()
    drawdown = equity - running_peak
    return float(abs(drawdown.min()))


def evaluate_oos_trades(trades: Iterable[TradeRecord] | pd.DataFrame) -> dict[str, float | int]:
    """Evaluate OOS performance from pre-existing trade records.

    This function does NOT generate strategy signals or orders.
    """
    df = _to_dataframe(trades)

    total_trades = int(len(df))
    gross_col = df["pnl"].astype(float)
    net_col = df["pnl_after_cost"].astype(float)

    wins = int((net_col > 0).sum())
    win_rate = wins / total_trades

    gross_pnl_points = float(gross_col.sum())
    net_pnl_points = float(net_col.sum())
    avg_trade_points = float(net_col.mean())
    max_drawdown_points = _max_drawdown_from_series(net_col)

    gross_profit = float(net_col[net_col > 0].sum())
    gross_loss_abs = float(abs(net_col[net_col < 0].sum()))
    profit_factor = inf if gross_loss_abs == 0 else gross_profit / gross_loss_abs

    long_trades = int((df["direction"] == 1).sum())
    short_trades = int((df["direction"] == -1).sum())

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
