# Current Status

Date: 2026-05-06

## Version

- version: v2 standard
- system type: strategy governance system, not execution system
- cleanup status: standard repository layout finalized

## Standard Layout

The repository is organized around:

- `.github/`
- `configs/`
- `dashboard/`
- `docs/`
- `runs/latest/reports/`
- `templates/`
- `v2/src/mqre_v2/`
- `v2/tests/`

## Removed Legacy Bundle

`01-01-01/` was removed from the standard repo.

Reason:

- It was a legacy workbench and data package.
- Formal v2 code, tests, dashboard, and GitHub Actions no longer import or execute it.
- M1 TXT parsing is now independent in `mqre_v2.io.m1_parser`.
- Dashboard data is served from `runs/latest/reports/`.

## Completed Modules

- Trade TXT Parser
- M1 OHLC TXT Parser
- M1 Backtest MVP
- Intraday Futures Strategy Generator
- Full Futures Trading Cost Model
- L1-L4 Pipeline CLI
- WFO Window Generator
- WFO Result Schema
- WFO Pass/Fail Gate
- WFO Runner Skeleton
- Optimizer Adapter Skeleton
- XS TXT WFO Adapter
- WFO TXT CLI
- TXT WFO Pipeline
- Run Manifest System
- Run TXT Validation
- Run -> WFO Pipeline
- Strategy Detail Reports
- Forward Test Tracking
- Forward Test Management GUI
- Baseline vs Challenger Decision
- WFO JSON Report Exporter
- Auto Research Pipeline
- Auto Research CLI
- Forward Evaluation
- Strategy Registry
- Promotion Recommendation Report
- Decision Audit Log
- Auto Promotion Pipeline
- Streamlit GUI
- Static Dashboard

## Latest Core Flow

Formal L1-L4 flow:

```text
M1
-> Strategy Generator
-> Multi-strategy Backtest
-> Trade TXT
-> Ranking
-> Detail
-> Forward
-> Auto Promotion
-> Audit
-> Dashboard
```

Detailed flow:

```text
M1 行情資料
-> Strategy Generator
-> 多策略回測
-> TradeRecord / Trade TXT
-> Run Latest Pipeline
-> Ranking JSON
-> Strategy Detail JSON
-> Auto Research
-> Forward Log
-> Auto Promotion Recommendation
-> Decision Audit Log
-> Dashboard
```

## GUI Modes

1. 單一策略 WFO
2. Baseline vs Challenger
3. Optimizer
4. 批量 TXT 排名
5. Forward Test 管理
6. Auto Research Pipeline
7. Forward Evaluation
8. Strategy Registry
9. Promotion Recommendation
10. Auto Promotion Pipeline

## Boundaries

- 不接券商
- 不接 XQ API
- 不下單
- 不自動切換實盤策略
- promoted / active strategy registry 只代表治理狀態，不代表實盤執行
- 系統不是固定 0313 或 1001plus+
- 1001plus+ 只是技術元件參考
- SimpleM1Strategy 是 MVP 策略邏輯
- 下一步才會替換為正式 0313 / 1001 / 0807 策略邏輯

## Cost Model

Ranking、WFO、weekly_pnl、equity_curve、strategy_detail KPI 與 dashboard 目前皆採扣成本後績效。

預設成本：

- 小台每點價值 `point_value = 50`
- 單邊滑點 `slippage_points_per_side = 2`
- 期交稅率 `tax_rate = 0.00002`
- 單邊手續費 `fee_money_per_side = 0`，可用 `--fee-money` 指定
- 口數 `qty = 1`

短線 1 分 K 策略必須檢查成本壓力測試。detail JSON 會輸出 raw pnl、net pnl、滑點、手續費、期交稅、總成本與不同滑點情境的壓力測試結果。

## Next Direction

1. Keep `runs/latest/reports/` updated for dashboard.
2. Replace the simple M1 MVP with formal 0313 / 1001 / 0807 strategy adapters.
3. Continue v2-v4 governance/reporting improvements.
4. Keep v5 execution layer out of scope.
