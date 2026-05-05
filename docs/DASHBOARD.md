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

注意：GitHub Pages 的前端密碼不是正式資安，只是基本阻擋。密碼與資料仍會存在前端程式與公開 JSON 中。

若要真正保護資料，需使用：

- private repo
- 後端登入
- Supabase Auth
- Cloudflare Access

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

- 登入門檻畫面
- 資料來源
- 更新時間
- 策略數量
- Top10 策略排行榜
- Top10 分數圖
- Top10 獲利圖
