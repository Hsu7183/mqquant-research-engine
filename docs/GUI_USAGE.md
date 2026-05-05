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

6. Auto Research Pipeline

   讀取 TXT 資料夾，自動執行 TXT -> WFO Pipeline -> Ranking JSON -> TopN，並依設定將 Top 1 策略加入 Forward Test `candidate`。這是 Level 1～4 的全自動研究主線，不是全自動交易。

7. Forward Evaluation

   針對 `forward_testing` 狀態策略重新讀取最新 TXT、執行 WFO，依分數門檻自動更新為 `promoted`、`rejected` 或維持觀察中。

8. Strategy Registry

   從 Forward Log 匯入 `promoted` 策略，登錄為正式策略版本 `active`，並可手動將策略退役為 `retired`。此模式只做版本治理，不會下單。

9. Promotion Recommendation

   讀取標準化 ranking JSON，依分數、pass rate 與 MDD 門檻產生策略升級建議報告，並可寫入 Decision Audit Log。此模式只產生 recommendation 與決策歷史紀錄，不會自動下單、不會自動切換策略，且 `requires_human_review=True`。

10. Auto Promotion Pipeline

    讀取 ranking JSON，自動產生 promotion recommendation JSON，並同步寫入 Decision Audit Log。此模式提供人工確認用摘要，不會自動下單、不會自動切換實盤策略。

## 建議實戰流程

1. 用 `parameter_grid` 產生 XS。
2. 在 XQ 手動回測輸出 TXT。
3. 使用 Auto Research Pipeline 執行主線流程：TXT 資料夾 -> WFO Pipeline -> Ranking JSON -> TopN -> Forward candidate。
4. 用 Forward Test 管理將候選策略切到 `forward_testing`。
5. 用 Forward Evaluation 產生 `promoted` / `rejected` 判斷。
6. 用 Strategy Registry 將 `promoted` 策略登錄為 `active`。
7. 用 Promotion Recommendation 或 Auto Promotion Pipeline 產生升級建議報告。
8. 檢查 Decision Audit Log，確認每次 promotion decision 可回溯。
9. 視需要再用 Baseline vs Challenger 做更細的升級決策。

## 注意事項

- 目前不接券商。
- 目前不接 XQ API。
- 目前不會自動下單。
- Auto Research Pipeline 是全自動研究，不是全自動交易。
- Strategy Registry 只登錄 promoted 策略為 active，不代表啟動交易。
- Promotion Recommendation 只產生建議與 Decision Audit Log，不自動下單、不自動切換策略。
- Auto Promotion Pipeline 只自動產生 recommendation + audit log，仍需人工確認。
- Decision Audit Log 可回溯每次 promotion decision。
- Level 1～4 目前只做研究、報表、觀察與決策基礎。
- TXT 格式必須符合標準 TradeRecord 欄位契約。
