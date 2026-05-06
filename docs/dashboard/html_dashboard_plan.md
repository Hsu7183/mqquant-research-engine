# HTML Dashboard Plan

## 1. Dashboard Purpose

The HTML dashboard is the read-only presentation layer for mqquant research outputs.

It should display:

- strategy search results
- `1001plus` baseline / challenger comparisons
- OOS results
- WFO results
- DSR results
- PBO results
- MDD sweep results
- forward test results
- strategy detail pages
- equity curves
- trade lists
- yearly performance
- monthly performance
- weekly performance

The dashboard is not an optimizer, backtester, or heavy compute engine.

## 2. Architecture Principles

- Python is responsible for calculation and artifact export.
- HTML / JS is responsible only for reading artifacts and rendering the UI.
- No heavy optimization should run in the browser.
- No backtesting should run in the browser.
- Dashboard rendering must not affect pipeline speed.
- Heavy compute remains in the Python pipeline, run manager, and parallel search.
- The dashboard should remain compatible with static hosting such as GitHub Pages.

## 3. Recommended Output Artifacts

Recommended artifact paths:

- `runs/latest/ranking.json`
- `runs/latest/strategy_detail.json`
- `runs/latest/oos_summary.json`
- `runs/latest/wfo_summary.json`
- `runs/latest/risk_report.json`
- `runs/latest/forward_log.csv`
- `runs/latest/decision_audit.json`

The current implementation may also keep compatibility with existing paths such as:

- `runs/latest/reports/ranking.json`
- `runs/latest/reports/details/*.json`

## 4. Recommended Pages

Recommended dashboard files:

- `dashboard/index.html`
- `dashboard/app.js`
- `dashboard/styles.css`

The dashboard should stay as plain HTML / JS / CSS unless there is a clear reason to
introduce a framework.

## 5. Display Sections

Recommended UI sections:

- Run summary
- Top strategies
- Baseline vs Challenger
- `1001plus` detail
- Equity curve
- Drawdown curve
- Trade list
- OOS validation
- WFO validation
- Robustness / plateau score
- Forward test log
- Promotion recommendation
- Decision audit log

## 6. Legacy UX Reference

The old `01-01-01` Streamlit interface may be used as UX reference only.

Allowed references:

- layout ideas
- progress visibility
- validation section grouping
- result comparison patterns
- top10 display patterns
- forward log presentation

Not allowed:

- moving Streamlit code into v2
- reviving the `mq01` runtime
- making the browser perform heavy compute
- coupling dashboard UI to deprecated 0313 / 0313plus assumptions

The dashboard should present v2 artifacts produced by the Python pipeline and should
remain fast even when strategy search is slow or large.
