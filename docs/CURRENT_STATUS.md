# Current WFO System Status

## Version

- version: v1.0 (stable)
- latest commit: d1b30b7801f52b3588c6daee8b59a6c612dd6334
- tests: 200 passed
- 系統定位：策略治理系統（非交易系統）
- version: v1.0 stable
- system type: strategy governance system, not execution system
- next direction: v2～v4 roadmap

## Test Status

- `python -m pytest -q` = 200 passed

## Level 1～4 Mainline

Level 1～4 是目前 mqquant 的主線，範圍是研究、報表、觀察與決策基礎。

目前明確不做：

- 不接券商
- 不接 XQ API
- 不自動下單
- 不做自動交易

## Latest Core Flow

```text
TXT 資料夾
-> WFO Pipeline
-> Ranking JSON
-> TopN
-> Forward candidate
-> Forward Evaluation
-> Strategy Registry active
```

## Completed Modules

- XS TXT Parser
- WFO Window Generator
- WFO Result Schema
- WFO Pass/Fail Gate
- WFO Runner Skeleton
- Optimizer Adapter Skeleton
- XS TXT WFO Adapter
- WFO TXT CLI
- TXT WFO Pipeline
- Forward Test Tracking
- Forward Test 管理 GUI
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

## Level 4 Support

- Forward Evaluation 可將 `forward_testing` 策略評估為 `promoted` / `rejected`。
- Strategy Registry 可將 `promoted` 策略登錄為 `active`。
- Promotion Recommendation 可根據 ranking report 產生升級建議。
- Decision Audit Log 可回溯每次 promotion decision。
- Auto Promotion Pipeline 可自動產生 recommendation + audit log，並輸出人工確認用摘要。
- `active` 只代表正式策略版本治理狀態，不代表下單或啟動交易。
- v4 Auto Decision Layer 已開始；所有建議都保留 `requires_human_review=True`。
- v4 仍不自動下單、不自動切換策略。

## Next Steps

1. 將真實 0313 / 1001 / 0807 TXT 接入 Auto Research Pipeline。
2. 建立 Level 3 決策規則與報表。
3. 建立 Level 4 forward observation review 報表。
4. 保持 01-01-01 baseline immutable。
