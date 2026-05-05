# Codex Handoff Instructions

當任何 Codex（單機 / 雲端）接手本專案時，請先閱讀：

1. BASELINE.md
2. 本文件

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

## WFO Current Status

目前 WFO 核心已完成：
- docs/WFO_SPEC.md
- v2/src/mqre_v2/validation/wfo/windows.py
- v2/src/mqre_v2/validation/wfo/results.py
- v2/src/mqre_v2/validation/wfo/gates.py
- v2/src/mqre_v2/validation/wfo/runner.py

目前測試狀態：
- python -m pytest -q 已通過 41 passed

下一步建議：
- 建立 optimizer adapter
- 建立 OOS evaluator adapter
- 建立 CLI / UI 入口
- 建立 baseline vs challenger report
