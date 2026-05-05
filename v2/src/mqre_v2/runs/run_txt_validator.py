from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from mqre_v2.io.txt_parser import parse_xs_txt
from mqre_v2.runs.run_manager import load_manifest, write_manifest


@dataclass(frozen=True)
class RunTxtValidationResult:
    run_id: str
    total_xs: int
    total_txt: int
    matched: int
    missing_txt: list[str]
    extra_txt: list[str]
    parse_failed: list[str]
    valid_txt: list[str]


def validate_run_txt(run_path: str) -> RunTxtValidationResult:
    manifest = load_manifest(run_path)
    root = Path(run_path)
    xs_dir = root / "xs"
    txt_dir = root / "txt"

    xs_files = sorted(xs_dir.glob("*.xs")) if xs_dir.exists() else []
    txt_files = sorted(txt_dir.glob("*.txt")) if txt_dir.exists() else []

    xs_by_stem = {path.stem: path for path in xs_files}
    txt_by_stem = {path.stem: path for path in txt_files}

    xs_stems = set(xs_by_stem)
    txt_stems = set(txt_by_stem)
    matched_stems = sorted(xs_stems & txt_stems)
    missing_stems = sorted(xs_stems - txt_stems)
    extra_stems = sorted(txt_stems - xs_stems)

    parse_failed: list[str] = []
    valid_txt: list[str] = []
    for stem in matched_stems:
        txt_path = txt_by_stem[stem]
        try:
            parse_xs_txt(txt_path.read_text(encoding="utf-8-sig"))
        except Exception:
            parse_failed.append(txt_path.name)
        else:
            valid_txt.append(txt_path.name)

    result = RunTxtValidationResult(
        run_id=manifest.run_id,
        total_xs=len(xs_files),
        total_txt=len(txt_files),
        matched=len(matched_stems),
        missing_txt=[f"{stem}.txt" for stem in missing_stems],
        extra_txt=[txt_by_stem[stem].name for stem in extra_stems],
        parse_failed=parse_failed,
        valid_txt=valid_txt,
    )

    updated_manifest = replace(
        manifest,
        txt_validated=True,
        txt_matched=result.matched,
        txt_missing=len(result.missing_txt),
        txt_parse_failed=len(result.parse_failed),
    )
    write_manifest(run_path, updated_manifest)

    return result
