# 1001plus Risk-Constrained Challenger 300 Run - 2026-05-07

## 1. Run metadata

- job_id: `20260507133447_ac0490cd`
- generator: `1001plus`
- generator_mode: `risk_constrained`
- num_strategies: `300`
- seed: `42`
- completed: `300/300`
- promotion_decision: `reject`

## 2. Top 10 ranking

| rank | strategy_id | score | sharpe | max_drawdown | trade_count |
|---:|---|---:|---:|---:|---:|
| 1 | `1001plus_ES7_EL40_RL66_RS30_AS1p4_AT3p4_D50_VW1` | 5.1245 | 0.592870 | 2804.1831 | 312 |
| 2 | `1001plus_ES6_EL43_RL67_RS30_AS1p5_AT3p2_D37_VW1` | 4.8781 | 0.603500 | 3156.9345 | 324 |
| 3 | `1001plus_ES7_EL24_RL67_RS30_AS1_AT2p9_D36_VW1` | 4.8706 | 0.571915 | 2848.5796 | 336 |
| 4 | `1001plus_ES10_EL40_RL67_RS30_AS1p3_AT2p9_D45_VW1` | 4.7834 | 0.573897 | 2955.5803 | 348 |
| 5 | `1001plus_ES9_EL31_RL67_RS30_AS1p1_AT3p6_D38_VW0` | 4.6323 | 0.571433 | 3082.0048 | 360 |
| 6 | `1001plus_ES7_EL22_RL70_RS30_AS1p1_AT3p5_D45_VW1` | 4.6160 | 0.573091 | 3114.8817 | 372 |
| 7 | `1001plus_ES4_EL29_RL67_RS32_AS1p8_AT3p2_D46_VW1` | 4.5650 | 0.606427 | 3499.2660 | 384 |
| 8 | `1001plus_ES6_EL38_RL65_RS31_AS1p6_AT3p2_D43_VW1` | 4.5522 | 0.596061 | 3408.4047 | 396 |
| 9 | `1001plus_ES8_EL30_RL66_RS33_AS1p1_AT2p7_D50_VW1` | 4.5088 | 0.592498 | 3416.1986 | 408 |
| 10 | `1001plus_ES6_EL27_RL66_RS30_AS1p5_AT2p5_D47_VW1` | 4.4956 | 0.575429 | 3258.7180 | 420 |

## 3. Risk comparison vs default 300-run

| metric | default 300-run | risk_constrained 300-run | result |
|---|---:|---:|---|
| max_dd | 29679.92308 | 24368.38260 | improved |
| ulcer_index | 18.235163 | 15.495345 | improved |
| recovery_days | 7251 | 6836 | improved |

## 4. Interpretation

The `risk_constrained` generator improved the major risk metrics compared with the default 300-run. Maximum drawdown, Ulcer Index, and recovery days all decreased.

However, the top challenger still failed the promotion decision. The run should be interpreted as a risk improvement, not a baseline upgrade.

Key conclusions:

- `risk_constrained` improved risk, but not enough to pass promotion thresholds.
- WFO remains a major rejection factor.
- The current baseline should not be replaced.
- Decision thresholds should not be relaxed to force an upgrade.

## 5. Next steps

1. Break down WFO results by round and identify which windows fail.
2. Inspect why WFO `pass_rate` and `stability_score` remain weak.
3. Compare the Top 10 shared parameter characteristics against failed candidates.
4. Consider regime bucket analysis before expanding the generator again.
5. Decide whether to build a second version of `risk_constrained` or add regime-aware candidate selection.
