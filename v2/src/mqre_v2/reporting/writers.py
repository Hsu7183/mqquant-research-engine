from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Any


def write_oos_result_json(result: Mapping[str, Any], output_dir: str | Path) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    target = output_path / "oos_result.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return target
