from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RANKING_PATH = ROOT / "runs" / "latest" / "ranking.json"
OUTPUT_PATH = ROOT / "docs" / "strategy" / "1001plus_plateau_analysis_20260507.md"

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

PARAMS = ["ES", "EL", "RL", "RS", "AS", "AT", "D", "VW"]


def main() -> int:
    ranking = _load_ranking(RANKING_PATH)
    selected = _select_plateau_candidates(ranking)
    parsed = [_parse_strategy_id(str(row["strategy_id"])) for row in selected]
    stats = _build_param_stats(parsed)
    verdict = _plateau_verdict(stats)
    report = _build_report(ranking, selected, stats, verdict)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")
    print(f"wrote {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"plateau_exists={verdict['plateau_exists']}")
    print(f"stable_params={','.join(verdict['stable_params'])}")
    return 0


def _load_ranking(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("ranking.json must be a non-empty list")
    return data


def _select_plateau_candidates(ranking: list[dict[str, Any]]) -> list[dict[str, Any]]:
    top20_count = min(20, len(ranking))
    top10pct_count = max(1, math.ceil(len(ranking) * 0.10))
    selected_count = max(top20_count, top10pct_count)
    return ranking[:selected_count]


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
        "AS": _float_token(groups["AS"]),
        "AT": _float_token(groups["AT"]),
        "D": int(groups["D"]),
        "VW": int(groups["VW"]),
    }


def _float_token(value: str) -> float:
    return float(value.replace("p", "."))


def _build_param_stats(parsed: list[dict[str, float | int]]) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}
    for param in PARAMS:
        values = [float(item[param]) for item in parsed]
        unique_values = sorted(set(values))
        param_mean = mean(values)
        param_std = pstdev(values) if len(values) > 1 else 0.0
        min_value = min(values)
        max_value = max(values)
        stats[param] = {
            "mean": param_mean,
            "std": param_std,
            "min": min_value,
            "max": max_value,
            "suggested_range": _suggested_range(param, values),
            "stable": _is_stable(param, values, param_std, min_value, max_value),
            "mode": _mode(values),
            "mode_share": _mode_share(values),
        }
    return stats


def _suggested_range(param: str, values: list[float]) -> str:
    if param == "VW":
        mode_value = int(_mode(values))
        return f"{mode_value}"
    sorted_values = sorted(values)
    low = _percentile(sorted_values, 0.25)
    high = _percentile(sorted_values, 0.75)
    if param in {"ES", "EL", "RL", "RS", "D"}:
        return f"{round(low)}~{round(high)}"
    return f"{_fmt(low)}~{_fmt(high)}"


def _is_stable(
    param: str,
    values: list[float],
    param_std: float,
    min_value: float,
    max_value: float,
) -> bool:
    value_range = max_value - min_value
    if param == "VW":
        return _mode_share(values) >= 0.70
    thresholds = {
        "ES": {"std": 2.0, "range": 5.0},
        "EL": {"std": 8.0, "range": 20.0},
        "RL": {"std": 3.0, "range": 8.0},
        "RS": {"std": 2.0, "range": 5.0},
        "AS": {"std": 0.6, "range": 1.5},
        "AT": {"std": 0.8, "range": 2.0},
        "D": {"std": 8.0, "range": 20.0},
    }
    threshold = thresholds[param]
    return param_std <= threshold["std"] or value_range <= threshold["range"]


def _mode(values: list[float]) -> float:
    counts = Counter(values)
    return counts.most_common(1)[0][0]


def _mode_share(values: list[float]) -> float:
    counts = Counter(values)
    return counts.most_common(1)[0][1] / len(values)


def _percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        raise ValueError("cannot compute percentile of empty values")
    position = (len(sorted_values) - 1) * pct
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return sorted_values[low]
    weight = position - low
    return sorted_values[low] * (1 - weight) + sorted_values[high] * weight


def _plateau_verdict(stats: dict[str, dict[str, Any]]) -> dict[str, Any]:
    stable_params = [param for param, row in stats.items() if bool(row["stable"])]
    unstable_params = [param for param in PARAMS if param not in stable_params]
    plateau_exists = len(stable_params) >= 4
    return {
        "plateau_exists": plateau_exists,
        "stable_params": stable_params,
        "unstable_params": unstable_params,
    }


def _build_report(
    ranking: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    stats: dict[str, dict[str, Any]],
    verdict: dict[str, Any],
) -> str:
    score_min = min(float(row.get("score", 0.0)) for row in selected)
    score_max = max(float(row.get("score", 0.0)) for row in selected)
    lines = [
        "# 1001plus Plateau Analysis",
        "",
        "## Run Scope",
        "",
        f"- source: `runs/latest/ranking.json`",
        f"- total ranking rows: `{len(ranking)}`",
        f"- analyzed rows: `{len(selected)}`",
        f"- selection rule: Top 20 or score top 10%, whichever is larger",
        f"- analyzed score range: `{_fmt(score_min)}` ~ `{_fmt(score_max)}`",
        "",
        "## A. Top20 Table",
        "",
        "| rank | strategy_id | score | sharpe | max_drawdown | trade_count |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(selected[:20], start=1):
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
            "## B. Parameter Distribution",
            "",
            "| param | mean | std | min | max | suggested_range | stable |",
            "|---|---:|---:|---:|---:|---|---|",
        ]
    )
    for param in PARAMS:
        row = stats[param]
        lines.append(
            "| "
            f"{param} | "
            f"{_fmt(row['mean'])} | "
            f"{_fmt(row['std'])} | "
            f"{_fmt(row['min'])} | "
            f"{_fmt(row['max'])} | "
            f"{row['suggested_range']} | "
            f"{'yes' if row['stable'] else 'no'} |"
        )

    lines.extend(
        [
            "",
            "## C. Plateau 判斷",
            "",
            f"- 是否存在穩定區: `{'yes' if verdict['plateau_exists'] else 'no'}`",
            f"- 穩定參數: `{', '.join(verdict['stable_params']) or 'none'}`",
            f"- 發散參數: `{', '.join(verdict['unstable_params']) or 'none'}`",
            "",
            "## D. Interpretation",
            "",
            *_interpretation(stats, verdict),
            "",
            "## E. 建議",
            "",
            *_recommendations(verdict),
            "",
        ]
    )
    return "\n".join(lines)


def _interpretation(
    stats: dict[str, dict[str, Any]],
    verdict: dict[str, Any],
) -> list[str]:
    lines = []
    for param in PARAMS:
        row = stats[param]
        if row["stable"]:
            lines.append(
                f"- `{param}` 出現相對集中區間，建議先觀察 `{row['suggested_range']}`。"
            )
        else:
            lines.append(
                f"- `{param}` 仍偏發散，Top 區域尚未收斂，不宜直接固定。"
            )
    if verdict["plateau_exists"]:
        lines.append("- 綜合判斷：存在初步 plateau，但仍需搭配 WFO / risk rejection checks 驗證。")
    else:
        lines.append("- 綜合判斷：尚未形成足夠穩定 plateau，Top 策略更像單點排序結果。")
    return lines


def _recommendations(verdict: dict[str, Any]) -> list[str]:
    if verdict["plateau_exists"]:
        return [
            "- 不建議直接全範圍擴到 1000 run；建議先針對穩定參數收斂範圍後再跑 300~500 組。",
            "- 對發散參數保留較寬探索範圍，避免過早鎖死。",
            "- 下一輪應加入 plateau score / robustness score，避免只看 Top1。",
            "- 若收斂後仍被 decision audit reject，應優先調整風險與 WFO gate，而不是盲目增加樣本數。",
        ]
    return [
        "- 暫不建議擴到 1000 run；目前 plateau 不明顯。",
        "- 先檢查 generator 範圍是否過寬，並分析 rejection checks 中最嚴重的失敗項。",
        "- 建議先做分桶分析，例如 VW=0 / VW=1、短 EMA / 長 EMA 區間，再決定下一輪搜尋方向。",
        "- baseline 不應被替換，Top challenger 只作為下一輪探索線索。",
    ]


def _fmt(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{number:.6f}".rstrip("0").rstrip(".")


if __name__ == "__main__":
    raise SystemExit(main())
