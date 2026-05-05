# mqquant 策略治理系統 v1

## 【版本資訊】

- version: v1.0
- date: 2026-05-06
- commit: d1b30b7801f52b3588c6daee8b59a6c612dd6334

## 【功能範圍】

Level 1：Auto Research Pipeline
Level 2：JSON 報表輸出
Level 3：Forward Test Tracking
Level 4：Strategy Registry（策略升級治理）

## 【GUI 模式】

- 單一策略 WFO
- Baseline vs Challenger
- Optimizer
- 批量 TXT 排名
- Auto Research Pipeline
- Forward Test 管理
- Forward Evaluation
- Strategy Registry

## 【已完成能力】

- XS → TXT → WFO → Ranking
- 策略自動評分（score）
- Top N 自動挑選
- candidate → forward_testing → promoted / rejected
- promoted → strategy registry（active）

## 【未包含（重要）】

- 不接券商 API
- 不接 XQ API
- 不會自動下單
- 不會自動回測 XS
- 不包含風控 / 交易執行

## 【風險提醒】

- WFO ≠ 未來保證
- 必須經過 forward test
- 不可直接用於實盤交易
