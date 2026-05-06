from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from mqre_v2.backtest.simple_m1_strategy import (
    SimpleM1StrategyParams,
    backtest_simple_m1_strategy,
)
from mqre_v2.backtest.trade_export import export_trades_to_xs_txt
from mqre_v2.io.m1_parser import parse_m1_txt


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    params = SimpleM1StrategyParams(strategy_name=args.strategy_name)

    bars = parse_m1_txt(args.m1_path)
    trades = backtest_simple_m1_strategy(bars, params)

    output_path = Path("runs") / "latest" / "txt" / f"{args.strategy_name}.txt"
    export_trades_to_xs_txt(
        trades=trades,
        output_path=str(output_path),
        strategy_name=args.strategy_name,
    )

    payload = {
        "strategy_name": args.strategy_name,
        "bars_count": len(bars),
        "trades_count": len(trades),
        "total_pnl": sum(trade.pnl for trade in trades),
        "output_trade_txt": str(output_path),
        "next_step": "python -m mqre_v2.cli.run_latest_pipeline",
    }
    print(json.dumps(payload, ensure_ascii=False, allow_nan=False))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a latest-run trade TXT from an M1 file."
    )
    parser.add_argument("--m1-path", required=True)
    parser.add_argument("--strategy-name", required=True)
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
