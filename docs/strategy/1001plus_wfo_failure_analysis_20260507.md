# 1001plus WFO Failure Analysis - 2026-05-07

## 1. WFO Summary

- challenger_strategy: `1001plus_v2exit_ES5_EL31_RL70_RS30_AS1p2_AT3p7_D44_VW1_TR1p5_GB0p3_TM66_TF0p5`
- promotion_decision: `reject`
- decision_reason: `candidate failed critical promotion thresholds`
- WFO pass_rate: `0`
- WFO stability_score: `0`
- WFO avg_sharpe: `0.132278`
- failed_rounds: `6/6`

Decision WFO thresholds:

| check | value | rule | threshold | status |
|---|---:|---|---:|---|
| pass_rate | 0 | >= | 0.6 | fail |
| avg_sharpe | 0.132278 | >= | 1 | fail |
| stability_score | 0 | >= | 0.6 | fail |

## 2. Failed Rounds Table

| round_id | return | sharpe | max_dd | trade_count | passed |
|---:|---:|---:|---:|---:|---|
| 1 | 0 | 0 | 0 | 0 | False |
| 2 | 0 | 0 | 0 | 0 | False |
| 3 | 0 | 0 | 0 | 0 | False |
| 4 | 0 | 0 | 0 | 0 | False |
| 5 | 0 | 0 | 0 | 0 | False |
| 6 | -0.023426 | 0.793667 | 2632.8542 | 854 | False |

## 3. Passed Rounds Table

No rounds in this category.

## 4. Failure Pattern

- main_pattern: `zero pass rate and zero stability score`
- failed_round_count: `6`
- failed_rounds_with_negative_return: `1`
- failed_rounds_with_positive_return: `0`
- avg_failed_round_sharpe: `0.132278`
- avg_failed_round_max_dd: `438.8090`
- avg_failed_round_trade_count: `142.3333`
- pass_rate gap: `-0.6`
- avg_sharpe gap: `-0.867722`
- stability_score gap: `-0.6`

## 5. Interpretation

- Top challenger: `1001plus_v2exit_ES5_EL31_RL70_RS30_AS1p2_AT3p7_D44_VW1_TR1p5_GB0p3_TM66_TF0p5`
- Ranking score is only `-1.3101`, far below the promotion score threshold in decision_audit.
- WFO pass_rate is `0`, below the required `0.6`.
- WFO stability_score is `0`, below the required `0.6`.
- WFO avg_sharpe is `0.132278`, below the required `1`.
- Worst return round: round `6` with return `-0.023426`.
- Worst drawdown round: round `6` with max_dd `2632.8542`.

The risk-constrained generator reduced portfolio-level risk metrics compared with the default 300-run, but WFO validation still failed. The failure is not caused by a single bad round only. Every WFO round is marked as failed, and most rounds have negative return. This means the current challenger set does not yet show stable cross-window behavior.

The baseline should not be upgraded from this run. The correct next step is to inspect WFO round behavior and regime dependency, not to relax the promotion threshold.

## 6. Next Steps

1. Add WFO round-level diagnostics by year or market regime.
2. Build regime buckets to separate trend, range, volatile breakout, and afternoon trend behavior.
3. Check whether WFO failures cluster in specific years or specific volatility regimes.
4. Narrow the generator range only after identifying which parameters are stable across rounds.
5. Consider adding controlled exit variations such as time stop or trailing stop, while keeping the 1001plus entry structure anchored.
6. Re-run risk-constrained candidates after WFO diagnostics, then compare pass_rate and stability_score before any baseline decision.
