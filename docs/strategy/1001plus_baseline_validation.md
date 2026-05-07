# 1001plus Baseline Validation

## 1. 1001plus 策略定位

`1001plus` 是 mqquant 後續策略研究的正式 baseline 候選，用來取代 legacy 0313 / 0313plus 參考策略在研究主線中的位置。

定位如下：

- 以台指期 1 分 K 日當沖為主要研究場景
- 作為未來 challenger / strategy generator 的比較基準
- 只負責產生標準 `TradeRecord`
- 不接券商、不下單、不接 XQ API
- 不直接搬移 legacy 01-01 / 01-01-01 架構

目前實作位置：

- `v2/src/mqre_v2/strategy/strategy_1001plus.py`
- `v2/src/mqre_v2/strategy/__init__.py`

可執行入口：

- `python -m mqre_v2.cli.backtest_m1 --strategy 1001plus`
- `python -m mqre_v2.cli.backtest_m1_to_latest --strategy 1001plus`
- `python -m mqre_v2.cli.run_l1_l4_pipeline --strategy 1001plus`

## 2. 遵守 XS V2 規範檢查

`1001plus` baseline 目前已按照 XS V2 最高規範建立防 look-ahead 的最小策略核心。

已檢查項目：

- 進場判斷只使用前一根或更早資料
- 不使用當根 Close / High / Low 作為進場判斷
- 進場價格固定使用當根 Open
- 出場優先於進場
- 同一根 Bar 不允許同時出場又重新進場
- 單次只持有一筆部位
- 不隔夜，換日或強制收盤時間會平倉
- ATR 在進場時凍結為 `entry_atr`
- Donchian 突破使用已完成資料確認
- EMA / RSI / ATR / VWAP 皆在 Bar 完成後才更新

對應測試：

- `test_1001plus_enters_and_exits_at_current_open`
- `test_1001plus_does_not_use_current_high_low_close_for_entry`
- `test_1001plus_freezes_entry_atr_for_exit`
- `test_1001plus_short_entry_uses_anchored_previous_bar`
- `test_1001plus_single_bar_single_action_on_force_exit`

測試檔案：

- `v2/tests/strategy/test_strategy_1001plus.py`

## 3. Backtest 驗證結果

驗證日期：2026-05-07

使用指令：

```bash
python -m mqre_v2.cli.backtest_m1_to_latest --m1-path M1.txt --strategy-name 1001plus_baseline --strategy 1001plus
```

驗證摘要：

- M1 bars 筆數：456,328
- 產生交易筆數：13,766
- 原始點數損益合計：7,491.0
- 輸出交易紀錄：`runs/latest/txt/1001plus_baseline.txt`

說明：

- 此結果代表 baseline 已可從 M1 行情資料產生標準 Trade TXT
- 排名、成本、WFO、detail artifacts 仍由既有 v2 pipeline 接續處理
- 此數值不代表實盤績效，也不構成交易建議

完整測試結果：

```text
python -m pytest -q
282 passed
```

## 4. Artifact / Dashboard 驗證結果

驗證流程：

```bash
python -m mqre_v2.cli.run_latest_pipeline
```

pipeline 驗證摘要：

- artifact 輸出成功
- `runs/latest/reports/ranking.json` 已產生
- `runs/latest/reports/details/*.json` 已產生
- detail JSON 數量：17
- valid txt 策略數量：17

Dashboard 本機 HTTP 驗證：

- `/dashboard/`：HTTP 200
- `/dashboard/app.js`：HTTP 200
- `/dashboard/styles.css`：HTTP 200
- `/runs/latest/ranking.json`：HTTP 200
- `/runs/latest/strategy_detail.json`：HTTP 200
- `/runs/latest/decision_audit.json`：HTTP 200
- `/runs/latest/forward_report.json`：HTTP 200

JavaScript 語法檢查：

```bash
node --check dashboard/app.js
```

結果：通過。

## 5. 已知限制

目前 `1001plus` baseline 仍是第一版可執行策略核心，限制如下：

- 尚未完成正式參數校準
- 尚未完成 baseline vs challenger 長期比較
- 尚未完成跨年份 / 多 regime 穩健性標記
- 尚未接入更完整的 1001plus XS 原始策略語義
- 目前回測仍是 Python baseline 實作，不是 XQ / XS 實盤環境
- 成本模型與壓力測試由既有 pipeline 負責，strategy 本身只輸出 raw `TradeRecord`
- 不包含券商 API、下單、部位同步、風控執行或交易監控

保留原則：

- 0313 / 0313plus 只保留為 deprecated reference
- legacy 01-01 / 01-01-01 只作為流程與 UX 參考
- 不得把 legacy Streamlit / bundle / mq01 架構整包搬入 v2

## 6. 下一步 Challenger / Strategy Generator 規劃

下一階段建議：

1. 建立 `1001plus_baseline` 固定參數版本，作為 immutable comparison baseline
2. 建立 challenger 參數空間，但所有候選都必須與 baseline 對比
3. 將 strategy generator 產生的策略族群改為 challenger，而不是取代 baseline
4. 加強 WFO / OOS / cost stress / forward test 的 baseline vs challenger 報告
5. 將 1001plus detail artifact 固定輸出給 dashboard
6. 建立 promotion recommendation 時，要求 challenger 同時通過：
   - WFO pass rate
   - OOS Sharpe
   - cost stress
   - forward test
   - decision audit
7. 只有人工確認後，challenger 才能進入 Strategy Registry

主線流程：

```text
M1 行情
-> 1001plus baseline backtest
-> Trade TXT
-> Run Pipeline
-> Artifacts
-> Dashboard
-> Decision Audit
-> Forward Test
-> Challenger Promotion Review
```

重要結論：

`1001plus` 是後續正式策略研究 baseline；strategy generator 與 challenger 系統只能在此 baseline 之上做比較與升級建議，不可再回到 0313 / 0313plus 作為策略核心。
