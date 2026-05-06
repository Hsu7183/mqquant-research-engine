# Legacy Inventory: 01-01-01

## Positioning

`01-01-01` is the only legacy reference for the old mqquant research workbench.
It is not the current strategy core, and it is not part of the maintained
`v2/src/mqre_v2` package.

The future strategy research baseline should be `1001plus`.

`0313` and `0313plus` are deprecated references only. They must not be described as
the formal strategy core, and their strategy logic must not be migrated into v2 as
the primary baseline.

## Allowed Legacy Use

`01-01-01` may be used only as a reference for concepts such as:

- calculation workflow
- validation-layer design
- OOS workflow ideas
- WFO workflow ideas
- robust metrics
- hard filters
- plateau score
- top10 persistence
- forward log lifecycle
- progress / stop / heartbeat concepts
- old Streamlit UX reference

All useful ideas must be rewritten into the v2 architecture. Do not directly import
or copy the old Streamlit, `bundle`, or `mq01` runtime.

## Difference From 01-01

`01-01-01` is a more complete follow-up copy of `01-01`.

Observed differences:

- `01-01-01` contains all common `01-01` files plus additional run history and exports.
- `01-01-01` has more complete handoff and status documentation.
- `01-01-01` includes an additional full project explanation document.
- `01-01-01` includes additional generated XS artifacts and parameter presets.
- `01-01-01` includes extra forward-test and run-history records.

Because `01-01-01` is the richer version, `01-01` is deprecated and should not be used
as a maintenance target.

## Reference Areas Worth Auditing

The following legacy areas may contain useful concepts to audit. They are not direct
migration targets:

- `bundle/src/backtest/report.py`
  - KPI, drawdown, NAV, period return, recovery, and reporting calculations.
- `bundle/src/optimize/gui_backend.py`
  - Optimizer workflow, hard filters, robust scoring, WFO / holdout-style
    qualification, plateau score, and result sorting ideas.
- `bundle/src/optimize/auto_optimizer.py`
  - Score aggregation and stability ideas.
- `bundle/src/research/xs_generator.py`
  - XS source generation ideas.
- `bundle/src/research/xscript_policy.py`
  - XScript policy / guardrail reference text.
- `mq01/background_worker.py`
  - Background job progress, stop, heartbeat, and worker lifecycle ideas.
- `mq01/job_store.py`
  - Job state persistence and monitoring ideas.
- `bundle/run_history/_persistent_top10_v3.*`
  - Historical top strategy persistence concepts.
- `bundle/run_history/forward_test_log.csv`
  - Legacy forward-test lifecycle records.

## Deprecated Strategy Logic

The following legacy strategy logic is deprecated reference material only:

- `0313`
- `0313plus`
- `bundle/src/strategy/strategy_0313plus.py`
- `bundle/src/strategy/strategy_0313plus_modular.py`
- any old `0313plus`-bound optimizer or generated strategy flow

These files may be read to understand historical assumptions, naming, UI expectations,
or validation flow. They must not become the official strategy baseline in v2.

If a generic validation concept is found inside a 0313plus-bound file, extract the
concept only and rewrite it as strategy-agnostic v2 code that can be applied to
`1001plus`.

## Content Not Recommended For Migration

The following content should not be migrated into v2:

- `__pycache__/`
- `*.pyc`
- worker stdout / stderr logs
- transient job state files
- old `mq01_jobs/` output folders
- generated run logs
- duplicate large market data files
- monolithic Streamlit UI files copied as-is
- the whole `bundle/` tree copied directly into `v2/src/mqre_v2`
- the whole `mq01/` runtime copied directly into `v2/src/mqre_v2`
- old 0313 / 0313plus strategy logic as the formal core

These files are historical runtime artifacts or old packaging structure. They should
not become part of the current standard system.

## Relationship To v2

The current maintained system is `v2/src/mqre_v2`.

The v2 system remains the formal core for:

- M1 TXT parsing
- TradeRecord parsing
- generated intraday strategy backtesting
- futures cost model
- WFO / ranking pipeline
- strategy detail reports
- HTML / JS dashboard artifacts
- forward test tracking
- auto research / promotion / decision audit flow
- run manager and parallel strategy search

Legacy concepts must only be migrated by extracting behavior, rewriting it into small
v2 modules, and adding tests.

## Hard Rule

`legacy_archive/01-01-01` is reference-only.

Do not:

- overwrite `v2/src/mqre_v2` with legacy files
- import directly from legacy code in production v2 modules
- make `01-01` a maintenance target
- treat 0313 / 0313plus as the official strategy core
- treat legacy run outputs as current pipeline outputs
- revive the old Streamlit / bundle / mq01 architecture inside v2

Any migration from legacy to v2 must be deliberate, test-covered, strategy-agnostic
where possible, and compatible with the future `1001plus` baseline.
