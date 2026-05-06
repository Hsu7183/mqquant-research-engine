# Daily Workflow

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

## 一鍵更新 Dashboard

只需執行：

```cmd
run_all_pipeline.cmd
```

或使用 PowerShell：

```powershell
.\run_all_pipeline.ps1
```

系統會自動：

- 回測 M1
- 產生交易紀錄
- 計算 KPI
- 更新 JSON
- push 到 GitHub
- Dashboard 自動更新

注意：此流程仍只做研究、報表與 dashboard 更新，不接券商、不接 XQ API、不下單。
