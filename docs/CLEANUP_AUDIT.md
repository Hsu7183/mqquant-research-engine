# Cleanup Audit

Date: 2026-05-06

## Pre-clean Status

- Command: `python -m pytest -q`
- Result: `219 passed`
- Git status before cleanup: clean on `main...origin/main`
- Tracked files before cleanup: 859
- Tracked files under `01-01-01/`: 731

## Current Top-level Folders Before Cleanup

- `.github/`: GitHub Actions workflows.
- `00_系統規範/`: legacy planning documents, superseded by `docs/`.
- `01-01-01/`: legacy Streamlit research workbench and bundled data package.
- `02_驗證方法/`: legacy OOS/WFO notes, superseded by `docs/WFO_SPEC.md`.
- `configs/`: parameter grid examples.
- `dashboard/`: GitHub Pages strategy dashboard.
- `docs/`: current product, workflow, schema, dashboard, and roadmap documentation.
- `incoming/`: untracked imported copy of legacy `01-01-01`.
- `projects/`: legacy placeholder strategy folders from early baseline work.
- `runs/`: generated run outputs. `runs/latest/reports/` is intentionally tracked for dashboard data.
- `templates/`: XS templates.
- `v2/`: current Python package and tests.

## Folder Purpose In Standard Version

- `.github/`: CI and scheduled pipeline automation.
- `configs/`: strategy parameter-grid inputs.
- `dashboard/`: static dashboard UI and sample ranking JSON.
- `docs/`: all maintained documentation.
- `runs/latest/reports/`: dashboard-facing ranking and detail JSON.
- `templates/`: XS template source files.
- `v2/src/mqre_v2/`: maintained application/library code.
- `v2/tests/`: maintained automated tests.

## Keep List

- `.github/`
- `configs/`
- `dashboard/`
- `docs/`
- `runs/latest/reports/`
- `templates/`
- `v2/src/mqre_v2/`
- `v2/tests/`
- `BASELINE.md`
- `HANDOFF.md`
- `README.md`
- `requirements.txt`
- `run_gui.cmd`
- `run_gui.ps1`
- `run_all_tests.cmd`

## Delete List

- `01-01-01/`
- `incoming/`
- `00_系統規範/`
- `02_驗證方法/`
- `projects/`
- `LATEST_HANDOFF.md`
- `AGENTS.md`
- `v2/docs/`
- `v2/data/`
- `v2/runs/`
- `__pycache__/`
- `.pytest_cache/`
- tracked `*.pyc`

## Delete Reasons

- `01-01-01/`: legacy workbench and data bundle. Formal `v2/src`, `v2/tests`, `dashboard`, and `.github` do not import or execute it. M1 parsing is now independent in `mqre_v2.io.m1_parser`.
- `incoming/`: untracked duplicate legacy import, including nested `.git`; not part of the maintained repo.
- `00_系統規範/` and `02_驗證方法/`: legacy notes superseded by maintained files in `docs/`.
- `projects/`: early placeholder strategy folders; current v2 workflow uses `configs/`, `templates/`, `runs/`, and reports.
- `LATEST_HANDOFF.md`: superseded by maintained `HANDOFF.md`.
- `AGENTS.md`: legacy agent note that points at old handoff content; replaced by `HANDOFF.md`.
- `v2/docs/`, `v2/data/`, `v2/runs/`: early skeleton artifacts outside the current package/test standard layout.
- caches and `*.pyc`: generated runtime artifacts that should not be tracked.

## Dependency Check

`git grep -n -E "01-01-01|bundle/data/M1.txt|M1.txt|mq01|ui_runtime|app.py" -- v2/src v2/tests dashboard .github configs templates runs README.md HANDOFF.md BASELINE.md docs run_gui.cmd run_gui.ps1 run_all_tests.cmd requirements.txt`

Findings:

- No formal code import, test, dashboard, or workflow depends on `01-01-01`.
- Remaining references are documentation/baseline statements and will be updated to describe `01-01-01` as a removed historical bundle.
- `docs/M1_TXT_FORMAT.md` references the old M1 location only as historical source context.

## Dashboard Data Protection

Do not delete:

- `runs/latest/reports/ranking.json`
- `runs/latest/reports/details/*.json`

These files are used by GitHub Pages dashboard fetch paths.
