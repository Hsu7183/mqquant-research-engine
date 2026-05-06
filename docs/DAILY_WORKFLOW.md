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

## 成本模型

`run_all_pipeline.cmd` 與 `run_all_pipeline.ps1` 預設使用：

- 單邊滑點：2 點
- 期交稅率：0.00002
- 每點價值：50 元
- 單邊手續費：0 元，可用 CLI `--fee-money` 調整
- 口數：1

排行榜、KPI、週損益與資產曲線皆採扣成本後績效。1 分 K 短線策略必須檢查成本壓力測試，不能只看未扣成本毛損益。

## 效能建議

策略搜尋支援多核心、進度 log 與快速資料切片。

```powershell
# debug
python -m mqre_v2.cli.run_strategy_search --m1-path M1.txt --num-strategies 5 --workers 1 --sample-bars 50000 --start-date 2020-01-01 --end-date 2026-12-31

# 小測
python -m mqre_v2.cli.run_strategy_search --m1-path M1.txt --num-strategies 20 --workers 2 --start-date 2020-01-01 --end-date 2026-12-31

# 正式
python -m mqre_v2.cli.run_strategy_search --m1-path M1.txt --num-strategies 300 --workers 0 --start-date 2020-01-01 --end-date 2026-12-31
```

- `--workers 0`：自動使用 `cpu_count - 1`
- `--sample-bars`：只取最後 N 根 M1 做快速測試
- `--dry-run`：只檢查 generator
- `--progress-every`：控制進度輸出頻率

若電腦卡住：

```powershell
Stop-Process -Name python -Force
```
