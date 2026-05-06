# Dashboard

mqquant dashboard 使用純 HTML / JavaScript / CSS，不使用 React。

## 開啟方式

在 repo root 啟動本機靜態伺服器：

```powershell
python -m http.server 8000
```

瀏覽：

```text
http://localhost:8000/dashboard/
```

GitHub Pages 預期網址：

```text
https://hsu7183.github.io/mqquant-research-engine/dashboard/
```

## 登入門檻

預設密碼：

```text
1qazxcvbnm,./
```

Dashboard 目前有入口防護頁，登入前只顯示密碼欄與確定按鈕。登入後才顯示策略排行榜。

## 前端防護功能

目前提供的前端防護干擾包含：

- 禁止右鍵 contextmenu
- 禁止 F12
- 禁止 Ctrl+Shift+I
- 禁止 Ctrl+Shift+J
- 禁止 Ctrl+U
- 禁止 Ctrl+S
- 禁止 Ctrl+P
- 禁止選取文字
- 禁止拖曳圖片或文字
- 偵測 DevTools 開啟時，清除登入狀態並回登入畫面

注意：GitHub Pages 前端防護不是正式資安，只是基本阻擋。密碼與資料仍會存在前端程式與公開 JSON 中。

若要真正保護資料，必須使用：

- private repo
- Cloudflare Access
- Supabase Auth
- 後端登入

## Ranking 資料來源

Dashboard 目前優先讀取 GitHub raw JSON：

```text
https://raw.githubusercontent.com/Hsu7183/mqquant-research-engine/main/runs/latest/reports/ranking.json
```

若 GitHub fetch 失敗，會 fallback 到：

```text
dashboard/sample_ranking.json
```

若 GitHub 與本地 sample 都失敗，會使用 `dashboard/app.js` 內建 fallback data。

## Ranking JSON 格式

Dashboard 讀取 `docs/REPORT_SCHEMA.md` 定義的 ranking JSON，核心欄位包含：

- `run_id`
- `generated_at`
- `summary.total_strategies`
- `summary.valid_strategies`
- `top_10`
- `all_results`

`top_10` 每筆策略至少包含：

- `rank`
- `strategy_name`
- `score`
- `total_test_net_profit`
- `pass_rate`
- `max_test_mdd`
- `average_test_pf`

## Strategy Detail JSON

Run pipeline 會在下列資料夾輸出每個策略的 detail JSON：

```text
runs/{run_id}/reports/details/{strategy_name}.json
```

Dashboard 的 latest detail 讀取路徑為：

```text
https://raw.githubusercontent.com/Hsu7183/mqquant-research-engine/main/runs/latest/reports/details/{strategy_name}.json
```

結構：

```json
{
  "strategy_name": "string",
  "run_id": "string",
  "summary": {
    "score": 0.0,
    "total_test_net_profit": 0.0,
    "pass_rate": 0.0,
    "max_test_mdd": 0.0,
    "average_test_pf": 0.0
  },
  "period": {
    "start": "2024-01-01",
    "end": "2024-06-30"
  },
  "trade_stats": {
    "trade_count": 120,
    "long_count": 60,
    "short_count": 60,
    "win_count": 66,
    "loss_count": 54,
    "win_rate": 0.55,
    "total_profit": 12500.0,
    "avg_trade_pnl": 104.17,
    "avg_win": 450.0,
    "avg_loss": 318.0,
    "largest_win": 2300.0,
    "largest_loss": 1500.0,
    "gross_profit": 29700.0,
    "gross_loss": 17200.0,
    "profit_factor": 1.73,
    "payoff_ratio": 1.42,
    "max_drawdown": 8300.0,
    "underwater_weeks": 6,
    "max_losing_streak": 3
  },
  "equity_curve": [
    { "week": "2024-W01", "equity": 100500.0 }
  ],
  "weekly_pnl": [
    { "week": "2024-W01", "pnl": 500.0 }
  ],
  "kpi": {
    "score": 0.0,
    "profit": 0.0,
    "pass_rate": 0.0,
    "mdd": 0.0,
    "pf": 0.0
  }
}
```

## Detail Page 行為

使用者在排行榜點擊「查看詳情」時：

1. Dashboard 先嘗試讀取 `runs/latest/reports/details/{strategy_name}.json`
2. 若 detail JSON 存在，詳情頁顯示：
   - 策略摘要卡
   - 每週資產曲線
   - 每週損益
   - KPI 表與 Strong / Watch / Weak 評等
3. 若 detail JSON 不存在或讀取失敗，fallback 使用 ranking row：
   - 顯示 ranking report 可用 KPI
   - 顯示「尚未讀取到 strategy_detail.json，目前使用 ranking 摘要資料」
4. 若 detail JSON 有讀取到但 `equity_curve` / `weekly_pnl` 為空：
   - 顯示「detail JSON 已讀取，但 weekly 資料為空，請重新執行 Run Pipeline」
   - 不建立空白 Chart.js 圖表

KPI 表目前包含：

- 測試期間
- 交易比數 / 多單比數 / 空單比數
- 勝率 / 賺錢比數 / 虧錢比數
- Profit Factor
- Payoff Ratio
- 最多連敗
- 總獲利 / 平均每筆損益 / 平均獲利 / 平均虧損
- 最大單筆獲利 / 最大單筆虧損
- 最大回撤
- 水下週數
- Score 分數
- WFO 通過率

詳情頁目前不顯示完整逐筆交易明細，也不假裝有交易明細。若未來要顯示逐筆交易，需另行擴充 report schema 或提供交易明細 JSON。

若圖表空白，通常代表 `runs/latest/reports/details/{strategy_name}.json` 未更新或未推上 GitHub。請重新執行 Run Pipeline，確認 `reports/details` 內有 strategy detail JSON，再 push 最新報表。

## 畫面內容

- 入口防護頁
- 策略排行榜首頁
- 單一策略詳情頁
- 資料來源
- 更新時間
- 策略數量
- Top10 策略排行榜
- Top10 分數圖
- Top10 獲利圖
- 每週資產曲線圖
- 每週損益圖
- KPI 表
