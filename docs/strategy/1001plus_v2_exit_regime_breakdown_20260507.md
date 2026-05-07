# 1001plus v2_exit Annual / Regime Bucket Breakdown - 2026-05-07

## 1. Top Challenger

- data source: `1001plus_v2_exit 300-run artifacts`
- source caution: this is not the earlier `risk_constrained` artifact set.
- scope: this report only describes the `v2_exit` failed experiment regime breakdown.
- strategy_id: `1001plus_v2exit_ES5_EL31_RL70_RS30_AS1p2_AT3p7_D44_VW1_TR1p5_GB0p3_TM66_TF0p5`
- promotion_decision: `reject`
- decision_reason: `candidate failed critical promotion thresholds`
- score: `1.9818`
- sharpe: `0.412088`
- max_drawdown: `4139.0687`
- trade_count: `312`
- data_source_note: `runs/latest` contains `1001plus_v2_exit` 300-run artifacts; this is not the earlier risk_constrained run.

## 2. Annual Breakdown Table

| year | total_pnl | trade_count | win_rate | max_drawdown | avg_trade_pnl |
|---:|---:|---:|---:|---:|---:|
| 2020 | -6611.5022 | 1637 | 46.24% | 6617.6551 | -4.038792 |
| 2021 | -8053.5421 | 1564 | 43.22% | 14671.1956 | -5.149324 |
| 2022 | -7674.6567 | 1601 | 44.78% | 22347.5858 | -4.793664 |
| 2023 | -7540.0017 | 1577 | 44.58% | 29885.8552 | -4.781231 |
| 2024 | -6965.5336 | 1519 | 45.75% | 36854.9097 | -4.585605 |
| 2025 | -5347.7809 | 1600 | 48.94% | 42199.1692 | -3.342363 |
| 2026 | -2858.0258 | 447 | 47.65% | 45074.8511 | -6.393794 |

## 3. Worst Years

| year | total_pnl | trade_count | win_rate | max_drawdown | avg_trade_pnl |
|---:|---:|---:|---:|---:|---:|
| 2021 | -8053.5421 | 1564 | 43.22% | 14671.1956 | -5.149324 |
| 2022 | -7674.6567 | 1601 | 44.78% | 22347.5858 | -4.793664 |
| 2023 | -7540.0017 | 1577 | 44.58% | 29885.8552 | -4.781231 |

## 4. Worst Months

| month | total_pnl | trade_count | max_drawdown | daily_pnl_std |
|---|---:|---:|---:|---:|
| 2026-03 | -1678.7943 | 137 | 44462.8251 | 93.857997 |
| 2021-01 | -1189.2899 | 161 | 7806.9448 | 44.343811 |
| 2025-12 | -944.8495 | 150 | 42199.1692 | 37.082076 |
| 2024-05 | -886.7932 | 140 | 32708.3655 | 30.567608 |
| 2021-08 | -871.9398 | 153 | 11719.9748 | 45.946814 |
| 2020-12 | -862.9749 | 170 | 6617.6550 | 31.121364 |
| 2025-09 | -857.1441 | 155 | 40739.2026 | 45.895073 |
| 2021-06 | -826.9182 | 121 | 10387.6214 | 36.822576 |
| 2024-08 | -820.3839 | 117 | 34613.5896 | 87.941677 |
| 2022-05 | -806.3954 | 145 | 17933.5832 | 36.479628 |

## 5. Regime Bucket Summary

| bucket | months | total_pnl | trade_count | avg_monthly_pnl | max_drawdown | negative_months |
|---|---:|---:|---:|---:|---:|---:|
| chop_bad | 37 | -24442.7722 | 5420 | -660.6155 | 44462.8251 | 37 |
| high_vol | 38 | -21770.9067 | 4961 | -572.9186 | 45074.8511 | 36 |
| high_vol_chop_bad | 19 | -12227.7454 | 2759 | -643.5655 | 44462.8251 | 19 |
| high_vol_trend_good | 2 | 156.0181 | 300 | 78.00905 | 42250.1551 | 0 |
| high_vol_weak_low_activity | 17 | -9699.1794 | 1902 | -570.5400 | 45074.8511 | 17 |
| low_vol | 38 | -23280.1363 | 4984 | -612.6352 | 37936.8050 | 38 |
| low_vol_chop_bad | 18 | -12215.0268 | 2661 | -678.6126 | 32708.3655 | 18 |
| low_vol_weak_low_activity | 20 | -11065.1095 | 2323 | -553.2555 | 37936.8050 | 20 |
| trend_good | 2 | 156.0181 | 300 | 78.00905 | 42250.1551 | 0 |
| weak_low_activity | 37 | -20764.2889 | 4225 | -561.1970 | 45074.8511 | 37 |

## 6. Interpretation

- main_failure_pattern: `high_vol_chop_bad losses dominate`
- Worst year is `2021` with total_pnl `-8053.5421`.
- Worst month is `2026-03` with total_pnl `-1678.7943`.
- Negative high-trade-count months: `37`.
- Data source caution: `runs/latest` contains `1001plus_v2_exit` 300-run artifacts; this is not the earlier risk_constrained run.
- Worst regime bucket is `chop_bad` with total_pnl `-24442.7722`.

## 7. Next Steps

1. Do not disable a specific calendar year blindly; first confirm whether bad years share a market regime.
2. Add a regime filter if the losses concentrate in `chop_bad` or high-volatility negative months.
3. Reduce trade frequency only if high-trade-count months also show strongly negative expectancy.
4. Re-check entry filters before adding more exit variations, especially if losses cluster in low-quality trend/chop buckets.
5. Re-run this script after restoring the intended risk_constrained artifacts if the current `runs/latest` is not the target experiment.
