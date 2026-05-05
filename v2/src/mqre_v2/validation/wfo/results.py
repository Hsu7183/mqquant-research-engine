from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass(frozen=True)
class WfoRoundResult:
    round_id: int
    train_start: date
    train_end: date
    gap_start: date
    gap_end: date
    test_start: date
    test_end: date
    strategy_name: str
    params_hash: str
    train_net_profit: float
    train_mdd: float
    train_pf: float
    train_trade_count: int
    test_net_profit: float
    test_mdd: float
    test_pf: float
    test_trade_count: int
    pass_flag: bool
    fail_reason: str


@dataclass(frozen=True)
class WfoSummary:
    total_rounds: int
    passed_rounds: int
    failed_rounds: int
    pass_rate: float
    total_test_net_profit: float
    average_test_net_profit: float
    max_test_mdd: float
    average_test_pf: float
    total_test_trade_count: int


def summarize_wfo_results(results: Iterable[WfoRoundResult]) -> WfoSummary:
    result_list = list(results)
    if not result_list:
        raise ValueError("results cannot be empty")

    total_rounds = len(result_list)
    passed_rounds = sum(1 for result in result_list if result.pass_flag)
    failed_rounds = total_rounds - passed_rounds
    total_test_net_profit = sum(result.test_net_profit for result in result_list)

    return WfoSummary(
        total_rounds=total_rounds,
        passed_rounds=passed_rounds,
        failed_rounds=failed_rounds,
        pass_rate=passed_rounds / total_rounds,
        total_test_net_profit=total_test_net_profit,
        average_test_net_profit=total_test_net_profit / total_rounds,
        max_test_mdd=max(result.test_mdd for result in result_list),
        average_test_pf=sum(result.test_pf for result in result_list) / total_rounds,
        total_test_trade_count=sum(result.test_trade_count for result in result_list),
    )
