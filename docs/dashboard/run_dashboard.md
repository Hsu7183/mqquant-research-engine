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

## 5. Generate A Decision Audit

The promotion recommendation / decision audit engine reads these artifacts:

- `runs/latest/ranking.json`
- `runs/latest/oos_summary.json`
- `runs/latest/wfo_summary.json`
- `runs/latest/risk_report.json`

Generate or refresh `runs/latest/decision_audit.json`:

```bash
python -m mqre_v2.cli.generate_decision_audit --artifact-dir runs/latest
```

The dashboard then displays:

- baseline strategy
- challenger strategy
- promotion decision
- recommendation
- score
- human review requirement
- risk warnings
- ranking / OOS / WFO / risk threshold checks

## 6. Monitor A Pipeline Job

Run the latest pipeline with progress output:

```bash
python scripts/run_with_progress.py
```

The script prints a line like:

```text
job_id=20260506183455_3761c6f8
```

It also writes:

- `runs/jobs/{job_id}/status.json`
- `runs/jobs/{job_id}/progress.json`

Start the local server:

```bash
python -m http.server 8000
```

Open:

```text
http://localhost:8000/dashboard/
```

Paste the printed `job_id` into the Job Monitor input and click `載入`.

To keep watching the job, check `Auto refresh`. The dashboard reads
`status.json` and `progress.json` every 2 seconds until the job reaches
`completed`, `failed`, or `stopped`.

If no `job_id` is entered, the dashboard shows `尚未指定 job_id`.

If the files are missing, the dashboard shows `找不到 job 或尚未產生 progress`.
