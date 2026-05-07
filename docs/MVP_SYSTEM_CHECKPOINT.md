# MVP System Checkpoint

This document summarizes the current mqquant MVP system boundary and operating
flow. It is a checkpoint for continuing development without mixing legacy code
back into the v2 core.

## 1. Completed System Chain

Current MVP chain:

```text
pipeline
-> job monitor
-> exporter
-> runs/latest
-> dashboard
-> decision engine
-> forward test
```

Meaning:

- Pipeline runs the research workflow and produces intermediate results.
- Job monitor records long-running status and progress under `runs/jobs/`.
- Exporter converts pipeline output into dashboard-readable artifacts.
- `runs/latest/` is the read-only artifact source for the HTML dashboard.
- Dashboard renders ranking, charts, job status, decision audit, and forward test.
- Decision engine reads ranking / OOS / WFO / risk / forward artifacts and writes
  `decision_audit.json`.
- Forward test layer records paper-tracking performance and evaluates live drift
  versus backtest expectation.

## 2. Module Locations

- Pipeline:
  - `v2/src/mqre_v2/runs/run_pipeline.py`
  - `v2/src/mqre_v2/pipeline/txt_wfo_pipeline.py`
  - `v2/src/mqre_v2/cli/run_latest_pipeline.py`
- Jobs:
  - `v2/src/mqre_v2/jobs/job_manager.py`
  - `v2/src/mqre_v2/jobs/job_state.py`
  - `scripts/run_with_progress.py`
- Export:
  - `v2/src/mqre_v2/export/artifact_exporter.py`
  - `v2/src/mqre_v2/export/serializers.py`
  - `scripts/export_from_mock_result.py`
- Decision:
  - `v2/src/mqre_v2/decision/artifact_decision.py`
  - `v2/src/mqre_v2/cli/generate_decision_audit.py`
  - `v2/src/mqre_v2/decision/recommendation.py`
  - `v2/src/mqre_v2/decision/audit_log.py`
- Forward:
  - `v2/src/mqre_v2/forward/forward_logger.py`
  - `v2/src/mqre_v2/forward/forward_evaluator.py`
  - `v2/src/mqre_v2/forward/forward_log.py`
- Dashboard:
  - `dashboard/index.html`
  - `dashboard/app.js`
  - `dashboard/styles.css`
- Artifact schema:
  - `docs/artifacts/1001plus_artifact_schema.md`

## 3. Usage

### Generate Mock Artifacts

```bash
python scripts/generate_mock_artifacts.py
```

This creates local dashboard artifacts under `runs/latest/`.

### Run Pipeline

```bash
python -m mqre_v2.cli.run_latest_pipeline
```

This runs the latest available run folder and exports dashboard artifacts.

### Run With Progress

```bash
python scripts/run_with_progress.py
```

The script prints a `job_id`. Dashboard can read:

```text
runs/jobs/{job_id}/status.json
runs/jobs/{job_id}/progress.json
```

### Start Dashboard

```bash
python -m http.server 8000
```

Open:

```text
http://localhost:8000/dashboard/
```

Do not use `file://`, because browser `fetch()` will not reliably load local
artifacts.

### Generate Decision Audit

```bash
python -m mqre_v2.cli.generate_decision_audit --artifact-dir runs/latest
```

Input artifacts:

- `runs/latest/ranking.json`
- `runs/latest/oos_summary.json`
- `runs/latest/wfo_summary.json`
- `runs/latest/risk_report.json`
- `runs/latest/forward_report.json` when available

Output:

- `runs/latest/decision_audit.json`

### Record / Evaluate Forward Test

Record one forward observation:

```python
from mqre_v2.forward import log_forward_trade

log_forward_trade("1001plus_0001", "2026-05-07 09:00:00", 20000.0, 120.0)
```

Evaluate forward performance:

```python
from mqre_v2.forward import evaluate_forward_performance

evaluate_forward_performance("1001plus_0001")
```

Outputs:

- `runs/forward/forward_log.csv`
- `runs/latest/forward_report.json`

## 4. Important Prohibitions

- Do not commit `runs/latest/*`.
- Do not commit `runs/jobs/*`.
- Do not commit `runs/forward/*`.
- Do not move or copy legacy physical data into the v2 core.
- Do not treat `0313` / `0313plus` as the strategy core.
- `1001plus` is the strategy baseline for future research.
- Do not connect broker APIs.
- Do not place orders.
- Do not connect XQ APIs.

## 5. Current Test Status

Required checks:

```bash
python -m pytest -q
node --check dashboard/app.js
```

Current expected state:

- Python tests should pass.
- Dashboard JavaScript syntax check should pass.

## 6. Next Roadmap

Phase 1: 1001plus real strategy baseline integration

- Connect the real 1001plus strategy baseline to the v2 research pipeline.
- Keep legacy 0313 / 0313plus as deprecated references only.

Phase 2: multi-core strategy search and finer progress reporting

- Improve parallel backtest execution.
- Add more granular job progress for each search stage.

Phase 3: stronger baseline / challenger promotion rules

- Expand decision thresholds.
- Add more explicit downgrade and watchlist logic.
- Improve decision audit traceability.

Phase 4: long-term forward test reports

- Build rolling forward reports by day / week / month.
- Track forward drift, recovery, and strategy health over time.

Phase 5: dashboard UX improvements

- Improve artifact loading states.
- Add filters, detail pages, and forward test trend charts.
- Keep dashboard read-only and artifact-driven.
