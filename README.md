# mqquant Research Engine

mqquant-research-engine is the standard strategy governance and research engine for mqquant.

This repository is a research, reporting, observation, and decision-support system. It is not an execution system.

## Standard Repository Layout

```text
mqquant-research-engine/
  .github/
  configs/
  dashboard/
  docs/
  runs/latest/reports/
  templates/
  v2/
    src/mqre_v2/
    tests/
  BASELINE.md
  HANDOFF.md
  README.md
  requirements.txt
  run_all_tests.cmd
  run_gui.cmd
  run_gui.ps1
```

## Core Capabilities

- XS / TXT research pipeline
- Trade TXT parser
- M1 OHLC TXT parser
- M1 Backtest MVP
- L1-L4 one-click pipeline
- WFO window generation, result schema, gates, and runner
- TXT -> WFO -> ranking JSON pipeline
- Auto Research Pipeline
- Forward Test Tracking
- Forward Evaluation
- Strategy Registry
- Promotion Recommendation
- Decision Audit Log
- Auto Promotion Pipeline
- Streamlit GUI
- Static GitHub Pages dashboard

## Current Flow

```text
M1
-> Backtest
-> Trade TXT
-> Ranking
-> Detail
-> Forward
-> Auto Promotion
-> Audit
-> Dashboard
```

The current M1 strategy logic is `SimpleM1Strategy`, an MVP adapter used to prove the full data path. It is not the formal 0313 / 1001 / 0807 strategy logic.

## Launch

Windows GUI:

```cmd
run_gui.cmd
```

or:

```powershell
.\run_gui.ps1
```

Run tests:

```cmd
run_all_tests.cmd
```

or:

```powershell
python -m pytest -q
```

Dashboard:

```text
https://hsu7183.github.io/mqquant-research-engine/dashboard/
```

One-click local update from M1 to GitHub dashboard:

```cmd
run_all_pipeline.cmd
```

or:

```powershell
.\run_all_pipeline.ps1
```

## Standard Version Cleanup

The historical `01-01-01` workbench bundle has been removed from the standard repository.

Reason:

- It was a legacy data/workbench package.
- The maintained system no longer imports or executes it.
- M1 parsing now exists independently in `mqre_v2.io.m1_parser`.
- Dashboard data is served from `runs/latest/reports/`.

## Boundaries

- No broker API integration.
- No XQ API integration.
- No automatic order placement.
- No automatic live strategy switching.
- Promotion recommendations require human review.
