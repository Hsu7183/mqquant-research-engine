# WFO Specification

## 1. WFO 目的

WFO（Walk Forward Optimization）是 mqquant 策略研究系統的主要驗證層，用來避免 single OOS 的運氣成分，檢查策略是否能跨市場區間穩定，並作為 baseline vs challenger 的主要比較流程。

## 2. 資料限制

目前主要研究資料為近 6 年台指期 1 分 K 資料。

本系統不假設有無限長歷史資料，因此 WFO 設計必須適合有限樣本。

每次切割都必須保留 gap / purge 區間，避免 train 與 test 之間產生資料洩漏。

## 3. 建議切割方式

預設切割方式：

- Train：36 個月
- Gap：1 個月
- Test：6 個月
- Step：6 個月

不得只使用單一 OOS 結果決定策略好壞。

## 4. 每輪流程

每一輪 WFO 必須按照以下流程：

1. 在 Train 區間執行 optimizer
2. 根據 Train 結果選出 top candidates
3. 將 candidates 套用到 Test 區間
4. 紀錄每一輪 OOS 結果
5. 不允許根據 Test 結果回頭調整參數

## 5. 每輪輸出欄位

每一輪 WFO 結果至少包含：

- round_id
- train_start
- train_end
- gap_start
- gap_end
- test_start
- test_end
- strategy_name
- params_hash
- train_net_profit
- train_mdd
- train_pf
- train_trade_count
- test_net_profit
- test_mdd
- test_pf
- test_trade_count
- pass_flag
- fail_reason

## 6. 通過條件

WFO 通過條件：

1. 多數 WFO round 必須通過
2. OOS 不可只靠單一大獲利 round
3. test_trade_count 不可過低
4. test_mdd 不可失控
5. slip stress 下仍需合理
6. baseline 與 challenger 必須使用同樣流程比較

## 7. 與後續模組關係

WFO 結果將提供給：

- PBO 近似評估
- DSR 近似評估
- Forward Test 啟動判斷
- baseline vs challenger 決策系統

WFO 不取代實盤 forward test。

## 8. 明確禁止事項

禁止：

1. 直接用全部資料最佳化後宣稱策略有效
2. 看完 OOS 結果後再回頭調參
3. 只挑最好的一輪 WFO 當成完整結果
4. 未經治理流程直接修改 baseline 定義
