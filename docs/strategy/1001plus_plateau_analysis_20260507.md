# 1001plus Plateau Analysis

## Run Scope

- source: `runs/latest/ranking.json`
- total ranking rows: `300`
- analyzed rows: `30`
- selection rule: Top 20 or score top 10%, whichever is larger
- analyzed score range: `3.5179` ~ `4.5725`

## A. Top20 Table

| rank | strategy_id | score | sharpe | max_drawdown | trade_count |
|---:|---|---:|---:|---:|---:|
| 1 | `1001plus_ES7_EL31_RL64_RS30_AS1p3_AT4p1_D48_VW0` | 4.5725 | 0.559132 | 3018.7901 | 312 |
| 2 | `1001plus_ES9_EL38_RL64_RS31_AS1p9_AT4p6_D49_VW1` | 4.5704 | 0.596839 | 3397.9633 | 324 |
| 3 | `1001plus_ES4_EL38_RL68_RS30_AS2p7_AT4p9_D17_VW1` | 4.5649 | 0.616133 | 3596.4625 | 336 |
| 4 | `1001plus_ES10_EL44_RL70_RS30_AS1_AT3p5_D17_VW0` | 4.384 | 0.561636 | 3232.3666 | 348 |
| 5 | `1001plus_ES8_EL13_RL67_RS30_AS1p6_AT4p2_D46_VW0` | 4.357 | 0.575291 | 3395.8804 | 360 |
| 6 | `1001plus_ES9_EL24_RL70_RS30_AS1p8_AT4p5_D34_VW0` | 4.3017 | 0.587461 | 3572.9209 | 372 |
| 7 | `1001plus_ES4_EL49_RL66_RS32_AS2p4_AT5_D37_VW1` | 4.184 | 0.615312 | 3969.1676 | 384 |
| 8 | `1001plus_ES10_EL25_RL63_RS31_AS2p3_AT3p2_D45_VW1` | 4.1378 | 0.589674 | 3758.9544 | 396 |
| 9 | `1001plus_ES3_EL38_RL69_RS30_AS1p3_AT4p8_D19_VW0` | 4.1063 | 0.573548 | 3629.1596 | 408 |
| 10 | `1001plus_ES5_EL24_RL69_RS31_AS1p9_AT2p8_D45_VW0` | 4.0588 | 0.575649 | 3697.6778 | 420 |
| 11 | `1001plus_ES7_EL26_RL70_RS32_AS2p1_AT2p5_D15_VW1` | 4.0587 | 0.588172 | 3823.0108 | 432 |
| 12 | `1001plus_ES7_EL24_RL63_RS34_AS3_AT3p6_D50_VW1` | 4.0506 | 0.59 | 3849.3931 | 444 |
| 13 | `1001plus_ES4_EL38_RL69_RS32_AS2p1_AT3p2_D46_VW1` | 4.0047 | 0.606128 | 4056.5649 | 456 |
| 14 | `1001plus_ES7_EL26_RL63_RS30_AS2_AT2p8_D43_VW1` | 3.9715 | 0.565346 | 3681.9751 | 468 |
| 15 | `1001plus_ES8_EL39_RL68_RS34_AS2p1_AT4p2_D36_VW1` | 3.8747 | 0.592628 | 4051.5924 | 480 |
| 16 | `1001plus_ES3_EL19_RL66_RS32_AS1p7_AT4p2_D35_VW1` | 3.8699 | 0.584434 | 3974.3931 | 492 |
| 17 | `1001plus_ES8_EL32_RL69_RS31_AS2p3_AT3p6_D16_VW1` | 3.8214 | 0.604487 | 4223.5159 | 504 |
| 18 | `1001plus_ES7_EL49_RL56_RS32_AS2p3_AT3p1_D50_VW0` | 3.8153 | 0.577369 | 3958.3661 | 516 |
| 19 | `1001plus_ES8_EL40_RL69_RS34_AS2p5_AT3p2_D34_VW1` | 3.8021 | 0.599312 | 4190.9807 | 528 |
| 20 | `1001plus_ES8_EL41_RL67_RS31_AS2p5_AT3p1_D20_VW0` | 3.7421 | 0.592109 | 4179.0424 | 540 |

## B. Parameter Distribution

| param | mean | std | min | max | suggested_range | stable |
|---|---:|---:|---:|---:|---|---|
| ES | 6.066667 | 2.308439 | 2 | 10 | 4~8 | no |
| EL | 33.1 | 8.833082 | 13 | 49 | 25~39 | no |
| RL | 66.833333 | 3.034066 | 56 | 70 | 65~69 | no |
| RS | 32.166667 | 2.464188 | 30 | 40 | 30~34 | no |
| AS | 2.086667 | 0.472393 | 1 | 3 | 1.725~2.475 | yes |
| AT | 3.72 | 0.861162 | 2.1 | 5 | 3.1~4.425 | no |
| D | 33.333333 | 13.11064 | 11 | 50 | 19~45 | no |
| VW | 0.6 | 0.489898 | 0 | 1 | 1 | no |

## C. Plateau 判斷

- 是否存在穩定區: `no`
- 穩定參數: `AS`
- 發散參數: `ES, EL, RL, RS, AT, D, VW`

## D. Interpretation

- `ES` 仍偏發散，Top 區域尚未收斂，不宜直接固定。
- `EL` 仍偏發散，Top 區域尚未收斂，不宜直接固定。
- `RL` 仍偏發散，Top 區域尚未收斂，不宜直接固定。
- `RS` 仍偏發散，Top 區域尚未收斂，不宜直接固定。
- `AS` 出現相對集中區間，建議先觀察 `1.725~2.475`。
- `AT` 仍偏發散，Top 區域尚未收斂，不宜直接固定。
- `D` 仍偏發散，Top 區域尚未收斂，不宜直接固定。
- `VW` 仍偏發散，Top 區域尚未收斂，不宜直接固定。
- 綜合判斷：尚未形成足夠穩定 plateau，Top 策略更像單點排序結果。

## E. 建議

- 暫不建議擴到 1000 run；目前 plateau 不明顯。
- 先檢查 generator 範圍是否過寬，並分析 rejection checks 中最嚴重的失敗項。
- 建議先做分桶分析，例如 VW=0 / VW=1、短 EMA / 長 EMA 區間，再決定下一輪搜尋方向。
- baseline 不應被替換，Top challenger 只作為下一輪探索線索。
