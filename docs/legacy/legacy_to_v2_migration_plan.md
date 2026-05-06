# Legacy To v2 Migration Plan

This document defines the allowed migration direction from the legacy `01-01-01`
system into the current `v2/src/mqre_v2` standard package.

The legacy system is reference-only. No phase may directly overwrite v2 modules with
legacy files.

`0313` and `0313plus` are deprecated references only. They are not the correct future
strategy core. The future formal research baseline should be `1001plus`.

## Phase 1: Legacy Audit Only

Scope:

- Audit the calculation workflow in `01-01-01`.
- Audit OOS concepts.
- Audit WFO concepts.
- Audit robust metrics.
- Audit hard filters.
- Audit plateau score.
- Audit top10 persistence.
- Audit forward log lifecycle.
- Compare each concept against current v2 functionality.
- Mark which concepts can be rewritten into v2.
- Mark which old strategy logic must not be migrated, especially `0313` and
  `0313plus`.

Candidate legacy references:

- `legacy_archive/01-01-01/bundle/src/backtest/report.py`
- `legacy_archive/01-01-01/bundle/src/optimize/gui_backend.py`
- `legacy_archive/01-01-01/bundle/src/optimize/auto_optimizer.py`
- `legacy_archive/01-01-01/bundle/run_history/_persistent_top10_v3.*`
- `legacy_archive/01-01-01/bundle/run_history/forward_test_log.csv`

Explicitly deprecated references:

- `legacy_archive/01-01-01/bundle/src/strategy/strategy_0313plus.py`
- `legacy_archive/01-01-01/bundle/src/strategy/strategy_0313plus_modular.py`
- any old 0313 / 0313plus-bound optimizer assumptions

Exit criteria:

- A written audit identifies reusable concepts and rejected legacy code.
- No production v2 code imports legacy modules.
- 0313 / 0313plus remains documented as deprecated reference only.

## Phase 2: 1001plus Strategy Baseline

Scope:

- Establish `1001plus` as the formal strategy research baseline.
- Apply generic validation concepts to `1001plus`.
- Keep validation logic strategy-agnostic where possible.

Rules:

- If legacy has useful validation logic, it must be abstracted before use.
- Do not preserve 0313plus binding.
- Do not make 0313 / 0313plus the default strategy core.
- Keep the current `TradeRecord` contract and cost-adjusted net pnl reporting basis.

Target v2 direction:

- Add or extend clean v2 strategy modules for `1001plus`.
- Reuse the current pipeline, report, dashboard, forward, and decision artifacts.
- Add focused tests before connecting to ranking or dashboard outputs.

Exit criteria:

- `1001plus` can be evaluated through the v2 pipeline.
- Legacy validation concepts, if used, are rewritten and tested.
- No direct legacy runtime dependency exists.

## Phase 3: HTML Dashboard

Scope:

- Use `01-01-01` old Streamlit UI only as UX reference.
- Build or extend the static HTML / JS dashboard.
- Read v2-generated JSON / CSV / artifacts only.

Rules:

- Dashboard does not perform heavy compute.
- Dashboard does not run optimization in the browser.
- Dashboard does not run backtests in the browser.
- Heavy compute stays in Python pipeline, run manager, and parallel search.
- This keeps strategy search speed independent from UI rendering.

Target v2 direction:

- Continue using `dashboard/index.html`, `dashboard/app.js`, and optional
  `dashboard/styles.css`.
- Standardize artifact paths emitted by Python.
- Keep dashboard compatible with GitHub Pages / static hosting.

Exit criteria:

- Dashboard can show ranking, strategy detail, validation summaries, forward logs,
  recommendation reports, and audit history from artifacts.
- No Streamlit / `mq01` runtime is revived as the v2 UI.

## Phase 4: Progress / Job Monitor

Scope:

- Reference progress, stop, and heartbeat concepts from:
  - `legacy_archive/01-01-01/mq01/background_worker.py`
  - `legacy_archive/01-01-01/mq01/job_store.py`

Rules:

- Rewrite with the v2 standard architecture.
- Do not directly copy old `mq01` code.
- Keep CLI execution stable on Windows.
- Keep job artifacts separate from source code.

Target v2 direction:

- Add small, testable progress/job-state modules only if needed.
- Integrate with run manager and pipeline logs.
- Keep static dashboard as a reader of emitted artifacts.

Exit criteria:

- Long-running jobs expose progress safely.
- Stop / heartbeat state is persisted in a standard v2 artifact location.
- No old `mq01` runtime dependency is introduced.

## Deprecated Source

`01-01` is deprecated because `01-01-01` is the more complete legacy reference.
Do not migrate from `01-01` unless a file is missing from `01-01-01` and the reason
is documented in the migration commit.

`0313` and `0313plus` are also deprecated references. They may be audited for generic
workflow concepts, but they must not become the formal v2 strategy core.
