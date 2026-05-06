from __future__ import annotations

import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from mqre_v2.decision.artifact_decision import build_decision_audit
from mqre_v2.export.serializers import format_datetime, write_csv, write_json


RANKING_FIELDS = [
    "strategy_id",
    "score",
    "annual_return",
    "sharpe",
    "max_drawdown",
    "trade_count",
    "win_rate",
    "profit_factor",
    "robustness_score",
    "wfo_pass_rate",
    "oos_sharpe",
]

EQUITY_FIELDS = ["datetime", "equity", "drawdown"]
TRADE_FIELDS = ["datetime", "price", "side", "pnl", "cumulative_pnl"]
FORWARD_FIELDS = ["datetime", "strategy_id", "pnl", "cumulative_pnl"]


def export_latest_run(result: dict, output_dir: str = "runs/latest") -> list[str]:
    """Export a pipeline-like result into the 1001plus dashboard artifact schema.

    Missing pieces are filled with deterministic mock fallback data so the dashboard
    always receives a complete artifact set while the upstream pipeline is still
    evolving.
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    source = result or {}
    ranking = _normalize_ranking(_first_present(source, ["ranking", "strategies", "all_results", "top_10"]))
    strategy_detail = _normalize_strategy_detail(source.get("strategy_detail"), ranking, source)
    equity_curve = _normalize_equity_curve(source.get("equity_curve"))
    trades = _normalize_trades(source.get("trades"))
    oos_summary = _normalize_oos_summary(source.get("oos_summary"))
    wfo_summary = _normalize_wfo_summary(source.get("wfo_summary"))
    risk_report = _normalize_risk_report(source.get("risk_report"))
    forward_log = _normalize_forward_log(source.get("forward_log"), ranking)
    decision_audit = _normalize_decision_audit(
        source.get("decision_audit"),
        ranking,
        oos_summary,
        wfo_summary,
        risk_report,
    )

    files = [
        output / "ranking.json",
        output / "strategy_detail.json",
        output / "equity_curve.csv",
        output / "trades.csv",
        output / "oos_summary.json",
        output / "wfo_summary.json",
        output / "risk_report.json",
        output / "forward_log.csv",
        output / "decision_audit.json",
    ]

    write_json(files[0], ranking)
    write_json(files[1], strategy_detail)
    write_csv(files[2], equity_curve, EQUITY_FIELDS)
    write_csv(files[3], trades, TRADE_FIELDS)
    write_json(files[4], oos_summary)
    write_json(files[5], wfo_summary)
    write_json(files[6], risk_report)
    write_csv(files[7], forward_log, FORWARD_FIELDS)
    write_json(files[8], decision_audit)

    return [str(path) for path in files]


def _first_present(source: dict, keys: list[str]) -> Any:
    for key in keys:
        value = source.get(key)
        if value:
            return value
    return None


def _normalize_ranking(raw: Any) -> list[dict[str, Any]]:
    rows = raw if isinstance(raw, list) and raw else _mock_ranking()
    normalized = [_ranking_row(row, index) for index, row in enumerate(rows, start=1)]
    return sorted(normalized, key=lambda item: _as_float(item["score"]), reverse=True)


def _ranking_row(row: Any, index: int) -> dict[str, Any]:
    item = row if isinstance(row, dict) else {}
    score = _as_float(item.get("score"), 100.0 - index * 3.5)
    total_profit = _as_float(
        item.get("total_test_net_profit", item.get("net_total_profit")),
        12000.0 - index * 650.0,
    )
    max_drawdown = _as_float(item.get("max_drawdown", item.get("max_test_mdd")), 9000.0 + index * 900.0)
    profit_factor = _as_float(item.get("profit_factor", item.get("average_test_pf")), 1.6 - index * 0.04)
    sharpe = _as_float(item.get("sharpe"), max(0.4, profit_factor - 0.2))
    return {
        "strategy_id": str(item.get("strategy_id") or item.get("strategy_name") or f"1001plus_{index:04d}"),
        "score": round(score, 4),
        "annual_return": round(_as_float(item.get("annual_return"), total_profit / 100000.0), 6),
        "sharpe": round(sharpe, 6),
        "max_drawdown": round(max_drawdown, 4),
        "trade_count": int(_as_float(item.get("trade_count", item.get("total_test_trade_count")), 300 + index * 12)),
        "win_rate": round(_as_float(item.get("win_rate"), 0.56 - index * 0.01), 6),
        "profit_factor": round(profit_factor, 6),
        "robustness_score": round(_as_float(item.get("robustness_score"), min(1.0, score / 150.0)), 6),
        "wfo_pass_rate": round(_as_float(item.get("wfo_pass_rate", item.get("pass_rate")), 0.7 - index * 0.02), 6),
        "oos_sharpe": round(_as_float(item.get("oos_sharpe"), sharpe * 0.85), 6),
    }


def _normalize_strategy_detail(raw: Any, ranking: list[dict[str, Any]], source: dict) -> dict[str, Any]:
    top = ranking[0]
    detail = raw if isinstance(raw, dict) else {}
    performance = detail.get("performance") if isinstance(detail.get("performance"), dict) else {}
    params = detail.get("params") if isinstance(detail.get("params"), dict) else source.get("params", {})
    cost_model = detail.get("cost_model") if isinstance(detail.get("cost_model"), dict) else source.get("cost_model", {})
    return {
        "strategy_id": str(detail.get("strategy_id") or top["strategy_id"]),
        "params": params or _mock_params(),
        "performance": {
            "return": _as_float(performance.get("return"), top["annual_return"]),
            "annual_return": _as_float(performance.get("annual_return"), top["annual_return"]),
            "sharpe": _as_float(performance.get("sharpe"), top["sharpe"]),
            "mdd": _as_float(performance.get("mdd"), top["max_drawdown"]),
            "win_rate": _as_float(performance.get("win_rate"), top["win_rate"]),
            "profit_factor": _as_float(performance.get("profit_factor"), top["profit_factor"]),
            "trade_count": int(_as_float(performance.get("trade_count"), top["trade_count"])),
            "average_trade_pnl": _as_float(performance.get("average_trade_pnl"), 42.7),
        },
        "cost_model": cost_model or _mock_cost_model(),
        "entry_logic_summary": str(
            detail.get("entry_logic_summary")
            or "1001plus artifact exporter fallback: trend and breakout confirmation."
        ),
        "exit_logic_summary": str(
            detail.get("exit_logic_summary")
            or "ATR stop, ATR target, time stop, and intraday force exit."
        ),
        "tags": detail.get("tags") if isinstance(detail.get("tags"), list) else ["trend", "breakout", "1001plus"],
    }


def _normalize_equity_curve(raw: Any) -> list[dict[str, Any]]:
    rows = raw if isinstance(raw, list) and raw else _mock_equity_curve()
    peak = None
    normalized = []
    for index, row in enumerate(rows):
        item = row if isinstance(row, dict) else {}
        equity = _as_float(item.get("equity"), 100000.0 + index * 95.0)
        peak = equity if peak is None else max(peak, equity)
        drawdown = _as_float(item.get("drawdown"), max(0.0, peak - equity))
        normalized.append(
            {
                "datetime": format_datetime(item.get("datetime") or item.get("ts") or _mock_dt(index)),
                "equity": round(equity, 4),
                "drawdown": round(drawdown, 4),
            }
        )
    return normalized


def _normalize_trades(raw: Any) -> list[dict[str, Any]]:
    rows = raw if isinstance(raw, list) and raw else _mock_trades()
    cumulative = 0.0
    normalized = []
    for index, row in enumerate(rows):
        item = row if isinstance(row, dict) else {}
        pnl = _as_float(item.get("pnl"), 80.0 + math.sin(index / 3.0) * 50.0)
        cumulative = _as_float(item.get("cumulative_pnl"), cumulative + pnl)
        normalized.append(
            {
                "datetime": format_datetime(item.get("datetime") or item.get("exit_time") or _mock_dt(index)),
                "price": round(_as_float(item.get("price", item.get("exit_price")), 20000.0 + index * 5.0), 4),
                "side": str(item.get("side") or ("buy" if index % 2 == 0 else "sell")),
                "pnl": round(pnl, 4),
                "cumulative_pnl": round(cumulative, 4),
            }
        )
    return normalized


def _normalize_oos_summary(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict) and raw:
        return {
            "oos_periods": raw.get("oos_periods", []),
            "oos_sharpe": _as_float(raw.get("oos_sharpe"), 1.0),
            "oos_return": _as_float(raw.get("oos_return"), 0.08),
            "oos_mdd": _as_float(raw.get("oos_mdd"), 9000.0),
        }
    return {
        "oos_periods": [
            {"start": "2024-01-01", "end": "2024-03-31", "return": 0.041, "sharpe": 1.08, "max_drawdown": 8200},
            {"start": "2024-04-01", "end": "2024-06-30", "return": 0.037, "sharpe": 1.16, "max_drawdown": 7900},
        ],
        "oos_sharpe": 1.12,
        "oos_return": 0.078,
        "oos_mdd": 8200.0,
    }


def _normalize_wfo_summary(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict) and raw:
        return {
            "rounds": raw.get("rounds", []),
            "avg_sharpe": _as_float(raw.get("avg_sharpe"), 1.0),
            "pass_rate": _as_float(raw.get("pass_rate"), 0.6),
            "stability_score": _as_float(raw.get("stability_score"), 0.7),
        }
    return {
        "rounds": [
            {"round_id": 1, "sharpe": 1.02, "return": 0.022, "max_drawdown": 7200, "passed": True},
            {"round_id": 2, "sharpe": 1.18, "return": 0.031, "max_drawdown": 8400, "passed": True},
            {"round_id": 3, "sharpe": 0.94, "return": 0.015, "max_drawdown": 9800, "passed": False},
        ],
        "avg_sharpe": 1.047,
        "pass_rate": 0.667,
        "stability_score": 0.72,
    }


def _normalize_risk_report(raw: Any) -> dict[str, Any]:
    item = raw if isinstance(raw, dict) else {}
    return {
        "max_dd": _as_float(item.get("max_dd"), 9800.0),
        "ulcer_index": _as_float(item.get("ulcer_index"), 3.8),
        "recovery_days": int(_as_float(item.get("recovery_days"), 16)),
        "volatility": _as_float(item.get("volatility"), 0.21),
        "downside_volatility": _as_float(item.get("downside_volatility"), 0.13),
    }


def _normalize_forward_log(raw: Any, ranking: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = raw if isinstance(raw, list) and raw else _mock_forward_log(ranking[0]["strategy_id"])
    cumulative = 0.0
    normalized = []
    for index, row in enumerate(rows):
        item = row if isinstance(row, dict) else {}
        pnl = _as_float(item.get("pnl"), 50.0 + index * 2.0)
        cumulative = _as_float(item.get("cumulative_pnl"), cumulative + pnl)
        normalized.append(
            {
                "datetime": format_datetime(item.get("datetime") or _mock_dt(index)),
                "strategy_id": str(item.get("strategy_id") or ranking[0]["strategy_id"]),
                "pnl": round(pnl, 4),
                "cumulative_pnl": round(cumulative, 4),
            }
        )
    return normalized


def _normalize_decision_audit(
    raw: Any,
    ranking: list[dict[str, Any]],
    oos_summary: dict[str, Any],
    wfo_summary: dict[str, Any],
    risk_report: dict[str, Any],
) -> dict[str, Any]:
    generated = build_decision_audit(ranking, oos_summary, wfo_summary, risk_report)
    item = raw if isinstance(raw, dict) else {}
    if not item:
        return generated

    merged = dict(generated)
    for key in [
        "baseline_strategy",
        "challenger_strategy",
        "promotion_decision",
        "reason",
        "timestamp",
        "recommend_promote",
        "requires_human_review",
        "score",
        "risk_warnings",
        "checks",
    ]:
        if key in item:
            merged[key] = item[key]

    merged["baseline_strategy"] = str(merged.get("baseline_strategy") or "1001plus_baseline")
    merged["challenger_strategy"] = str(merged.get("challenger_strategy") or ranking[0]["strategy_id"])
    merged["promotion_decision"] = str(merged.get("promotion_decision") or "review_required")
    merged["reason"] = str(merged.get("reason") or generated["reason"])
    merged["timestamp"] = format_datetime(merged.get("timestamp") or datetime(2026, 5, 7, 9, 0, 0))
    return merged


def _mock_ranking() -> list[dict[str, Any]]:
    return [
        {
            "strategy_id": f"1001plus_{index:04d}",
            "score": 125.0 - index * 5.0,
            "annual_return": 0.22 - index * 0.015,
            "sharpe": 1.65 - index * 0.09,
            "max_drawdown": 8500 + index * 1200,
            "trade_count": 360 + index * 24,
            "win_rate": 0.58 - index * 0.01,
            "profit_factor": 1.75 - index * 0.07,
            "robustness_score": 0.82 - index * 0.03,
            "wfo_pass_rate": 0.78 - index * 0.025,
            "oos_sharpe": 1.42 - index * 0.08,
        }
        for index in range(1, 6)
    ]


def _mock_params() -> dict[str, Any]:
    return {
        "baseline": "1001plus",
        "don_len": 72,
        "ema_fast": 5,
        "ema_slow": 34,
        "atr_len": 14,
        "atr_tp_k": 3.5,
        "atr_sl_k": 1.8,
    }


def _mock_cost_model() -> dict[str, Any]:
    return {
        "slippage_points_per_side": 2.0,
        "fee_money_per_side": 0.0,
        "tax_rate": 0.00002,
        "point_value": 50.0,
        "qty": 1,
    }


def _mock_equity_curve() -> list[dict[str, Any]]:
    equity = 100000.0
    peak = equity
    rows = []
    for index in range(220):
        pnl = 88.0 + math.sin(index / 6.0) * 72.0
        if index in {43, 91, 142, 180}:
            pnl -= 540.0
        equity += pnl
        peak = max(peak, equity)
        rows.append(
            {
                "datetime": _mock_dt(index),
                "equity": equity,
                "drawdown": max(0.0, peak - equity),
            }
        )
    return rows


def _mock_trades() -> list[dict[str, Any]]:
    rows = []
    cumulative = 0.0
    for index in range(60):
        pnl = 130.0 + math.sin(index / 3.0) * 85.0
        if index % 10 == 0:
            pnl -= 280.0
        cumulative += pnl
        rows.append(
            {
                "datetime": _mock_dt(index * 2),
                "price": 20300 + index * 7.0,
                "side": "buy" if index % 2 == 0 else "sell",
                "pnl": pnl,
                "cumulative_pnl": cumulative,
            }
        )
    return rows


def _mock_forward_log(strategy_id: str) -> list[dict[str, Any]]:
    rows = []
    cumulative = 0.0
    for index in range(25):
        pnl = 60.0 + math.cos(index / 2.5) * 34.0
        if index in {6, 13, 20}:
            pnl -= 120.0
        cumulative += pnl
        rows.append(
            {
                "datetime": _mock_dt(index),
                "strategy_id": strategy_id,
                "pnl": pnl,
                "cumulative_pnl": cumulative,
            }
        )
    return rows


def _mock_dt(index: int) -> datetime:
    return datetime(2024, 1, 2, 8, 45, 0) + timedelta(days=index)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return number
