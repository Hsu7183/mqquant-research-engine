from __future__ import annotations

import argparse
import json
from datetime import date
from typing import Sequence

from mqre_v2.automation.auto_research import AutoResearchConfig, run_auto_research


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    summary = run_auto_research(
        AutoResearchConfig(
            txt_folder=args.txt_folder,
            start_date=args.start_date,
            end_date=args.end_date,
            output_json_path=args.output_json_path,
            forward_log_path=args.forward_log_path,
            top_n=args.top_n,
            auto_add_top1_to_forward=not args.no_auto_forward,
            min_score_to_forward=args.min_score_to_forward,
        )
    )
    print(json.dumps(summary, ensure_ascii=False, allow_nan=False))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run mqquant auto research pipeline.")
    parser.add_argument("--txt-folder", required=True)
    parser.add_argument("--start-date", required=True, type=_parse_date)
    parser.add_argument("--end-date", required=True, type=_parse_date)
    parser.add_argument("--output-json-path", required=True)
    parser.add_argument("--forward-log-path", required=True)
    parser.add_argument("--top-n", default=10, type=int)
    parser.add_argument("--min-score-to-forward", default=0.0, type=float)
    parser.add_argument("--no-auto-forward", action="store_true")
    return parser


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid date: {value}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
