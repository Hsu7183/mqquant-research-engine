from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    strategy_name: str
    created_at: str
    parameter_grid_path: str
    template_path: str
    total_param_combinations: int
    xs_generated: bool = False
    xs_count: int = 0
    txt_validated: bool = False
    txt_matched: int = 0
    txt_missing: int = 0
    txt_parse_failed: int = 0
    pipeline_completed: bool = False
    pipeline_total: int = 0
    pipeline_valid: int = 0
    notes: str = ""


def create_run_directory(base_dir: str, strategy_name: str) -> str:
    if not strategy_name:
        raise ValueError("strategy_name cannot be empty")

    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    date_prefix = datetime.now().strftime("%Y%m%d")
    run_prefix = f"{date_prefix}_{strategy_name}_batch"
    next_index = _next_batch_index(base_path, run_prefix)
    run_id = f"{run_prefix}{next_index:03d}"
    run_path = base_path / run_id

    for dirname in ["xs", "txt", "reports", "logs"]:
        (run_path / dirname).mkdir(parents=True, exist_ok=True)

    return str(run_path)


def write_manifest(run_path: str, manifest: RunManifest) -> None:
    target = Path(run_path) / "manifest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(asdict(manifest), handle, ensure_ascii=False, indent=2)


def load_manifest(run_path: str) -> RunManifest:
    source = Path(run_path) / "manifest.json"
    with source.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    return RunManifest(
        run_id=str(payload["run_id"]),
        strategy_name=str(payload["strategy_name"]),
        created_at=str(payload["created_at"]),
        parameter_grid_path=str(payload["parameter_grid_path"]),
        template_path=str(payload["template_path"]),
        total_param_combinations=int(payload["total_param_combinations"]),
        xs_generated=bool(payload.get("xs_generated", False)),
        xs_count=int(payload.get("xs_count", 0)),
        txt_validated=bool(payload.get("txt_validated", False)),
        txt_matched=int(payload.get("txt_matched", 0)),
        txt_missing=int(payload.get("txt_missing", 0)),
        txt_parse_failed=int(payload.get("txt_parse_failed", 0)),
        pipeline_completed=bool(payload.get("pipeline_completed", False)),
        pipeline_total=int(payload.get("pipeline_total", 0)),
        pipeline_valid=int(payload.get("pipeline_valid", 0)),
        notes=str(payload.get("notes", "")),
    )


def _next_batch_index(base_path: Path, run_prefix: str) -> int:
    pattern = re.compile(rf"^{re.escape(run_prefix)}(\d{{3}})$")
    existing_indexes = []
    for path in base_path.iterdir():
        if not path.is_dir():
            continue
        match = pattern.match(path.name)
        if match:
            existing_indexes.append(int(match.group(1)))

    if not existing_indexes:
        return 1
    return max(existing_indexes) + 1
