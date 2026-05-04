# v2 OOS Runner（Phase 2 最小可用版）

## 目的

本階段只做 **既有交易紀錄** 的 OOS 統計評估，不產生任何策略訊號或交易。

- ✅ 只評估 pre-generated trades
- ❌ 不做策略生成器
- ❌ 不做 optimizer
- ❌ 不做 WFO runner
- ❌ 不做 PBO/DSR
- ❌ 不做 Forward Test
- ❌ 不做 Baseline/Challenger

## 輸入與輸出

- 輸入：`TradeRecord` 清單或 `pandas.DataFrame`
- 核心函式：`mqre_v2.validation.oos.runner.evaluate_oos_trades`
- 報告輸出：`mqre_v2.reporting.writers.write_oos_result_json` 會寫出 `oos_result.json`

## 評估欄位

- `total_trades`
- `win_rate`
- `gross_pnl_points`
- `net_pnl_points`
- `avg_trade_points`
- `max_drawdown_points`
- `profit_factor`
- `long_trades`
- `short_trades`

## 測試

在 repo root 執行：

```bash
PYTHONPATH=v2/src pytest -q v2/tests/test_oos_runner.py
```
