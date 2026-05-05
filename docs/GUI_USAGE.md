# GUI Usage Guide

## 如何啟動 GUI

在 repo root 執行其中一個指令：

```powershell
.\run_gui.ps1
```

或：

```cmd
run_gui.cmd
```

兩個啟動檔都會將 `PYTHONPATH` 設為目前 repo 的 `v2/src`，並執行：

```powershell
python -m streamlit run v2/src/mqre_v2/gui/wfo_app.py
```

## GUI 模式

1. 單一策略 WFO

   讀取單一 TXT 檔，設定 WFO window 與 gate 參數，執行 WFO，查看 summary、round results、圖表與 JSON。

2. Baseline vs Challenger

   同時讀取 baseline TXT 與 challenger TXT，各自執行 WFO，使用 baseline vs challenger decision 模組比較是否升級。

3. Optimizer

   提供簡化 optimizer、parameter grid 預覽，以及 XS 批次產生入口。此模式只產生 XS 或整理參數空間，不會連接 XQ 或自動回測。

4. 批量 TXT 排名

   掃描資料夾內 TXT 檔，逐一執行 TXT -> WFO -> ranking pipeline，輸出 Top 10 與完整 JSON，並可將 Top 1 加入 Forward Test 觀察名單。

5. Forward Test 管理

   讀取 forward test CSV log，更新策略狀態：

   - `candidate`
   - `forward_testing`
   - `promoted`
   - `rejected`

## 建議實戰流程

1. 用 `parameter_grid` 產生 XS。
2. 在 XQ 手動回測輸出 TXT。
3. 用批量 TXT 排名跑 WFO pipeline。
4. 把 Top 1 加入 Forward Test。
5. 用 Forward Test 管理更新狀態。

## 注意事項

- 目前不接券商。
- 目前不接 XQ API。
- 目前不會自動下單。
- TXT 格式必須符合標準 TradeRecord 欄位契約。
