# 1001plus Rejection Analysis

## 1. Decision Summary

- challenger_strategy: `1001plus_ES7_EL31_RL64_RS30_AS1p3_AT4p1_D48_VW0`
- promotion_decision: `reject`
- reason: `candidate failed critical promotion thresholds`
- score: `4.5725`
- forward_status: `good`
- rejection_bottleneck: `risk`

## 2. Failed Checks Table

| section | check | value | rule | threshold | margin | severity |
|---|---|---:|---|---:|---:|---|
| ranking | score | 4.5725 | >= | 100 | -95.4275 | failed |
| ranking | profit_factor | 0.759132 | >= | 1.1 | -0.340868 | failed |
| wfo | pass_rate | 0 | >= | 0.6 | -0.6 | failed |
| wfo | avg_sharpe | 0.759132 | >= | 1 | -0.240868 | failed |
| wfo | stability_score | 0 | >= | 0.6 | -0.6 | failed |
| risk | max_dd | 29679.92308 | <= | 15000 | -14679.92308 | failed |
| risk | ulcer_index | 18.235163 | <= | 10 | -8.235163 | failed |
| risk | recovery_days | 7251 | <= | 60 | -7191 | failed |

## 3. Warning Checks Table

無。

## 4. Passed Checks Table

| section | check | value | rule | threshold | margin | severity |
|---|---|---:|---|---:|---:|---|
| ranking | trade_count | 312 | >= | 30 | 282 | passed |
| oos | oos_sharpe | 1.12 | >= | 1 | 0.12 | passed |
| oos | oos_return | 0.078 | >= | 0 | 0.078 | passed |
| oos | oos_mdd | 8200 | <= | 15000 | 6800 | passed |
| forward | stability_score | 85 | >= | 60 | 25 | passed |
| forward | forward_status | good | status | not bad |  | passed |

## 5. 主要 Reject Bottleneck

- 主要瓶頸分類：`risk`。
- `max_dd` 未達標：value `29679.92308`，threshold `15000`，margin `-14679.92308`。
- `ulcer_index` 未達標：value `18.235163`，threshold `10`，margin `-8.235163`。
- `recovery_days` 未達標：value `7251`，threshold `60`，margin `-7191`。

## 6. 下一步建議

- risk 問題：是，risk checks 有 failed/warning。
- OOS 問題：目前 OOS checks 通過。
- WFO 問題：是，WFO checks 有 failed/warning。
- forward 問題：目前 forward checks 通過。
- generator / threshold：建議先調整 generator 的風險與穩健性方向，不建議先放寬 decision threshold。
