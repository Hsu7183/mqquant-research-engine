from __future__ import annotations

from dataclasses import dataclass
from math import inf
from pathlib import Path
from typing import Any

from mqre_v2.core.trades import TradeRecord
from mqre_v2.io.txt_parser import parse_xs_txt
from mqre_v2.validation.wfo.results import WfoRoundResult
from mqre_v2.validation.wfo.windows import WfoWindow


@dataclass(frozen=True)
class TxtWfoInput:
    strategy_name: str
    txt_path: str
    params_hash: str = "txt-import"


def compute_trade_metrics(trades: list[TradeRecord]) -> dict[str, float | int]:
    if not trades:
        return {
            "net_profit": 0.0,
            "mdd": 0.0,
            "pf": 0.0,
            "trade_count": 0,
        }

    pnl_values = [trade.pnl for trade in trades]
    gross_profit = sum(value for value in pnl_values if value > 0)
    gross_loss = abs(sum(value for value in pnl_values if value < 0))

    if gross_loss == 0:
        pf = inf if gross_profit > 0 else 0.0
    else:
        pf = gross_profit / gross_loss

    return {
        "net_profit": float(sum(pnl_values)),
        "mdd": _max_drawdown(pnl_values),
        "pf": float(pf),
        "trade_count": len(trades),
    }


def build_txt_evaluate_fn(txt_input: TxtWfoInput):
    all_trades = parse_xs_txt(Path(txt_input.txt_path).read_text(encoding="utf-8-sig"))

    def evaluate_fn(window: WfoWindow, optimizer_result: Any) -> WfoRoundResult:
        filtered_trades = [
            trade
            for trade in all_trades
            if window.test_start <= trade.exit_time.date() <= window.test_end
        ]
        metrics = compute_trade_metrics(filtered_trades)

        return WfoRoundResult(
            round_id=window.round_id,
            train_start=window.train_start,
            train_end=window.train_end,
            gap_start=window.gap_start,
            gap_end=window.gap_end,
            test_start=window.test_start,
            test_end=window.test_end,
            strategy_name=txt_input.strategy_name,
            params_hash=txt_input.params_hash,
            train_net_profit=float(_get_value(optimizer_result, "train_net_profit", 0.0)),
            train_mdd=float(_get_value(optimizer_result, "train_mdd", 0.0)),
            train_pf=float(_get_value(optimizer_result, "train_pf", 0.0)),
            train_trade_count=int(_get_value(optimizer_result, "train_trade_count", 0)),
            test_net_profit=float(metrics["net_profit"]),
            test_mdd=float(metrics["mdd"]),
            test_pf=float(metrics["pf"]),
            test_trade_count=int(metrics["trade_count"]),
            pass_flag=False,
            fail_reason="",
        )

    return evaluate_fn


def _max_drawdown(pnl_values: list[float]) -> float:
    equity = 0.0
    running_peak = 0.0
    max_drawdown = 0.0

    for pnl in pnl_values:
        equity += pnl
        running_peak = max(running_peak, equity)
        max_drawdown = max(max_drawdown, running_peak - equity)

    return float(max_drawdown)


def _get_value(source: Any, name: str, default: Any) -> Any:
    if isinstance(source, dict):
        return source.get(name, default)
    return getattr(source, name, default)
