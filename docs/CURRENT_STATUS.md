# Current WFO System Status

## Test Status

- `python -m pytest -q` = 137 passed

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
- Streamlit GUI

## GUI Modes

1. 單一策略 WFO
2. Baseline vs Challenger
3. Optimizer
4. 批量 TXT 排名
5. Forward Test 管理
6. Auto Research Pipeline

## Next Steps

1. 將真實 0313 / 1001 / 0807 TXT 接入 Auto Research Pipeline。
2. 建立 Level 3 決策規則與報表。
3. 建立 Level 4 forward observation review 流程。
4. 保持 01-01-01 baseline immutable。
