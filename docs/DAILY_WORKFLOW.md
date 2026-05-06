# Daily Workflow

## 一鍵 L1-L4 更新 Dashboard

只需執行：

```cmd
run_all_pipeline.cmd
```

或使用 PowerShell：

```powershell
.\run_all_pipeline.ps1
```

系統會自動完成：

```text
M1 行情資料
-> 策略生成器
-> 多策略回測
-> Trade TXT
-> Run Latest Pipeline
-> Ranking JSON
-> Strategy Detail JSON
-> Auto Research
-> Forward Log
-> Auto Promotion Recommendation
-> Decision Audit Log
-> Dashboard
```

## 手動研究流程

1. 用 parameter_grid 產生 XS
2. 在 XQ 手動回測
3. 匯出 TXT
4. GUI 執行批量 TXT 排名
5. 查看 Top 10
6. 執行 Auto Research Pipeline
7. Top1 加入 Forward Test candidate
8. Forward Evaluation
9. promoted 策略匯入 Strategy Registry
10. 人工檢查後才可考慮後續實盤

## 邊界

- 目前不接券商
- 目前不接 XQ API
- 不自動下單
- 系統不是固定 0313 或 1001plus+
- 1001plus+ 只是技術元件參考
- SimpleM1Strategy 是 MVP 策略邏輯
- 下一步才會替換為正式 0313 / 1001 / 0807 策略邏輯
