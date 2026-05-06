# 1001plus Artifact Schema

This document defines the shared artifact schema for the future `1001plus` pipeline
and HTML dashboard.

The Python pipeline is responsible for generating these files. The HTML dashboard is
read-only and must only load these artifacts for presentation.

The dashboard must not run strategy optimization, backtesting, WFO, OOS, risk
calculation, or promotion logic in the browser.

## 1. Data Directory Structure

Canonical output directory:

```text
runs/latest/
  ranking.json
  strategy_detail.json
  equity_curve.csv
  trades.csv
  oos_summary.json
  wfo_summary.json
  risk_report.json
  forward_log.csv
  decision_audit.json
```

Responsibilities:

- Pipeline: produces all artifacts.
- Dashboard: reads artifacts and renders tables, charts, and summaries.
- Human operator: reviews dashboard output before any research decision is accepted.

## 2. `ranking.json`

Purpose: strategy ranking list.

Expected shape:

```json
[
  {
    "strategy_id": "1001plus_0001",
    "score": 123.45,
    "annual_return": 0.18,
    "sharpe": 1.35,
    "max_drawdown": 12500.0,
    "trade_count": 420,
    "win_rate": 0.54,
    "profit_factor": 1.42,
    "robustness_score": 0.71,
    "wfo_pass_rate": 0.67,
    "oos_sharpe": 1.12
  }
]
```

Fields:

- `strategy_id`: unique strategy identifier. Used by dashboard links, detail lookup,
  and comparison workflows.
- `score`: final ranking score. Computed by the pipeline from performance, risk,
  robustness, WFO, OOS, and cost-adjusted return components.
- `annual_return`: annualized return. Computed from the equity curve over the tested
  period.
- `sharpe`: Sharpe ratio. Computed from periodic returns, usually daily or weekly
  returns depending on the pipeline configuration.
- `max_drawdown`: maximum drawdown in money or points, using the same unit as the
  equity curve. Computed from peak-to-trough equity decline.
- `trade_count`: number of completed trades used in the evaluation.
- `win_rate`: winning trade ratio. Computed as winning trades divided by total trades.
- `profit_factor`: gross profit divided by absolute gross loss. If gross loss is zero
  and gross profit is positive, the pipeline may emit `Infinity` or a capped value
  defined by implementation policy.
- `robustness_score`: aggregate robustness metric. Computed from stress tests,
  parameter stability, plateau behavior, and related validation checks.
- `wfo_pass_rate`: Walk Forward Optimization pass rate. Computed as passed WFO rounds
  divided by total WFO rounds.
- `oos_sharpe`: Sharpe ratio measured only on out-of-sample periods.

## 3. `strategy_detail.json`

Purpose: complete information for one selected strategy.

Expected shape:

```json
{
  "strategy_id": "1001plus_0001",
  "params": {},
  "performance": {},
  "cost_model": {},
  "entry_logic_summary": "",
  "exit_logic_summary": "",
  "tags": ["trend", "breakout"]
}
```

Fields:

- `strategy_id`: unique strategy identifier. Must match a row in `ranking.json`.
- `params`: strategy parameter dictionary. Contains all parameter names and values
  needed to reproduce the strategy configuration.
- `performance`: performance summary object. Should include return, annual return,
  Sharpe, maximum drawdown, win rate, profit factor, trade count, average trade pnl,
  and other KPI fields chosen by the pipeline.
- `cost_model`: cost assumptions used in the evaluation. Should include slippage,
  fees, tax rate, point value, quantity, and total / average cost statistics.
- `entry_logic_summary`: human-readable summary of entry conditions. Used by the
  dashboard to explain why the strategy enters trades.
- `exit_logic_summary`: human-readable summary of exit conditions. Used by the
  dashboard to explain stops, targets, time exits, force exits, and protection rules.
- `tags`: list of strategy tags, such as `trend`, `mean_reversion`, or `breakout`.
  Used for filtering and grouping in the dashboard.

Calculation notes:

- `performance` must be based on cost-adjusted net pnl unless a field explicitly says
  it is raw pnl.
- `cost_model` must match the same assumptions used by ranking and validation.
- Entry and exit summaries are descriptive metadata; they are not executable logic.

## 4. `equity_curve.csv`

Purpose: time series for equity and drawdown charts.

Columns:

```csv
datetime,equity,drawdown
```

Fields:

- `datetime`: timestamp for the equity observation. Usually trade close time, daily
  mark, or weekly mark depending on pipeline settings.
- `equity`: cumulative account equity after cost-adjusted pnl. Computed from starting
  capital plus cumulative net pnl.
- `drawdown`: current drawdown from the historical equity peak. Computed as current
  equity minus rolling peak, or as a positive drawdown magnitude if the implementation
  standard chooses positive values.

## 5. `trades.csv`

Purpose: trade list for dashboard inspection and detailed analysis.

Columns:

```csv
datetime,price,side,pnl,cumulative_pnl
```

Fields:

- `datetime`: trade event timestamp. For completed-trade rows, this should usually be
  exit time.
- `price`: trade event price. For completed-trade rows, this should usually be exit
  price.
- `side`: trade side or action. Recommended values include `long`, `short`, `buy`,
  `sell`, `entry_long`, `exit_long`, `entry_short`, or `exit_short`, depending on
  pipeline detail level.
- `pnl`: cost-adjusted pnl for the trade row. If raw pnl is needed, it should be
  emitted as a separate explicit column in a later schema version.
- `cumulative_pnl`: cumulative cost-adjusted pnl up to and including this row.

## 6. `oos_summary.json`

Purpose: out-of-sample validation summary.

Expected shape:

```json
{
  "oos_periods": [],
  "oos_sharpe": 1.12,
  "oos_return": 0.08,
  "oos_mdd": 9000.0
}
```

Fields:

- `oos_periods`: list of OOS periods. Each period should include start date, end date,
  return, Sharpe, max drawdown, trade count, and pass/fail status when available.
- `oos_sharpe`: aggregate Sharpe ratio across OOS periods.
- `oos_return`: aggregate or annualized OOS return, according to pipeline policy.
- `oos_mdd`: maximum drawdown measured only on OOS equity.

Calculation notes:

- OOS metrics must not include training / optimization periods.
- OOS results must be generated by the pipeline before dashboard rendering.

## 7. `wfo_summary.json`

Purpose: Walk Forward Optimization validation summary.

Expected shape:

```json
{
  "rounds": [],
  "avg_sharpe": 1.05,
  "pass_rate": 0.67,
  "stability_score": 0.72
}
```

Fields:

- `rounds`: list of WFO rounds. Each round should include train period, gap period,
  test period, selected parameters, test performance, pass/fail flag, and fail reason.
- `avg_sharpe`: average Sharpe ratio across WFO test rounds.
- `pass_rate`: passed WFO rounds divided by total WFO rounds.
- `stability_score`: stability metric across WFO rounds. Computed from consistency of
  returns, drawdowns, trade counts, parameter stability, and score dispersion.

Calculation notes:

- WFO test results must be separated from training results.
- The dashboard displays WFO outputs only; it does not choose parameters.

## 8. `risk_report.json`

Purpose: risk and survivability report.

Expected shape:

```json
{
  "max_dd": 12500.0,
  "ulcer_index": 4.2,
  "recovery_days": 18,
  "volatility": 0.22,
  "downside_volatility": 0.14
}
```

Fields:

- `max_dd`: maximum drawdown. Computed from the equity curve peak-to-trough decline.
- `ulcer_index`: ulcer index. Computed from squared percentage drawdowns averaged over
  time, then square-rooted.
- `recovery_days`: longest or current number of days required to recover from a
  drawdown back to the previous equity high.
- `volatility`: annualized volatility of periodic returns.
- `downside_volatility`: annualized volatility of negative periodic returns only.

Calculation notes:

- Risk fields must use the same return frequency and cost assumptions documented by
  the pipeline run.
- Risk report values are for research and governance, not execution approval.

## 9. `forward_log.csv`

Purpose: forward test tracking series.

Columns:

```csv
datetime,strategy_id,pnl,cumulative_pnl
```

Fields:

- `datetime`: timestamp of the forward test observation or completed forward trade.
- `strategy_id`: strategy identifier under forward observation.
- `pnl`: forward-period cost-adjusted pnl for the row.
- `cumulative_pnl`: cumulative forward-period cost-adjusted pnl for the strategy.

Calculation notes:

- Forward log must be separated from historical backtest / WFO / OOS results.
- Promotion decisions should reference forward log data but must still require human
  review unless a later governance document explicitly changes that rule.

## 10. `decision_audit.json`

Purpose: baseline / challenger decision and promotion audit trail.

Expected shape:

```json
{
  "baseline_strategy": "1001plus_baseline",
  "challenger_strategy": "1001plus_0001",
  "promotion_decision": "review_required",
  "reason": "challenger passed score and WFO thresholds",
  "timestamp": "2026-05-07T00:00:00+08:00"
}
```

Fields:

- `baseline_strategy`: strategy id of the baseline used for comparison.
- `challenger_strategy`: strategy id of the challenger being evaluated.
- `promotion_decision`: decision result. Recommended values include `promote`,
  `reject`, `watch`, or `review_required`.
- `reason`: human-readable explanation of the decision. Should reference score,
  OOS, WFO, risk, forward test, or robustness conditions when relevant.
- `timestamp`: ISO 8601 timestamp when the decision record was generated.

Calculation notes:

- The pipeline or decision module produces this file.
- The dashboard reads and displays it.
- A promotion recommendation is not an automated trade or deployment action.

## Dashboard / Pipeline Boundary

Hard boundary:

- Pipeline produces artifacts.
- Dashboard reads artifacts.
- Dashboard must not perform heavy compute.
- Dashboard must not mutate pipeline state.
- Dashboard must not infer missing validation results as passed.

If an artifact is missing, the dashboard should show a clear missing-data state and
ask the user to rerun the pipeline.
