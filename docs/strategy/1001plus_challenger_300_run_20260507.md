# 1001plus Challenger 300-Run Result

## 1. Run Metadata

- job_id: `20260507123017_9dae2e1d`
- generator: `1001plus`
- num_strategies: `300`
- seed: `42`
- completed: `300/300`
- git status: `clean`

## 2. Top 10 Ranking

| rank | strategy_id | score | sharpe | max_drawdown | trade_count |
|---:|---|---:|---:|---:|---:|
| 1 | `1001plus_ES7_EL31_RL64_RS30_AS1p3_AT4p1_D48_VW0` | 4.5725 | 0.559132 | 3018.7901 | 312 |
| 2 | `1001plus_ES9_EL38_RL64_RS31_AS1p9_AT4p6_D49_VW1` | 4.5704 | 0.596839 | 3397.9633 | 324 |
| 3 | `1001plus_ES4_EL38_RL68_RS30_AS2p7_AT4p9_D17_VW1` | 4.5649 | 0.616133 | 3596.4625 | 336 |
| 4 | `1001plus_ES10_EL44_RL70_RS30_AS1_AT3p5_D17_VW0` | 4.3840 | 0.561636 | 3232.3666 | 348 |
| 5 | `1001plus_ES8_EL13_RL67_RS30_AS1p6_AT4p2_D46_VW0` | 4.3570 | 0.575291 | 3395.8804 | 360 |
| 6 | `1001plus_ES9_EL24_RL70_RS30_AS1p8_AT4p5_D34_VW0` | 4.3017 | 0.587461 | 3572.9209 | 372 |
| 7 | `1001plus_ES4_EL49_RL66_RS32_AS2p4_AT5_D37_VW1` | 4.1840 | 0.615312 | 3969.1676 | 384 |
| 8 | `1001plus_ES10_EL25_RL63_RS31_AS2p3_AT3p2_D45_VW1` | 4.1378 | 0.589674 | 3758.9544 | 396 |
| 9 | `1001plus_ES3_EL38_RL69_RS30_AS1p3_AT4p8_D19_VW0` | 4.1063 | 0.573548 | 3629.1596 | 408 |
| 10 | `1001plus_ES5_EL24_RL69_RS31_AS1p9_AT2p8_D45_VW0` | 4.0588 | 0.575649 | 3697.6778 | 420 |

## 3. Decision Audit

- challenger: `1001plus_ES7_EL31_RL64_RS30_AS1p3_AT4p1_D48_VW0`
- promotion_decision: `reject`
- reason: `candidate failed critical promotion thresholds`

## 4. Interpretation

- 300 組 1001plus challenger 已成功跑完整條 pipeline。
- dashboard / exporter / decision engine 正常。
- 目前 top challenger 未達升級門檻。
- 因此 baseline 不應被替換。

## 5. Next Steps

1. 檢查 rejection checks。
2. 分析 top 10 共同參數特徵。
3. 做 plateau / robustness 分析。
4. 再決定是否擴大到 1000 組或調整 generator 範圍。
