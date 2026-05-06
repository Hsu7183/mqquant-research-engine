"""Generate mock 1001plus artifacts for dashboard/schema testing.

This script intentionally uses deterministic mock data only. It does not import or
execute mqre_v2 strategy, backtest, WFO, or pipeline code.
"""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "runs" / "latest"


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _build_ranking() -> list[dict[str, object]]:
    strategies: list[dict[str, object]] = []
    base_scores = [128.4, 119.8, 111.2, 104.6, 96.5]
    for idx, score in enumerate(base_scores, start=1):
        strategies.append(
            {
                "strategy_id": f"1001plus_{idx:04d}",
                "score": round(score, 2),
                "annual_return": round(0.215 - idx * 0.014, 4),
                "sharpe": round(1.72 - idx * 0.11, 3),
                "max_drawdown": round(8200 + idx * 1450, 2),
                "trade_count": 360 + idx * 28,
                "win_rate": round(0.58 - idx * 0.012, 4),
                "profit_factor": round(1.78 - idx * 0.08, 3),
                "robustness_score": round(0.82 - idx * 0.035, 3),
                "wfo_pass_rate": round(0.78 - idx * 0.025, 3),
                "oos_sharpe": round(1.46 - idx * 0.09, 3),
            }
        )
    return strategies


def _build_strategy_detail(ranking: list[dict[str, object]]) -> dict[str, object]:
    top = ranking[0]
    return {
        "strategy_id": top["strategy_id"],
        "params": {
            "baseline": "1001plus",
            "don_len": 72,
            "ema_fast": 5,
            "ema_slow": 34,
            "atr_len": 14,
            "atr_tp_k": 3.5,
            "atr_sl_k": 1.8,
            "force_exit_time": "13:12",
        },
        "performance": {
            "return": 0.186,
            "annual_return": top["annual_return"],
            "sharpe": top["sharpe"],
            "mdd": top["max_drawdown"],
            "win_rate": top["win_rate"],
            "profit_factor": top["profit_factor"],
            "trade_count": top["trade_count"],
            "average_trade_pnl": 42.7,
            "net_total_profit": 16568.0,
            "raw_total_profit": 18420.0,
        },
        "cost_model": {
            "slippage_points_per_side": 2.0,
            "fee_money_per_side": 0.0,
            "tax_rate": 0.00002,
            "point_value": 50.0,
            "qty": 1,
            "avg_cost_per_trade_points": 4.82,
        },
        "entry_logic_summary": (
            "1001plus mock baseline: trend-aligned breakout after prior-bar "
            "confirmation with volatility filter."
        ),
        "exit_logic_summary": (
            "ATR target, ATR stop, max holding bars, and intraday force exit."
        ),
        "tags": ["trend", "breakout", "1001plus"],
    }


def _build_equity_curve(start: datetime, rows: int = 220) -> list[dict[str, object]]:
    equity_rows: list[dict[str, object]] = []
    equity = 100000.0
    peak = equity
    for idx in range(rows):
        drift = 92.0 + idx * 0.18
        cycle = math.sin(idx / 7.0) * 85.0
        shock = -620.0 if idx in {42, 87, 138, 171} else 0.0
        equity += drift + cycle + shock
        peak = max(peak, equity)
        drawdown = max(0.0, peak - equity)
        equity_rows.append(
            {
                "datetime": _iso(start + timedelta(days=idx)),
                "equity": round(equity, 2),
                "drawdown": round(drawdown, 2),
            }
        )
    return equity_rows


def _build_trades(start: datetime, rows: int = 60) -> list[dict[str, object]]:
    trade_rows: list[dict[str, object]] = []
    cumulative = 0.0
    for idx in range(rows):
        pnl = 145.0 + math.sin(idx / 3.0) * 95.0
        if idx % 9 == 0:
            pnl -= 310.0
        if idx % 17 == 0:
            pnl += 260.0
        cumulative += pnl
        trade_rows.append(
            {
                "datetime": _iso(start + timedelta(days=idx * 2, minutes=idx * 3)),
                "price": round(20350 + idx * 8 + math.sin(idx / 4.0) * 35, 2),
                "side": "buy" if idx % 2 == 0 else "sell",
                "pnl": round(pnl, 2),
                "cumulative_pnl": round(cumulative, 2),
            }
        )
    return trade_rows


def _build_oos_summary() -> dict[str, object]:
    periods = []
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for idx in range(4):
        period_start = start + timedelta(days=idx * 120)
        period_end = period_start + timedelta(days=89)
        periods.append(
            {
                "period_id": idx + 1,
                "start": period_start.date().isoformat(),
                "end": period_end.date().isoformat(),
                "return": round(0.034 + idx * 0.007, 4),
                "sharpe": round(1.03 + idx * 0.08, 3),
                "max_drawdown": round(7200 + idx * 650, 2),
                "trade_count": 56 + idx * 8,
                "passed": idx != 1,
            }
        )
    return {
        "oos_periods": periods,
        "oos_sharpe": 1.18,
        "oos_return": 0.162,
        "oos_mdd": 9150.0,
    }


def _build_wfo_summary() -> dict[str, object]:
    rounds = []
    start = datetime(2023, 1, 1, tzinfo=timezone.utc)
    for idx in range(6):
        test_start = start + timedelta(days=idx * 90)
        test_end = test_start + timedelta(days=59)
        rounds.append(
            {
                "round_id": idx + 1,
                "train_start": (test_start - timedelta(days=365)).date().isoformat(),
                "train_end": (test_start - timedelta(days=31)).date().isoformat(),
                "test_start": test_start.date().isoformat(),
                "test_end": test_end.date().isoformat(),
                "sharpe": round(0.95 + idx * 0.07, 3),
                "return": round(0.018 + idx * 0.004, 4),
                "max_drawdown": round(6800 + idx * 500, 2),
                "trade_count": 44 + idx * 5,
                "passed": idx not in {1, 4},
                "fail_reason": "" if idx not in {1, 4} else "drawdown watch zone",
            }
        )
    return {
        "rounds": rounds,
        "avg_sharpe": 1.125,
        "pass_rate": 0.667,
        "stability_score": 0.74,
    }


def _build_risk_report() -> dict[str, object]:
    return {
        "max_dd": 9650.0,
        "ulcer_index": 3.86,
        "recovery_days": 17,
        "volatility": 0.218,
        "downside_volatility": 0.132,
    }


def _build_forward_log(start: datetime, rows: int = 25) -> list[dict[str, object]]:
    forward_rows: list[dict[str, object]] = []
    cumulative = 0.0
    for idx in range(rows):
        pnl = 68.0 + math.cos(idx / 2.0) * 38.0
        if idx in {6, 13, 21}:
            pnl -= 155.0
        cumulative += pnl
        forward_rows.append(
            {
                "datetime": _iso(start + timedelta(days=idx)),
                "strategy_id": "1001plus_0001",
                "pnl": round(pnl, 2),
                "cumulative_pnl": round(cumulative, 2),
            }
        )
    return forward_rows


def _build_decision_audit() -> dict[str, object]:
    return {
        "baseline_strategy": "1001plus_baseline",
        "challenger_strategy": "1001plus_0001",
        "promotion_decision": "promote",
        "reason": (
            "mock challenger passed ranking, OOS, WFO, and risk thresholds; human "
            "review is still required before promotion."
        ),
        "timestamp": _iso(datetime(2026, 5, 7, 9, 0, tzinfo=timezone.utc)),
        "recommend_promote": True,
        "requires_human_review": True,
        "score": 128.4,
        "risk_warnings": [],
        "checks": {
            "ranking": {
                "score": 128.4,
                "min_score": 100.0,
                "profit_factor": 1.7,
                "min_profit_factor": 1.1,
                "trade_count": 388,
                "min_trade_count": 30,
            },
            "oos": {
                "oos_sharpe": 1.18,
                "min_oos_sharpe": 1.0,
                "oos_return": 0.162,
                "min_oos_return": 0.0,
                "oos_mdd": 9150.0,
                "max_oos_mdd": 15000.0,
            },
            "wfo": {
                "pass_rate": 0.667,
                "min_pass_rate": 0.6,
                "avg_sharpe": 1.125,
                "min_avg_sharpe": 1.0,
                "stability_score": 0.74,
                "min_stability_score": 0.6,
            },
            "risk": {
                "max_dd": 9650.0,
                "max_risk_drawdown": 15000.0,
                "ulcer_index": 3.86,
                "max_ulcer_index": 10.0,
                "recovery_days": 17,
                "max_recovery_days": 60,
            },
        },
    }


def generate_mock_artifacts() -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    start = datetime(2024, 1, 2, 8, 45, tzinfo=timezone.utc)
    ranking = _build_ranking()
    generated_files = [
        OUTPUT_DIR / "ranking.json",
        OUTPUT_DIR / "strategy_detail.json",
        OUTPUT_DIR / "equity_curve.csv",
        OUTPUT_DIR / "trades.csv",
        OUTPUT_DIR / "oos_summary.json",
        OUTPUT_DIR / "wfo_summary.json",
        OUTPUT_DIR / "risk_report.json",
        OUTPUT_DIR / "forward_log.csv",
        OUTPUT_DIR / "decision_audit.json",
    ]

    _write_json(OUTPUT_DIR / "ranking.json", ranking)
    _write_json(OUTPUT_DIR / "strategy_detail.json", _build_strategy_detail(ranking))
    _write_csv(
        OUTPUT_DIR / "equity_curve.csv",
        ["datetime", "equity", "drawdown"],
        _build_equity_curve(start),
    )
    _write_csv(
        OUTPUT_DIR / "trades.csv",
        ["datetime", "price", "side", "pnl", "cumulative_pnl"],
        _build_trades(start),
    )
    _write_json(OUTPUT_DIR / "oos_summary.json", _build_oos_summary())
    _write_json(OUTPUT_DIR / "wfo_summary.json", _build_wfo_summary())
    _write_json(OUTPUT_DIR / "risk_report.json", _build_risk_report())
    _write_csv(
        OUTPUT_DIR / "forward_log.csv",
        ["datetime", "strategy_id", "pnl", "cumulative_pnl"],
        _build_forward_log(start),
    )
    _write_json(OUTPUT_DIR / "decision_audit.json", _build_decision_audit())

    return generated_files


def main() -> None:
    files = generate_mock_artifacts()
    print("Generated mock 1001plus artifacts:")
    for path in files:
        print(f"- {path.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
