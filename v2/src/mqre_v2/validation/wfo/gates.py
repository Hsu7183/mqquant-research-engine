from __future__ import annotations

from dataclasses import dataclass, replace

from mqre_v2.validation.wfo.results import WfoRoundResult, WfoSummary


@dataclass(frozen=True)
class WfoGateConfig:
    min_test_trade_count: int = 20
    max_test_mdd: float = 15000.0
    min_test_pf: float = 1.05
    min_pass_rate: float = 0.6
    require_positive_total_profit: bool = True


def evaluate_wfo_round(
    result: WfoRoundResult,
    config: WfoGateConfig,
) -> WfoRoundResult:
    fail_reasons: list[str] = []

    if result.test_trade_count < config.min_test_trade_count:
        fail_reasons.append("test_trade_count below minimum")
    if result.test_mdd > config.max_test_mdd:
        fail_reasons.append("test_mdd above maximum")
    if result.test_pf < config.min_test_pf:
        fail_reasons.append("test_pf below minimum")
    if result.test_net_profit <= 0:
        fail_reasons.append("test_net_profit not positive")

    return replace(
        result,
        pass_flag=len(fail_reasons) == 0,
        fail_reason="; ".join(fail_reasons),
    )


def evaluate_wfo_summary(
    summary: WfoSummary,
    config: WfoGateConfig,
) -> tuple[bool, str]:
    fail_reasons: list[str] = []

    if summary.pass_rate < config.min_pass_rate:
        fail_reasons.append("pass_rate below minimum")
    if config.require_positive_total_profit and summary.total_test_net_profit <= 0:
        fail_reasons.append("total_test_net_profit not positive")

    return len(fail_reasons) == 0, "; ".join(fail_reasons)
