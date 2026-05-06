# Current Status

Date: 2026-05-06

## Version

- version: v2 standard
- system type: strategy governance system, not execution system
- cleanup status: standard repository layout finalized
- latest verified tests before this update: `219 passed`

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

M1 demo flow:

```text
M1 TXT
-> BarRecord
-> SimpleM1StrategyParams
-> TradeRecord
-> Trade TXT
-> WFO / Dashboard Pipeline
```

Research governance flow:

```text
TXT folder
-> WFO Pipeline
-> Ranking JSON
-> TopN
-> Forward candidate
-> Forward Evaluation
-> Strategy Registry active
-> Promotion Recommendation
-> Decision Audit Log
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
- M1 Backtest MVP 是簡化研究流程，不是正式 0313 / 1001 策略

## Next Direction

1. Keep `runs/latest/reports/` updated for dashboard.
2. Add real TXT exports into pipeline runs.
3. Replace the simple M1 MVP with formal 0313 / 1001 strategy adapters when ready.
4. Continue v2-v4 governance/reporting improvements.
5. Keep v5 execution layer out of scope.
