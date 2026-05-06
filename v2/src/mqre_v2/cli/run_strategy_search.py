from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Sequence

from mqre_v2.backtest.generated_strategy import backtest_generated_intraday_strategy
from mqre_v2.backtest.trade_export import export_trades_to_xs_txt
from mqre_v2.cli.run_latest_pipeline import run_latest_pipeline
from mqre_v2.io.m1_parser import parse_m1_txt
from mqre_v2.strategy_gen.generator import generate_intraday_futures_strategies


def run_strategy_search(
    m1_path: str,
    num_strategies: int,
    seed: int | None,
    families: list[str] | None,
    start_date: date,
    end_date: date,
    output_folder: str = "runs/latest/txt",
    ranking_output: str = "runs/latest/reports/ranking.json",
) -> dict[str, Any]:
    bars = [
        bar
        for bar in parse_m1_txt(m1_path)
        if start_date <= bar.ts.date() <= end_date
    ]
    configs = generate_intraday_futures_strategies(
        n=num_strategies,
        seed=seed,
        families=families,
    )

    output_path = Path(output_folder)
    _clear_files(output_path, "*.txt")
    _clear_files(Path("runs") / "latest" / "reports" / "details", "*.json")

    completed_backtests = 0
    non_empty_trade_files = 0
    family_counts: Counter[str] = Counter()
    for config in configs:
        completed_backtests += 1
        family_counts[config.family] += 1
        trades = backtest_generated_intraday_strategy(bars, config)
        if not trades:
            continue

        export_trades_to_xs_txt(
            trades=trades,
            output_path=str(output_path / f"{config.strategy_id}.txt"),
            strategy_name=config.strategy_id,
        )
        non_empty_trade_files += 1

    ranking_filename = Path(ranking_output).name
    pipeline_summary = (
        run_latest_pipeline(
            base_dir="runs",
            start_date=start_date,
            end_date=end_date,
            output_filename=ranking_filename,
        )
        if non_empty_trade_files
        else {
            "output_json_path": ranking_output,
            "top_10": [],
            "detail_json_count": 0,
        }
    )
    top_5 = [_compact_ranking_row(item) for item in list(pipeline_summary.get("top_10", []))[:5]]
    best_family = _strategy_family(str(top_5[0]["strategy_name"])) if top_5 else ""

    return {
        "generated_count": len(configs),
        "completed_backtests": completed_backtests,
        "non_empty_trade_files": non_empty_trade_files,
        "ranking_json": str(Path("runs") / "latest" / "reports" / ranking_filename),
        "top_5": top_5,
        "family_counts": dict(sorted(family_counts.items())),
        "best_family": best_family,
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    summary = run_strategy_search(
        m1_path=args.m1_path,
        num_strategies=args.num_strategies,
        seed=args.seed,
        families=_parse_families(args.families),
        start_date=args.start_date,
        end_date=args.end_date,
        output_folder=args.output_folder,
        ranking_output=args.ranking_output,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate and rank intraday futures strategies.")
    parser.add_argument("--m1-path", required=True)
    parser.add_argument("--num-strategies", required=True, type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--families", default="")
    parser.add_argument("--start-date", required=True, type=_parse_date)
    parser.add_argument("--end-date", required=True, type=_parse_date)
    parser.add_argument("--output-folder", default="runs/latest/txt")
    parser.add_argument("--ranking-output", default="runs/latest/reports/ranking.json")
    return parser


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid date: {value}") from exc


def _parse_families(value: str) -> list[str] | None:
    families = [item.strip() for item in value.split(",") if item.strip()]
    return families or None


def _clear_files(folder: Path, pattern: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for path in folder.glob(pattern):
        if path.is_file():
            path.unlink()


def _strategy_family(strategy_name: str) -> str:
    known = [
        "trend_breakout",
        "open_range_breakout",
        "vwap_pullback",
        "mean_reversion_range",
        "volume_breakout",
        "breakdown_momentum",
        "slow_grind_trend",
        "afternoon_trend_extension",
    ]
    for family in known:
        if strategy_name.startswith(f"{family}_"):
            return family
    return strategy_name.rsplit("_", 1)[0]


def _compact_ranking_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "rank": row.get("rank"),
        "strategy_name": row.get("strategy_name"),
        "score": row.get("score"),
        "total_test_net_profit": row.get("total_test_net_profit"),
        "pass_rate": row.get("pass_rate"),
        "max_test_mdd": row.get("max_test_mdd"),
        "average_test_pf": row.get("average_test_pf"),
        "passed": row.get("passed"),
        "fail_reason": row.get("fail_reason", ""),
    }


if __name__ == "__main__":
    raise SystemExit(main())
