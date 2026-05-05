# WFO Modules

本文記錄目前 `v2/src/mqre_v2/validation/wfo/` 內的 Walk Forward Optimization 基礎模組。

## windows.py

- `WfoWindow`
  - 單一 WFO round 的時間切割資料結構
  - 包含 train / gap / test 區間
- `generate_wfo_windows`
  - 依照 WFO 規格產生完整 window list
  - 預設切割為 Train 36 個月、Gap 1 個月、Test 6 個月、Step 6 個月
  - 只保留 `test_end <= end_date` 的完整 round

## results.py

- `WfoRoundResult`
  - 單一 WFO round 的輸出 schema
  - 欄位符合 `docs/WFO_SPEC.md` 的每輪輸出欄位
- `WfoSummary`
  - 多輪 WFO 結果的彙總 schema
  - 包含 round 數、通過率、測試段總損益、MDD、PF、交易數
- `summarize_wfo_results`
  - 將多個 `WfoRoundResult` 彙總為 `WfoSummary`
  - 空集合會 raise `ValueError`

## gates.py

- `WfoGateConfig`
  - WFO pass/fail gate 的設定
  - 包含最低交易數、最大 MDD、最低 PF、最低通過率與總測試損益要求
- `evaluate_wfo_round`
  - 對單一 `WfoRoundResult` 套用 pass/fail gate
  - 使用新物件回傳，不原地修改結果
- `evaluate_wfo_summary`
  - 對 `WfoSummary` 套用整體 pass/fail gate
  - 回傳 `(passed, fail_reason)`

## runner.py

- `WfoRunResult`
  - WFO runner 的總輸出
  - 包含 windows、round_results、summary、passed、fail_reason
- `run_wfo`
  - WFO 流程串接骨架
  - 目前不實作 optimizer，只呼叫外部傳入的 `optimize_fn` 與 `evaluate_fn`
  - 不吞掉 `optimize_fn` / `evaluate_fn` 的例外

## Data Flow

```text
generate_wfo_windows
-> optimize_fn
-> evaluate_fn
-> evaluate_wfo_round
-> summarize_wfo_results
-> evaluate_wfo_summary
-> WfoRunResult
```
