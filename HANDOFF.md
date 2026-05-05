# Codex Handoff Instructions

當任何 Codex（單機 / 雲端）接手本專案時，請先閱讀：

1. BASELINE.md
2. 本文件
3. docs/WFO_SPEC.md
4. docs/WFO_MODULES.md
5. docs/CURRENT_STATUS.md

並遵守：

- 不得修改 01-01-01
- 所有新策略必須建立於 projects/*
- 所有驗證需包含：
  - OOS
  - WFO
  - Baseline 對比

系統流程：

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
- Baseline vs Challenger Decision
- WFO JSON Report Exporter

目前 WFO 核心檔案：

- docs/WFO_SPEC.md
- docs/WFO_MODULES.md
- docs/CURRENT_STATUS.md
- v2/src/mqre_v2/io/txt_parser.py
- v2/src/mqre_v2/validation/wfo/windows.py
- v2/src/mqre_v2/validation/wfo/results.py
- v2/src/mqre_v2/validation/wfo/gates.py
- v2/src/mqre_v2/validation/wfo/runner.py
- v2/src/mqre_v2/validation/wfo/adapters.py
- v2/src/mqre_v2/validation/wfo/txt_adapter.py
- v2/src/mqre_v2/cli/wfo_txt.py
- v2/src/mqre_v2/validation/decision.py
- v2/src/mqre_v2/reporting/wfo_report.py

目前測試狀態：

- python -m pytest -q 已通過 80 passed

下一步建議：

- 將 CLI 加入 README 使用方式
- 建立 baseline/challenger 雙 TXT 比較 CLI
- 建立 GitHub Actions 自動產 report
- 接 0313 / 1001 / 0807 真實 TXT

## GUI Launch And Current Status

GUI 已有 5 個模式：

1. 單一策略 WFO
2. Baseline vs Challenger
3. Optimizer
4. 批量 TXT 排名
5. Forward Test 管理

啟動方式：

```powershell
.\run_gui.ps1
```

或：

```cmd
run_gui.cmd
```

最新測試狀態：

- `python -m pytest -q` = 129 passed

最新 commit：

- `32dcb0eee788691fe37b6a7f032d819153f144f6`
