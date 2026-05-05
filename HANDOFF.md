# Codex Handoff Instructions

當任何 Codex（單機 / 雲端）接手本專案時，請先閱讀：

1. BASELINE.md
2. 本文件
3. docs/WFO_SPEC.md
4. docs/WFO_MODULES.md
5. docs/CURRENT_STATUS.md
6. docs/GUI_USAGE.md

並遵守：

- 不得修改 01-01-01
- 所有新策略必須建立於 projects/*
- 所有驗證需包含：
  - OOS
  - WFO
  - Baseline 對比

## System Flow

Step1：Optimizer
Step2：Single OOS
Step3：Walk Forward
Step4：Validation（MDD / Sharpe / PF）
Step5：Forward Test（baseline vs challenger）

此文件為跨平台接續工作的唯一入口。

## Completed Core Modules

目前已完成模組：

- XS TXT Parser
- WFO Window Generator
- WFO Result Schema
- WFO Pass/Fail Gate
- WFO Runner Skeleton
- Optimizer Adapter Skeleton
- WFO TXT Adapter
- WFO TXT CLI
- TXT WFO Pipeline
- Forward Test Tracking
- Forward Test 管理 GUI
- Baseline vs Challenger Decision
- WFO JSON Report Exporter
- Auto Research Pipeline

## Level 1～4 Mainline

Level 1～4 是目前主線，僅涵蓋研究、報表、觀察與決策基礎。

最新流程：

```text
TXT 資料夾
-> WFO Pipeline
-> Ranking JSON
-> TopN
-> Forward candidate
```

注意：

- 這是全自動研究，不是全自動交易
- 目前不接券商
- 目前不接 XQ API
- 目前不會自動下單

## GUI

GUI 已有 6 個模式：

1. 單一策略 WFO
2. Baseline vs Challenger
3. Optimizer
4. 批量 TXT 排名
5. Forward Test 管理
6. Auto Research Pipeline

啟動方式：

```powershell
.\run_gui.ps1
```

或：

```cmd
run_gui.cmd
```

## Test Status

- `python -m pytest -q` = 137 passed
