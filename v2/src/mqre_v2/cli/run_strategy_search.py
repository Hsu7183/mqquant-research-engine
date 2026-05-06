from __future__ import annotations

import argparse
import os
import json
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable, Sequence

from mqre_v2.backtest.costs import CostConfig, net_pnl_points_for_trade
from mqre_v2.backtest.generated_strategy import backtest_generated_intraday_strategy
from mqre_v2.backtest.trade_export import export_trades_to_xs_txt
from mqre_v2.core.bars import BarRecord
from mqre_v2.cli.run_latest_pipeline import run_latest_pipeline
from mqre_v2.io.m1_parser import parse_m1_txt
from mqre_v2.strategy_gen.generator import (
    GeneratedStrategyConfig,
    generate_intraday_futures_strategies,
)


@dataclass(frozen=True, slots=True)
class StrategySearchWorkerContext:
    bars: list[BarRecord]
    output_folder: str
    cost_config: CostConfig
    min_net_profit_per_trade: float
    max_trades_per_day: float


_WORKER_CONTEXT: StrategySearchWorkerContext | None = None


def run_strategy_search(
    m1_path: str,
    num_strategies: int,
    seed: int | None,
    families: list[str] | None,
    start_date: date,
    end_date: date,
    output_folder: str = "runs/latest/txt",
    ranking_output: str = "runs/latest/reports/ranking.json",
    cost_config: CostConfig | None = None,
    min_net_profit_per_trade: float = 0.0,
    max_trades_per_day: float = 999999.0,
    workers: int = 0,
    progress_every: int = 10,
    sample_bars: int = 0,
    dry_run: bool = False,
    log_fn: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    effective_cost = cost_config or CostConfig()
    logger = log_fn or _null_logger
    started_at = time.perf_counter()
    resolved_workers = _resolve_workers(workers)

    logger("策略搜尋啟動")
    logger(f"讀取 M1：{m1_path}")
    bars = [
        bar
        for bar in parse_m1_txt(m1_path)
        if start_date <= bar.ts.date() <= end_date
    ]
    if sample_bars < 0:
        raise ValueError("sample_bars must be >= 0")
    if sample_bars > 0:
        bars = bars[-sample_bars:]
        logger(f"快速測試模式：只使用最後 {sample_bars} 根 bars")
    logger(f"M1 bars 筆數：{len(bars)}")

    configs = generate_intraday_futures_strategies(
        n=num_strategies,
        seed=seed,
        families=families,
    )
    logger(f"生成策略數：{num_strategies}")
    logger(f"使用 workers：{resolved_workers}")

    output_path = Path(output_folder)
    family_counts: Counter[str] = Counter(config.family for config in configs)
    ranking_filename = Path(ranking_output).name

    if dry_run:
        logger("策略搜尋完成")
        return {
            "generated_count": len(configs),
            "completed_backtests": 0,
            "non_empty_trade_files": 0,
            "ranking_json": str(Path("runs") / "latest" / "reports" / ranking_filename),
            "top_5": [],
            "family_counts": dict(sorted(family_counts.items())),
            "best_family": "",
            "cost": _cost_to_dict(effective_cost),
            "workers": resolved_workers,
            "sample_bars": sample_bars,
            "dry_run": True,
            "error_count": 0,
            "errors": [],
        }

    _clear_files(output_path, "*.txt")
    _clear_files(Path("runs") / "latest" / "reports" / "details", "*.json")

    worker_context = StrategySearchWorkerContext(
        bars=bars,
        output_folder=str(output_path),
        cost_config=effective_cost,
        min_net_profit_per_trade=min_net_profit_per_trade,
        max_trades_per_day=max_trades_per_day,
    )
    completed_backtests = 0
    non_empty_trade_files = 0
    strategy_quality: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, str]] = []

    for result in _run_backtests(
        configs=configs,
        context=worker_context,
        workers=resolved_workers,
    ):
        completed_backtests += 1
        if result.get("error"):
            errors.append(
                {
                    "strategy_id": str(result.get("strategy_id", "")),
                    "error": str(result.get("error", "")),
                }
            )
        else:
            quality = result.get("quality")
            if isinstance(quality, dict):
                strategy_quality[str(result["strategy_id"])] = quality
            if int(result.get("trades_count", 0)) > 0:
                non_empty_trade_files += 1

        if _should_log_progress(completed_backtests, len(configs), progress_every):
            elapsed = time.perf_counter() - started_at
            logger(
                f"已完成 {completed_backtests}/{len(configs)}，"
                f"有交易策略 {non_empty_trade_files}，耗時 {elapsed:.1f}s"
            )

    pipeline_summary = (
        run_latest_pipeline(
            base_dir="runs",
            start_date=start_date,
            end_date=end_date,
            output_filename=ranking_filename,
            cost_config=effective_cost,
            strategy_quality=strategy_quality,
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
    logger("策略搜尋完成")

    return {
        "generated_count": len(configs),
        "completed_backtests": completed_backtests,
        "non_empty_trade_files": non_empty_trade_files,
        "ranking_json": str(Path("runs") / "latest" / "reports" / ranking_filename),
        "top_5": top_5,
        "family_counts": dict(sorted(family_counts.items())),
        "best_family": best_family,
        "cost": _cost_to_dict(effective_cost),
        "workers": resolved_workers,
        "sample_bars": sample_bars,
        "dry_run": False,
        "error_count": len(errors),
        "errors": errors,
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
        cost_config=CostConfig(
            slippage_points_per_side=args.slippage_points,
            fee_money_per_side=args.fee_money,
            tax_rate=args.tax_rate,
            point_value=args.point_value,
            qty=args.qty,
        ),
        min_net_profit_per_trade=args.min_net_profit_per_trade,
        max_trades_per_day=args.max_trades_per_day,
        workers=args.workers,
        progress_every=args.progress_every,
        sample_bars=args.sample_bars,
        dry_run=args.dry_run,
        log_fn=_stdout_logger,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False))
    print(_build_chinese_summary(summary), flush=True)
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
    parser.add_argument("--slippage-points", type=float, default=2.0)
    parser.add_argument("--fee-money", type=float, default=0.0)
    parser.add_argument("--tax-rate", type=float, default=0.00002)
    parser.add_argument("--point-value", type=float, default=50.0)
    parser.add_argument("--qty", type=int, default=1)
    parser.add_argument("--min-net-profit-per-trade", type=float, default=0.0)
    parser.add_argument("--max-trades-per-day", type=float, default=999999.0)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--progress-every", type=int, default=10)
    parser.add_argument("--sample-bars", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
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


def _run_backtests(
    configs: list[GeneratedStrategyConfig],
    context: StrategySearchWorkerContext,
    workers: int,
):
    if workers <= 1:
        _init_strategy_search_worker(context)
        for config in configs:
            yield _backtest_one_strategy_worker(config)
        return

    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=_init_strategy_search_worker,
        initargs=(context,),
    ) as executor:
        futures = {
            executor.submit(_backtest_one_strategy_worker, config): config
            for config in configs
        }
        for future in as_completed(futures):
            config = futures[future]
            try:
                yield future.result()
            except Exception as exc:
                yield {
                    "strategy_id": config.strategy_id,
                    "trades_count": 0,
                    "txt_path": None,
                    "quality": {},
                    "error": str(exc),
                }


def _init_strategy_search_worker(context: StrategySearchWorkerContext) -> None:
    global _WORKER_CONTEXT
    _WORKER_CONTEXT = context


def _backtest_one_strategy_worker(config: GeneratedStrategyConfig) -> dict[str, Any]:
    if _WORKER_CONTEXT is None:
        return {
            "strategy_id": config.strategy_id,
            "trades_count": 0,
            "txt_path": None,
            "quality": {},
            "error": "worker context is not initialized",
        }

    try:
        trades = backtest_generated_intraday_strategy(_WORKER_CONTEXT.bars, config)
        txt_path = None
        quality: dict[str, Any] = {}
        if trades:
            quality = _quality_for_trades(
                trades=trades,
                cost_config=_WORKER_CONTEXT.cost_config,
                min_net_profit_per_trade=_WORKER_CONTEXT.min_net_profit_per_trade,
                max_trades_per_day=_WORKER_CONTEXT.max_trades_per_day,
            )
            output_path = Path(_WORKER_CONTEXT.output_folder) / f"{config.strategy_id}.txt"
            export_trades_to_xs_txt(
                trades=trades,
                output_path=str(output_path),
                strategy_name=config.strategy_id,
            )
            txt_path = str(output_path)

        return {
            "strategy_id": config.strategy_id,
            "trades_count": len(trades),
            "txt_path": txt_path,
            "quality": quality,
            "error": None,
        }
    except Exception as exc:
        return {
            "strategy_id": config.strategy_id,
            "trades_count": 0,
            "txt_path": None,
            "quality": {},
            "error": str(exc),
        }


def _resolve_workers(workers: int) -> int:
    if workers < 0:
        raise ValueError("workers must be >= 0")
    if workers == 0:
        return max(1, (os.cpu_count() or 1) - 1)
    return workers


def _should_log_progress(done: int, total: int, progress_every: int) -> bool:
    if done == total:
        return True
    return progress_every > 0 and done % progress_every == 0


def _stdout_logger(message: str) -> None:
    print(message, flush=True)


def _null_logger(message: str) -> None:
    _ = message


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
        "raw_total_profit": row.get("raw_total_profit"),
        "net_total_profit": row.get("net_total_profit"),
        "total_cost": row.get("total_cost"),
    }


def _quality_for_trades(
    trades: list,
    cost_config: CostConfig,
    min_net_profit_per_trade: float,
    max_trades_per_day: float,
) -> dict[str, Any]:
    net_pnls = [net_pnl_points_for_trade(trade, cost_config) for trade in trades]
    net_total = sum(net_pnls)
    trade_count = len(trades)
    trade_days = {trade.exit_time.date() for trade in trades}
    avg_net = net_total / trade_count if trade_count else 0.0
    avg_trades_per_day = trade_count / len(trade_days) if trade_days else 0.0
    fail_reasons: list[str] = []
    if trade_count < 30:
        fail_reasons.append("insufficient trades")
    if avg_net < min_net_profit_per_trade:
        fail_reasons.append("avg net pnl per trade below minimum")
    if avg_trades_per_day > max_trades_per_day:
        fail_reasons.append("too many trades per day")
    return {
        "avg_net_pnl_per_trade": avg_net,
        "avg_trades_per_day": avg_trades_per_day,
        "trade_count": trade_count,
        "fail_reasons": fail_reasons,
    }


def _cost_to_dict(cost_config: CostConfig) -> dict[str, float | int]:
    return {
        "slippage_points_per_side": cost_config.slippage_points_per_side,
        "round_trip_slippage_points": cost_config.slippage_points_per_side * 2.0,
        "fee_money_per_side": cost_config.fee_money_per_side,
        "tax_rate": cost_config.tax_rate,
        "point_value": cost_config.point_value,
        "qty": cost_config.qty,
    }


def _build_chinese_summary(summary: dict[str, Any]) -> str:
    cost = summary["cost"]
    top1 = summary["top_5"][0] if summary["top_5"] else {}
    return "\n".join(
        [
            "策略搜尋完成：",
            f"- 生成策略數：{summary['generated_count']}",
            f"- 有交易策略數：{summary['non_empty_trade_files']}",
            f"- 單邊滑點：{cost['slippage_points_per_side']}",
            f"- 來回滑點：{cost['round_trip_slippage_points']}",
            f"- 單邊手續費：{cost['fee_money_per_side']}",
            f"- 期交稅率：{cost['tax_rate']}",
            f"- 每點價值：{cost['point_value']}",
            f"- 口數：{cost['qty']}",
            f"- 最佳策略族群：{summary.get('best_family', '')}",
            f"- Top1 策略：{top1.get('strategy_name', '')}",
            f"- Top1 毛損益：{top1.get('raw_total_profit', '')}",
            f"- Top1 扣成本後損益：{top1.get('net_total_profit', '')}",
            f"- Top1 通過率：{top1.get('pass_rate', '')}",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
