# 1001plus risk_constrained Annual / Regime Bucket Breakdown - 2026-05-07

## 1. Top Challenger

- data source: `1001plus risk_constrained 300-run artifacts`
- scope: this report describes the risk_constrained 300-run regime breakdown.
- job_id: `20260507151145_bbd43bbf`
- strategy_id: `1001plus_ES7_EL40_RL66_RS30_AS1p4_AT3p4_D50_VW1`
- promotion_decision: `reject`
- decision_reason: `candidate failed critical promotion thresholds`
- score: `5.1245`
- sharpe: `0.59287`
- max_drawdown: `2804.1831`
- trade_count: `312`
- data_source_note: `runs/latest` contains 1001plus risk_constrained 300-run artifacts for this report.

## 2. Annual Breakdown Table

| year | total_pnl | trade_count | win_rate | max_drawdown | avg_trade_pnl |
|---:|---:|---:|---:|---:|---:|
| 2020 | -4123.6018 | 1170 | 30.77% | 4270.8853 | -3.524446 |
| 2021 | -4806.8261 | 1099 | 29.39% | 8957.4600 | -4.373818 |
| 2022 | -4661.3280 | 1112 | 30.49% | 13618.7887 | -4.191842 |
| 2023 | -4864.7269 | 1067 | 28.77% | 18483.5128 | -4.559257 |
| 2024 | -3864.8265 | 1044 | 31.99% | 22375.8508 | -3.701941 |
| 2025 | -1911.2701 | 1081 | 34.41% | 24312.1515 | -1.768057 |
| 2026 | 234.6847 | 265 | 35.47% | 24368.3826 | 0.885603 |

## 3. Worst Years

| year | total_pnl | trade_count | win_rate | max_drawdown | avg_trade_pnl |
|---:|---:|---:|---:|---:|---:|
| 2023 | -4864.7269 | 1067 | 28.77% | 18483.5128 | -4.559257 |
| 2021 | -4806.8261 | 1099 | 29.39% | 8957.4600 | -4.373818 |
| 2022 | -4661.3280 | 1112 | 30.49% | 13618.7887 | -4.191842 |

## 4. Worst Months

| month | total_pnl | trade_count | max_drawdown | daily_pnl_std |
|---|---:|---:|---:|---:|
| 2026-03 | -1286.2316 | 87 | 24164.0952 | 203.9682 |
| 2024-11 | -864.4747 | 89 | 22060.9614 | 98.350507 |
| 2025-03 | -818.1378 | 90 | 23055.2279 | 75.958241 |
| 2021-11 | -768.8490 | 97 | 8466.8768 | 35.489542 |
| 2023-07 | -750.0333 | 107 | 16762.0106 | 46.926654 |
| 2022-09 | -739.9194 | 96 | 12681.5604 | 47.393561 |
| 2021-03 | -689.5667 | 100 | 5464.7335 | 58.813505 |
| 2023-05 | -639.1326 | 98 | 15668.1264 | 29.111129 |
| 2022-04 | -635.9967 | 81 | 10467.5990 | 61.282886 |
| 2021-10 | -620.1559 | 87 | 7698.0281 | 71.301598 |

## 5. Regime Bucket Summary

| bucket | months | total_pnl | trade_count | avg_monthly_pnl | max_drawdown | negative_months |
|---|---:|---:|---:|---:|---:|---:|
| chop_bad | 34 | -15339.0992 | 3398 | -451.1500 | 24312.1515 | 34 |
| high_vol | 38 | -7813.4671 | 3376 | -205.6176 | 24368.3826 | 25 |
| high_vol_chop_bad | 12 | -4470.6980 | 1204 | -372.5582 | 24312.1515 | 12 |
| high_vol_trend_good | 13 | 3228.0436 | 1123 | 248.3110 | 24246.9374 | 0 |
| high_vol_weak_low_activity | 13 | -6570.8127 | 1049 | -505.4471 | 24368.3826 | 13 |
| low_vol | 38 | -16184.4276 | 3462 | -425.9060 | 19294.5784 | 38 |
| low_vol_chop_bad | 22 | -10868.4012 | 2194 | -494.0182 | 18973.4907 | 22 |
| low_vol_weak_low_activity | 16 | -5316.0264 | 1268 | -332.2516 | 19294.5784 | 16 |
| trend_good | 13 | 3228.0436 | 1123 | 248.3110 | 24246.9374 | 0 |
| weak_low_activity | 29 | -11886.8391 | 2317 | -409.8910 | 24368.3826 | 29 |

## 6. Interpretation

- main_failure_pattern: `high_vol_chop_bad losses dominate`
- Worst year is `2023` with total_pnl `-4864.7269`.
- Worst month is `2026-03` with total_pnl `-1286.2316`.
- Negative high-trade-count months: `34`.
- Data source caution: `runs/latest` contains 1001plus risk_constrained 300-run artifacts for this report.
- Worst regime bucket is `low_vol` with total_pnl `-16184.4276`.

## 7. Next Steps

1. Do not disable a specific calendar year blindly; first confirm whether bad years share a market regime.
2. Add a regime filter if the losses concentrate in `chop_bad` or high-volatility negative months.
3. Reduce trade frequency only if high-trade-count months also show strongly negative expectancy.
4. Re-check entry filters before adding more exit variations, especially if losses cluster in low-quality trend/chop buckets.
5. Re-run this script after each 300-run so the report title and source follow the current `runs/latest` artifacts.
