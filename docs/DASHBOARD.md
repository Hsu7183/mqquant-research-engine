# Dashboard

## 如何開啟 dashboard

Dashboard 是純 HTML + JavaScript，不使用 React。

建議在 repo root 啟動一個本機靜態伺服器：

```powershell
python -m http.server 8000
```

然後在瀏覽器開啟：

```text
http://localhost:8000/dashboard/
```

直接開啟 `dashboard/index.html` 時，部分瀏覽器可能會阻擋讀取本地 JSON；若遇到空白或讀取失敗，請使用上面的 `http.server` 方式。

## JSON 格式

Dashboard 讀取符合 `docs/REPORT_SCHEMA.md` 的 ranking JSON：

- `run_id`
- `generated_at`
- `summary.total_strategies`
- `summary.valid_strategies`
- `top_10`
- `all_results`

`top_10` 每筆策略需包含：

- `rank`
- `strategy_name`
- `score`
- `total_test_net_profit`
- `pass_rate`
- `max_test_mdd`
- `average_test_pf`

## 目前資料來源

目前預設載入：

```text
dashboard/sample_ranking.json
```

## 未來資料來源

未來會接 GitHub raw JSON，例如：

```text
https://raw.githubusercontent.com/Hsu7183/mqquant-research-engine/main/runs/{run_id}/reports/ranking.json
```

接上 GitHub raw JSON 後，只需要調整 `dashboard/app.js` 的 `REPORT_URL`。
