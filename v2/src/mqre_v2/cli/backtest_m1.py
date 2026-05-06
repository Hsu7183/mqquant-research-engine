from __future__ import annotations

import argparse
import json
from typing import Sequence

from mqre_v2.backtest.simple_m1_strategy import (
    SimpleM1StrategyParams,
    backtest_simple_m1_strategy,
)
from mqre_v2.backtest.trade_export import export_trades_to_xs_txt
from mqre_v2.io.m1_parser import parse_m1_txt


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    params = SimpleM1StrategyParams(
        strategy_name=args.strategy_name,
        entry_buffer=args.entry_buffer,
        take_profit=args.take_profit,
        stop_loss=args.stop_loss,
        max_hold_bars=args.max_hold_bars,
        begin_time=args.begin_time,
        end_time=args.end_time,
        force_exit_time=args.force_exit_time,
    )

    bars = parse_m1_txt(args.m1_path)
    trades = backtest_simple_m1_strategy(bars, params)
    export_trades_to_xs_txt(
        trades=trades,
        output_path=args.output_trade_txt,
        strategy_name=params.strategy_name,
    )

    payload = {
        "strategy_name": params.strategy_name,
        "bars_count": len(bars),
        "trades_count": len(trades),
        "total_pnl": sum(trade.pnl for trade in trades),
        "output_trade_txt": args.output_trade_txt,
    }
    print(json.dumps(payload, ensure_ascii=False, allow_nan=False))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backtest a simple M1 momentum strategy.")
    parser.add_argument("--m1-path", required=True)
    parser.add_argument("--output-trade-txt", required=True)
    parser.add_argument("--strategy-name", default="simple_m1_momentum")
    parser.add_argument("--entry-buffer", default=10.0, type=float)
    parser.add_argument("--take-profit", default=30.0, type=float)
    parser.add_argument("--stop-loss", default=20.0, type=float)
    parser.add_argument("--max-hold-bars", default=30, type=int)
    parser.add_argument("--begin-time", default="0848")
    parser.add_argument("--end-time", default="1240")
    parser.add_argument("--force-exit-time", default="1312")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
