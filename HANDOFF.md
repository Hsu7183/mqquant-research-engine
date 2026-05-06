# Codex Handoff Instructions

When any Codex instance takes over this repository, read these files first:

1. `README.md`
2. `BASELINE.md`
3. `docs/CURRENT_STATUS.md`
4. `docs/GUI_USAGE.md`
5. `docs/WFO_SPEC.md`
6. `docs/WFO_MODULES.md`
7. `docs/CLEANUP_AUDIT.md`

## Current Standard Version

This repo has been cleaned into the v2 standard layout.

The maintained system is:

- `v2/src/mqre_v2/`
- `v2/tests/`
- `dashboard/`
- `docs/`
- `configs/`
- `templates/`
- `.github/workflows/`
- `runs/latest/reports/`

The historical `01-01-01` workbench bundle was removed because formal code, tests, dashboard, and CI no longer depend on it. The M1 TXT parser is now independent in `mqre_v2.io.m1_parser`.

## Core Rule

This repository is a strategy governance system, not a trading execution system.

Do not add:

- broker API integration
- XQ API automation
- automatic order placement
- automatic live strategy switching

## System Flow

```text
TXT folder
-> WFO Pipeline
-> Ranking JSON
-> TopN
-> Forward candidate
-> Forward Evaluation
-> Strategy Registry active
-> Promotion Recommendation
-> Decision Audit Log
-> Auto Promotion Pipeline summary
```

## Completed Core Modules

- Trade TXT Parser
- M1 OHLC TXT Parser
- WFO Window Generator
- WFO Result Schema
- WFO Pass/Fail Gate
- WFO Runner Skeleton
- Optimizer Adapter Skeleton
- WFO TXT Adapter
- WFO TXT CLI
- TXT WFO Pipeline
- Run Manifest System
- Run TXT Validation
- Run -> WFO Pipeline
- Strategy Detail Reports
- Forward Test Tracking
- Forward Test Management GUI
- Forward Evaluation
- Strategy Registry
- Promotion Recommendation Report
- Decision Audit Log
- Auto Promotion Pipeline
- Baseline vs Challenger Decision
- WFO JSON Report Exporter
- Auto Research Pipeline

## GUI

GUI modes:

1. 單一策略 WFO
2. Baseline vs Challenger
3. Optimizer
4. 批量 TXT 排名
5. Forward Test 管理
6. Auto Research Pipeline
7. Forward Evaluation
8. Strategy Registry
9. Promotion Recommendation
10. Auto Promotion Pipeline

Launch:

```powershell
.\run_gui.ps1
```

or:

```cmd
run_gui.cmd
```

## Dashboard Data

Keep these files tracked for GitHub Pages:

- `runs/latest/reports/ranking.json`
- `runs/latest/reports/details/*.json`

General run outputs remain ignored by `.gitignore`.

## Test Status

Current standard verification command:

```powershell
python -m pytest -q
node --check dashboard/app.js
python -m json.tool dashboard/sample_ranking.json
```

## Development Direction

- v1～v4 governance capabilities are retained.
- Future work should extend v2+ modules, not restore the old workbench bundle.
- v5 execution layer remains out of scope.
