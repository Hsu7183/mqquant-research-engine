from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mqre_v2.validation.wfo.results import WfoRoundResult
from mqre_v2.validation.wfo.windows import WfoWindow


@dataclass(frozen=True)
class OptimizerResult:
    strategy_name: str
    params: dict[str, Any]
    params_hash: str
    train_net_profit: float
    train_mdd: float
    train_pf: float
    train_trade_count: int


@dataclass(frozen=True)
class BacktestResult:
    test_net_profit: float
    test_mdd: float
    test_pf: float
    test_trade_count: int


def default_optimize_fn(window: WfoWindow) -> OptimizerResult:
    params: dict[str, Any] = {
        "adapter": "dummy",
        "round_id": window.round_id,
    }

    return OptimizerResult(
        strategy_name="dummy_strategy",
        params=params,
        params_hash=str(params),
        train_net_profit=1000.0,
        train_mdd=1000.0,
        train_pf=1.2,
        train_trade_count=30,
    )


def default_evaluate_fn(
    window: WfoWindow,
    optimizer_result: OptimizerResult,
) -> WfoRoundResult:
    backtest_result = BacktestResult(
        test_net_profit=500.0,
        test_mdd=1000.0,
        test_pf=1.2,
        test_trade_count=25,
    )

    return WfoRoundResult(
        round_id=window.round_id,
        train_start=window.train_start,
        train_end=window.train_end,
        gap_start=window.gap_start,
        gap_end=window.gap_end,
        test_start=window.test_start,
        test_end=window.test_end,
        strategy_name=optimizer_result.strategy_name,
        params_hash=optimizer_result.params_hash,
        train_net_profit=optimizer_result.train_net_profit,
        train_mdd=optimizer_result.train_mdd,
        train_pf=optimizer_result.train_pf,
        train_trade_count=optimizer_result.train_trade_count,
        test_net_profit=backtest_result.test_net_profit,
        test_mdd=backtest_result.test_mdd,
        test_pf=backtest_result.test_pf,
        test_trade_count=backtest_result.test_trade_count,
        pass_flag=False,
        fail_reason="unchecked",
    )
