from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "runs" / "latest"
OUTPUT_DIR = ROOT / "docs" / "strategy"
REPORT_DATE = "20260507"


@dataclass(frozen=True, slots=True)
class TradeRow:
    dt: datetime
    price: float
    side: str
    pnl: float
    cumulative_pnl: float


@dataclass(frozen=True, slots=True)
class EquityRow:
    dt: datetime
    equity: float
    drawdown: float


def main() -> int:
    trades = _load_trades(RUN_DIR / "trades.csv")
    equity = _load_equity(RUN_DIR / "equity_curve.csv")
    ranking = _load_json(RUN_DIR / "ranking.json")
    decision = _load_json(RUN_DIR / "decision_audit.json")

    if not trades:
        raise ValueError("trades.csv has no rows")
    if not equity:
        raise ValueError("equity_curve.csv has no rows")
    if not isinstance(ranking, list) or not ranking:
        raise ValueError("ranking.json must be a non-empty list")
    if not isinstance(decision, dict):
        raise ValueError("decision_audit.json must be an object")

    annual = _annual_breakdown(trades, equity)
    monthly = _monthly_breakdown(trades, equity)
    buckets = _regime_buckets(monthly)
    context = _report_context(str(ranking[0].get("strategy_id", "")))
    job_id = _latest_job_id()

    report = _build_report(
        top_strategy=ranking[0],
        decision=decision,
        annual=annual,
        monthly=monthly,
        buckets=buckets,
        context=context,
        job_id=job_id,
    )
    output_path = OUTPUT_DIR / context["output_filename"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    worst_year = min(annual, key=lambda row: row["total_pnl"])
    worst_month = min(monthly, key=lambda row: row["total_pnl"])
    pattern = _main_failure_pattern(buckets)
    print(f"wrote {output_path.relative_to(ROOT)}")
    print(f"job_id={job_id}")
    print(f"worst_year={worst_year['year']} total_pnl={_fmt(worst_year['total_pnl'])}")
    print(f"worst_month={worst_month['month']} total_pnl={_fmt(worst_month['total_pnl'])}")
    print(f"failure_pattern={pattern}")
    return 0


def _load_json(path: Path) -> Any:
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _load_trades(path: Path) -> list[TradeRow]:
    if not path.is_file():
        raise FileNotFoundError(path)
    rows: list[TradeRow] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"datetime", "price", "side", "pnl", "cumulative_pnl"}
        if set(reader.fieldnames or []) < required:
            raise ValueError(f"trades.csv missing required fields: {required}")
        for row in reader:
            rows.append(
                TradeRow(
                    dt=_parse_datetime(row["datetime"]),
                    price=float(row["price"]),
                    side=row["side"],
                    pnl=float(row["pnl"]),
                    cumulative_pnl=float(row["cumulative_pnl"]),
                )
            )
    return rows


def _load_equity(path: Path) -> list[EquityRow]:
    if not path.is_file():
        raise FileNotFoundError(path)
    rows: list[EquityRow] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"datetime", "equity", "drawdown"}
        if set(reader.fieldnames or []) < required:
            raise ValueError(f"equity_curve.csv missing required fields: {required}")
        for row in reader:
            rows.append(
                EquityRow(
                    dt=_parse_datetime(row["datetime"]),
                    equity=float(row["equity"]),
                    drawdown=float(row["drawdown"]),
                )
            )
    return rows


def _parse_datetime(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def _annual_breakdown(
    trades: list[TradeRow],
    equity: list[EquityRow],
) -> list[dict[str, Any]]:
    trades_by_year: dict[int, list[TradeRow]] = defaultdict(list)
    equity_by_year: dict[int, list[EquityRow]] = defaultdict(list)
    for trade in trades:
        trades_by_year[trade.dt.year].append(trade)
    for row in equity:
        equity_by_year[row.dt.year].append(row)

    years = sorted(set(trades_by_year) | set(equity_by_year))
    return [
        {
            "year": year,
            **_trade_stats(trades_by_year.get(year, [])),
            "max_drawdown": _max_period_drawdown(equity_by_year.get(year, [])),
        }
        for year in years
    ]


def _monthly_breakdown(
    trades: list[TradeRow],
    equity: list[EquityRow],
) -> list[dict[str, Any]]:
    trades_by_month: dict[str, list[TradeRow]] = defaultdict(list)
    equity_by_month: dict[str, list[EquityRow]] = defaultdict(list)
    for trade in trades:
        trades_by_month[_month_key(trade.dt)].append(trade)
    for row in equity:
        equity_by_month[_month_key(row.dt)].append(row)

    months = sorted(set(trades_by_month) | set(equity_by_month))
    rows = []
    daily_std_by_month = _daily_pnl_std_by_month(trades)
    for month in months:
        stats = _trade_stats(trades_by_month.get(month, []))
        rows.append(
            {
                "month": month,
                "total_pnl": stats["total_pnl"],
                "trade_count": stats["trade_count"],
                "win_rate": stats["win_rate"],
                "avg_trade_pnl": stats["avg_trade_pnl"],
                "max_drawdown": _max_period_drawdown(equity_by_month.get(month, [])),
                "daily_pnl_std": daily_std_by_month.get(month, 0.0),
            }
        )
    return rows


def _trade_stats(rows: list[TradeRow]) -> dict[str, Any]:
    trade_count = len(rows)
    total_pnl = sum(row.pnl for row in rows)
    win_count = sum(1 for row in rows if row.pnl > 0)
    return {
        "total_pnl": total_pnl,
        "trade_count": trade_count,
        "win_rate": (win_count / trade_count) if trade_count else 0.0,
        "avg_trade_pnl": (total_pnl / trade_count) if trade_count else 0.0,
    }


def _max_period_drawdown(rows: list[EquityRow]) -> float:
    if not rows:
        return 0.0
    peak = rows[0].equity
    max_dd = 0.0
    for row in rows:
        peak = max(peak, row.equity)
        max_dd = max(max_dd, peak - row.equity)
    return max(max_dd, max(row.drawdown for row in rows))


def _daily_pnl_std_by_month(trades: list[TradeRow]) -> dict[str, float]:
    daily: dict[tuple[str, str], float] = defaultdict(float)
    for trade in trades:
        daily[(_month_key(trade.dt), trade.dt.date().isoformat())] += trade.pnl

    by_month: dict[str, list[float]] = defaultdict(list)
    for (month, _day), pnl in daily.items():
        by_month[month].append(pnl)

    return {month: _std(values) for month, values in by_month.items()}


def _regime_buckets(monthly: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not monthly:
        return []
    vol_threshold = _percentile([row["daily_pnl_std"] for row in monthly], 0.5)
    trade_threshold = _percentile([row["trade_count"] for row in monthly], 0.5)
    bucket_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in monthly:
        vol_bucket = "high_vol" if row["daily_pnl_std"] >= vol_threshold else "low_vol"
        behavior = _behavior_bucket(row, trade_threshold)
        bucket_rows[vol_bucket].append(row)
        bucket_rows[behavior].append(row)
        bucket_rows[f"{vol_bucket}_{behavior}"].append(row)

    summary = []
    for bucket, rows in sorted(bucket_rows.items()):
        summary.append(
            {
                "bucket": bucket,
                "months": len(rows),
                "total_pnl": sum(row["total_pnl"] for row in rows),
                "trade_count": sum(int(row["trade_count"]) for row in rows),
                "avg_monthly_pnl": mean([row["total_pnl"] for row in rows]) if rows else 0.0,
                "max_drawdown": max([row["max_drawdown"] for row in rows], default=0.0),
                "negative_months": sum(1 for row in rows if row["total_pnl"] < 0),
            }
        )
    return summary


def _behavior_bucket(row: dict[str, Any], trade_threshold: float) -> str:
    if row["total_pnl"] >= 0:
        return "trend_good"
    if row["trade_count"] >= trade_threshold:
        return "chop_bad"
    return "weak_low_activity"


def _build_report(
    top_strategy: dict[str, Any],
    decision: dict[str, Any],
    annual: list[dict[str, Any]],
    monthly: list[dict[str, Any]],
    buckets: list[dict[str, Any]],
    context: dict[str, str],
    job_id: str,
) -> str:
    top_id = str(top_strategy.get("strategy_id", ""))
    data_note = _data_source_note(top_id)
    worst_years = sorted(annual, key=lambda row: row["total_pnl"])[:3]
    worst_months = sorted(monthly, key=lambda row: row["total_pnl"])[:10]
    pattern = _main_failure_pattern(buckets)

    lines = [
        f"# {context['title']} - 2026-05-07",
        "",
        "## 1. Top Challenger",
        "",
        f"- data source: `{context['data_source']}`",
        f"- scope: {context['scope']}",
        f"- job_id: `{job_id}`",
        f"- strategy_id: `{top_id}`",
        f"- promotion_decision: `{decision.get('promotion_decision', '')}`",
        f"- decision_reason: `{decision.get('reason', '')}`",
        f"- score: `{_fmt(top_strategy.get('score'))}`",
        f"- sharpe: `{_fmt(top_strategy.get('sharpe'))}`",
        f"- max_drawdown: `{_fmt(top_strategy.get('max_drawdown'))}`",
        f"- trade_count: `{top_strategy.get('trade_count', '')}`",
        f"- data_source_note: {data_note}",
        "",
        "## 2. Annual Breakdown Table",
        "",
        _annual_table(annual),
        "",
        "## 3. Worst Years",
        "",
        _annual_table(worst_years),
        "",
        "## 4. Worst Months",
        "",
        _monthly_table(worst_months),
        "",
        "## 5. Regime Bucket Summary",
        "",
        _bucket_table(buckets),
        "",
        "## 6. Interpretation",
        "",
        f"- main_failure_pattern: `{pattern}`",
        *_interpretation_notes(annual, monthly, buckets, data_note),
        "",
        "## 7. Next Steps",
        "",
        "1. Do not disable a specific calendar year blindly; first confirm whether bad years share a market regime.",
        "2. Add a regime filter if the losses concentrate in `chop_bad` or high-volatility negative months.",
        "3. Reduce trade frequency only if high-trade-count months also show strongly negative expectancy.",
        "4. Re-check entry filters before adding more exit variations, especially if losses cluster in low-quality trend/chop buckets.",
        "5. Re-run this script after each 300-run so the report title and source follow the current `runs/latest` artifacts.",
        "",
    ]
    return "\n".join(lines)


def _report_context(strategy_id: str) -> dict[str, str]:
    if strategy_id.startswith("1001plus_v2exit_"):
        return {
            "title": "1001plus v2_exit Annual / Regime Bucket Breakdown",
            "data_source": "1001plus_v2_exit 300-run artifacts",
            "scope": "this report only describes the `v2_exit` failed experiment regime breakdown.",
            "output_filename": f"1001plus_v2_exit_regime_breakdown_{REPORT_DATE}.md",
        }
    if strategy_id.startswith("1001plus_"):
        return {
            "title": "1001plus risk_constrained Annual / Regime Bucket Breakdown",
            "data_source": "1001plus risk_constrained 300-run artifacts",
            "scope": "this report describes the risk_constrained 300-run regime breakdown.",
            "output_filename": f"1001plus_risk_constrained_regime_breakdown_{REPORT_DATE}.md",
        }
    return {
        "title": "1001plus Annual / Regime Bucket Breakdown",
        "data_source": "unrecognized 1001plus-like artifacts",
        "scope": "this report describes the current `runs/latest` artifacts.",
        "output_filename": f"1001plus_regime_breakdown_{REPORT_DATE}.md",
    }


def _data_source_note(strategy_id: str) -> str:
    if strategy_id.startswith("1001plus_v2exit_"):
        return "`runs/latest` contains `1001plus_v2_exit` 300-run artifacts; this is not the earlier risk_constrained run."
    if strategy_id.startswith("1001plus_"):
        return "`runs/latest` contains 1001plus risk_constrained 300-run artifacts for this report."
    return "`runs/latest` strategy naming is not recognized as 1001plus."


def _latest_job_id() -> str:
    jobs_dir = ROOT / "runs" / "jobs"
    if not jobs_dir.is_dir():
        return ""
    job_dirs = [path for path in jobs_dir.iterdir() if path.is_dir()]
    if not job_dirs:
        return ""
    return max(job_dirs, key=lambda path: path.stat().st_mtime).name


def _annual_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No annual rows."
    lines = [
        "| year | total_pnl | trade_count | win_rate | max_drawdown | avg_trade_pnl |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row['year']} | "
            f"{_fmt(row['total_pnl'])} | "
            f"{row['trade_count']} | "
            f"{_pct(row['win_rate'])} | "
            f"{_fmt(row['max_drawdown'])} | "
            f"{_fmt(row['avg_trade_pnl'])} |"
        )
    return "\n".join(lines)


def _monthly_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No monthly rows."
    lines = [
        "| month | total_pnl | trade_count | max_drawdown | daily_pnl_std |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row['month']} | "
            f"{_fmt(row['total_pnl'])} | "
            f"{row['trade_count']} | "
            f"{_fmt(row['max_drawdown'])} | "
            f"{_fmt(row['daily_pnl_std'])} |"
        )
    return "\n".join(lines)


def _bucket_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No bucket rows."
    lines = [
        "| bucket | months | total_pnl | trade_count | avg_monthly_pnl | max_drawdown | negative_months |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row['bucket']} | "
            f"{row['months']} | "
            f"{_fmt(row['total_pnl'])} | "
            f"{row['trade_count']} | "
            f"{_fmt(row['avg_monthly_pnl'])} | "
            f"{_fmt(row['max_drawdown'])} | "
            f"{row['negative_months']} |"
        )
    return "\n".join(lines)


def _interpretation_notes(
    annual: list[dict[str, Any]],
    monthly: list[dict[str, Any]],
    buckets: list[dict[str, Any]],
    data_note: str,
) -> list[str]:
    worst_year = min(annual, key=lambda row: row["total_pnl"])
    worst_month = min(monthly, key=lambda row: row["total_pnl"])
    worst_bucket = min(buckets, key=lambda row: row["total_pnl"]) if buckets else None
    high_trade_negative_months = [
        row for row in monthly if row["total_pnl"] < 0 and row["trade_count"] >= _percentile([m["trade_count"] for m in monthly], 0.5)
    ]
    notes = [
        f"- Worst year is `{worst_year['year']}` with total_pnl `{_fmt(worst_year['total_pnl'])}`.",
        f"- Worst month is `{worst_month['month']}` with total_pnl `{_fmt(worst_month['total_pnl'])}`.",
        f"- Negative high-trade-count months: `{len(high_trade_negative_months)}`.",
        f"- Data source caution: {data_note}",
    ]
    if worst_bucket is not None:
        notes.append(
            f"- Worst regime bucket is `{worst_bucket['bucket']}` with total_pnl `{_fmt(worst_bucket['total_pnl'])}`."
        )
    return notes


def _main_failure_pattern(buckets: list[dict[str, Any]]) -> str:
    if not buckets:
        return "no bucket data"
    by_name = {row["bucket"]: row for row in buckets}
    chop = by_name.get("chop_bad")
    high_vol_chop = by_name.get("high_vol_chop_bad")
    low_vol_chop = by_name.get("low_vol_chop_bad")
    worst = min(buckets, key=lambda row: row["total_pnl"])
    if high_vol_chop and high_vol_chop["total_pnl"] < 0:
        return "high_vol_chop_bad losses dominate"
    if chop and chop["total_pnl"] < 0:
        return "negative pnl clusters in high-trade chop_bad months"
    if low_vol_chop and low_vol_chop["total_pnl"] < 0:
        return "low_vol_chop_bad losses dominate"
    return f"worst bucket is {worst['bucket']}"


def _month_key(value: datetime) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = sum(values) / len(values)
    return (sum((value - avg) ** 2 for value in values) / len(values)) ** 0.5


def _percentile(values: list[float | int], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * q))))
    return ordered[index]


def _fmt(value: Any) -> str:
    number = float(value or 0.0)
    if abs(number) >= 100:
        return f"{number:.4f}"
    return f"{number:.6f}".rstrip("0").rstrip(".")


def _pct(value: Any) -> str:
    return f"{float(value or 0.0) * 100:.2f}%"


if __name__ == "__main__":
    raise SystemExit(main())
