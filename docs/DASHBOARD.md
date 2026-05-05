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

## 資料來源

Dashboard 目前優先讀取 GitHub raw JSON：

```text
https://raw.githubusercontent.com/Hsu7183/mqquant-research-engine/main/runs/latest/reports/ranking.json
```

若 GitHub fetch 失敗，會 fallback 到：

```text
dashboard/sample_ranking.json
```

若 GitHub 與本地 sample 都失敗，會使用 `dashboard/app.js` 內建 fallback data。

## JSON 格式

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

## 單一策略詳情頁

詳情頁目前使用 ranking report 中的 `top_10` / `all_results` 資料建立 KPI 分析。

若 `all_results` 有同名策略，詳情頁會優先使用 `all_results` 的資料；否則使用 `top_10` 的 row。

目前不包含完整逐筆交易明細，也不假裝有交易明細。若未來要顯示逐筆交易，需另行擴充 report schema 或提供交易明細 JSON。

詳情頁內容包含：

- 策略摘要卡
- 分數 / 淨利相對排行圖
- KPI 表
- 策略研究風險提醒
