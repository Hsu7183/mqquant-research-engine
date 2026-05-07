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
from mqre_v2.strategy.strategy_1001plus import (
    Strategy1001PlusParams,
    backtest_strategy_1001plus,
)


def backtest_m1_to_latest(
    m1_path: str,
    strategy_name: str,
    strategy: str = "simple_m1",
) -> dict:
    bars = parse_m1_txt(m1_path)
    trades = _run_strategy(bars, strategy_name, strategy)

    output_path = Path("runs") / "latest" / "txt" / f"{strategy_name}.txt"
    export_trades_to_xs_txt(
        trades=trades,
        output_path=str(output_path),
        strategy_name=strategy_name,
    )

    return {
        "strategy_name": strategy_name,
        "strategy": strategy,
        "bars_count": len(bars),
        "trades_count": len(trades),
        "total_pnl": sum(trade.pnl for trade in trades),
        "output_trade_txt": str(output_path),
        "next_step": "python -m mqre_v2.cli.run_latest_pipeline",
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    payload = backtest_m1_to_latest(args.m1_path, args.strategy_name, args.strategy)
    print(json.dumps(payload, ensure_ascii=False, allow_nan=False))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a latest-run trade TXT from an M1 file."
    )
    parser.add_argument("--m1-path", required=True)
    parser.add_argument("--strategy-name", required=True)
    parser.add_argument(
        "--strategy",
        choices=["simple_m1", "1001plus"],
        default="simple_m1",
    )
    return parser


def _run_strategy(bars, strategy_name: str, strategy: str):
    if strategy == "simple_m1":
        return backtest_simple_m1_strategy(
            bars,
            SimpleM1StrategyParams(strategy_name=strategy_name),
        )
    if strategy == "1001plus":
        return backtest_strategy_1001plus(
            bars,
            Strategy1001PlusParams(strategy_name=strategy_name),
        )
    raise ValueError(f"unsupported strategy: {strategy}")


if __name__ == "__main__":
    raise SystemExit(main())
