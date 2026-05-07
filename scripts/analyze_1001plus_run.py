from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RANKING_PATH = ROOT / "runs" / "latest" / "ranking.json"
DECISION_AUDIT_PATH = ROOT / "runs" / "latest" / "decision_audit.json"
OUTPUT_PATH = ROOT / "docs" / "strategy" / "1001plus_300_run_analysis_20260507.md"

STRATEGY_RE = re.compile(
    r"^1001plus_"
    r"ES(?P<ES>\d+)_"
    r"EL(?P<EL>\d+)_"
    r"RL(?P<RL>\d+)_"
    r"RS(?P<RS>\d+)_"
    r"AS(?P<AS>\d+(?:p\d+)?)_"
    r"AT(?P<AT>\d+(?:p\d+)?)_"
    r"D(?P<D>\d+)_"
    r"VW(?P<VW>[01])$"
)


def main() -> int:
    ranking = _load_json(RANKING_PATH)
    decision_audit = _load_json(DECISION_AUDIT_PATH)
    if not isinstance(ranking, list) or not ranking:
        raise ValueError(f"ranking must be a non-empty list: {RANKING_PATH}")
    if not isinstance(decision_audit, dict):
        raise ValueError(f"decision audit must be an object: {DECISION_AUDIT_PATH}")

    top10 = ranking[:10]
    parsed_params = [_parse_strategy_id(str(row["strategy_id"])) for row in top10]
    report = build_report(top10, parsed_params, decision_audit)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")

    print(f"wrote {OUTPUT_PATH.relative_to(ROOT)}")
    return 0


def build_report(
    top10: list[dict[str, Any]],
    parsed_params: list[dict[str, float | int]],
    decision_audit: dict[str, Any],
) -> str:
    checks = decision_audit.get("checks", {})
    risk_warnings = decision_audit.get("risk_warnings", [])
    lines = [
        "# 1001plus 300-Run Analysis",
        "",
        "## 1. Decision Rejection Reason",
        "",
        f"- challenger: `{decision_audit.get('challenger_strategy', '')}`",
        f"- promotion_decision: `{decision_audit.get('promotion_decision', '')}`",
        f"- reason: `{decision_audit.get('reason', '')}`",
        f"- score: `{decision_audit.get('score', '')}`",
        f"- forward_status: `{decision_audit.get('forward_status', '')}`",
        "",
        "主要 rejection warnings:",
        "",
    ]
    if isinstance(risk_warnings, list) and risk_warnings:
        lines.extend(f"- {warning}" for warning in risk_warnings)
    else:
        lines.append("- 無")

    lines.extend(
        [
            "",
            "Decision checks 摘要:",
            "",
            _checks_table(checks if isinstance(checks, dict) else {}),
            "",
            "## 2. Top10 Ranking Table",
            "",
            "| rank | strategy_id | score | sharpe | max_drawdown | trade_count |",
            "|---:|---|---:|---:|---:|---:|",
        ]
    )
    for index, row in enumerate(top10, start=1):
        lines.append(
            "| "
            f"{index} | "
            f"`{row.get('strategy_id', '')}` | "
            f"{_fmt(row.get('score'))} | "
            f"{_fmt(row.get('sharpe'))} | "
            f"{_fmt(row.get('max_drawdown'))} | "
            f"{row.get('trade_count', '')} |"
        )

    lines.extend(
        [
            "",
            "## 3. Top10 Parameter Distribution",
            "",
            _distribution_table(parsed_params),
            "",
            "VWAP filter 分布:",
            "",
        ]
    )
    vw_counts = Counter(int(params["VW"]) for params in parsed_params)
    lines.append(f"- VW=1: {vw_counts.get(1, 0)}")
    lines.append(f"- VW=0: {vw_counts.get(0, 0)}")

    lines.extend(
        [
            "",
            "## 4. 共同特徵觀察",
            "",
            *_observations(top10, parsed_params, checks if isinstance(checks, dict) else {}),
            "",
            "## 5. 是否建議擴大到 1000 組",
            "",
            _scale_recommendation(decision_audit, parsed_params),
            "",
            "## 6. 下一步建議",
            "",
            "1. 先檢查 `decision_audit.json` 中每個 rejection check，特別是 score、WFO pass rate、PF、risk drawdown。",
            "2. 對 Top10 做參數 plateau 分析，觀察 ES/EL/RS/RL/AS/AT/D 是否集中在狹窄區域。",
            "3. 若要擴大到 1000 組，建議先縮小或重設 generator 範圍，而不是盲目放大。",
            "4. 加入 robustness / plateau score 後，再判斷 challenger 是否值得進入 forward test。",
            "5. baseline 暫不替換；目前 top challenger 只能作為下一輪搜尋線索。",
            "",
        ]
    )
    return "\n".join(lines)


def _load_json(path: Path) -> Any:
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_strategy_id(strategy_id: str) -> dict[str, float | int]:
    match = STRATEGY_RE.match(strategy_id)
    if not match:
        raise ValueError(f"unsupported 1001plus strategy_id: {strategy_id}")
    groups = match.groupdict()
    return {
        "ES": int(groups["ES"]),
        "EL": int(groups["EL"]),
        "RL": int(groups["RL"]),
        "RS": int(groups["RS"]),
        "AS": _parse_float_token(groups["AS"]),
        "AT": _parse_float_token(groups["AT"]),
        "D": int(groups["D"]),
        "VW": int(groups["VW"]),
    }


def _parse_float_token(value: str) -> float:
    return float(value.replace("p", "."))


def _distribution_table(parsed_params: list[dict[str, float | int]]) -> str:
    lines = [
        "| param | min | max | avg | values |",
        "|---|---:|---:|---:|---|",
    ]
    for key in ["ES", "EL", "RL", "RS", "AS", "AT", "D"]:
        values = [float(params[key]) for params in parsed_params]
        unique = ", ".join(_fmt(value) for value in sorted(set(values)))
        lines.append(
            f"| {key} | {_fmt(min(values))} | {_fmt(max(values))} | {_fmt(mean(values))} | {unique} |"
        )
    return "\n".join(lines)


def _checks_table(checks: dict[str, Any]) -> str:
    rows: list[tuple[str, str, str]] = []
    for section, payload in checks.items():
        if isinstance(payload, dict):
            for key, value in payload.items():
                rows.append((str(section), str(key), str(value)))
    if not rows:
        return "無 decision checks。"

    lines = [
        "| section | key | value |",
        "|---|---|---:|",
    ]
    for section, key, value in rows:
        lines.append(f"| {section} | {key} | {value} |")
    return "\n".join(lines)


def _observations(
    top10: list[dict[str, Any]],
    parsed_params: list[dict[str, float | int]],
    checks: dict[str, Any],
) -> list[str]:
    es_avg = mean(float(params["ES"]) for params in parsed_params)
    el_avg = mean(float(params["EL"]) for params in parsed_params)
    rl_avg = mean(float(params["RL"]) for params in parsed_params)
    rs_avg = mean(float(params["RS"]) for params in parsed_params)
    as_avg = mean(float(params["AS"]) for params in parsed_params)
    at_avg = mean(float(params["AT"]) for params in parsed_params)
    d_avg = mean(float(params["D"]) for params in parsed_params)
    vw_counts = Counter(int(params["VW"]) for params in parsed_params)
    score_values = [float(row.get("score", 0.0)) for row in top10]
    drawdown_values = [float(row.get("max_drawdown", 0.0)) for row in top10]
    trade_counts = [int(row.get("trade_count", 0)) for row in top10]
    wfo = checks.get("wfo", {}) if isinstance(checks.get("wfo"), dict) else {}

    return [
        f"- Top10 的 EMA short 平均約 {es_avg:.2f}，EMA long 平均約 {el_avg:.2f}，偏向短 EMA 搭配中長週期趨勢濾網。",
        f"- RSI long threshold 平均約 {rl_avg:.2f}，RSI short threshold 平均約 {rs_avg:.2f}，Top10 偏向嚴格多單門檻與偏低空單門檻。",
        f"- ATR stop 平均約 {as_avg:.2f}，ATR take profit 平均約 {at_avg:.2f}，停利倍數明顯高於停損倍數。",
        f"- Donchian period 平均約 {d_avg:.2f}，Top10 多集中在中長 breakout lookback。",
        f"- VWAP filter：VW=1 有 {vw_counts.get(1, 0)} 組，VW=0 有 {vw_counts.get(0, 0)} 組，Top10 並未完全依賴 VWAP filter。",
        f"- Top10 score 範圍為 {min(score_values):.4f} 到 {max(score_values):.4f}，整體距離 promotion threshold 仍很遠。",
        f"- Top10 max_drawdown 範圍為 {min(drawdown_values):.4f} 到 {max(drawdown_values):.4f}，風險端仍需壓低。",
        f"- Top10 trade_count 範圍為 {min(trade_counts)} 到 {max(trade_counts)}，交易數足夠，但品質與穩健性不足。",
        f"- WFO pass_rate = {wfo.get('pass_rate', '')}，是本次 reject 的核心訊號之一。",
    ]


def _scale_recommendation(
    decision_audit: dict[str, Any],
    parsed_params: list[dict[str, float | int]],
) -> str:
    decision = str(decision_audit.get("promotion_decision", ""))
    score = float(decision_audit.get("score", 0.0))
    vw_counts = Counter(int(params["VW"]) for params in parsed_params)
    if decision == "reject" and score < 20:
        return (
            "暫不建議直接擴大到 1000 組。這次 Top1 score 仍明顯低於升級門檻，"
            "應先檢查 rejection checks 與 Top10 參數共通區域，再調整 generator 範圍。"
        )
    if vw_counts.get(1, 0) == 0 or vw_counts.get(0, 0) == 0:
        return (
            "可考慮小幅擴大，但需補足 VWAP filter 開關兩側的樣本，避免搜尋偏向單一結構。"
        )
    return (
        "可考慮擴大，但建議先加入 plateau / robustness 分析，避免只是放大同一批低品質參數區域。"
    )


def _fmt(value: Any) -> str:
    if isinstance(value, int):
        return str(value)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    text = f"{number:.6f}".rstrip("0").rstrip(".")
    return text if text else "0"


if __name__ == "__main__":
    raise SystemExit(main())
