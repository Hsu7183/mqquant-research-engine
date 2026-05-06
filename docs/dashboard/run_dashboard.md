# Run Local Dashboard

The mqquant HTML dashboard reads local mock artifacts from `runs/latest/`.

## 1. Generate Mock Artifacts

From the repository root:

```bash
python scripts/generate_mock_artifacts.py
```

This creates:

- `runs/latest/ranking.json`
- `runs/latest/strategy_detail.json`
- `runs/latest/equity_curve.csv`
- `runs/latest/trades.csv`
- `runs/latest/oos_summary.json`
- `runs/latest/wfo_summary.json`
- `runs/latest/risk_report.json`
- `runs/latest/forward_log.csv`
- `runs/latest/decision_audit.json`

## 2. Start A Local Server

From the repository root, run one of:

```bash
python -m http.server 8000
```

## 3. Open The Dashboard

Open:

```text
http://localhost:8000/dashboard/
```

## 4. Notes

- Do not open `dashboard/index.html` with `file://`.
- Browser `fetch()` calls are blocked or inconsistent under `file://`.
- The dashboard does not run backtests, optimization, WFO, OOS, or risk calculation.
- Python produces artifacts; HTML / JS only reads artifacts and renders tables/charts.
