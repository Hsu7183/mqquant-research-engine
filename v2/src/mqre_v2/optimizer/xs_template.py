from __future__ import annotations

import re
from pathlib import Path

PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def render_xs_template(template_path: str, params: dict) -> str:
    template = Path(template_path).read_text(encoding="utf-8")
    placeholders = set(PLACEHOLDER_PATTERN.findall(template))
    missing = sorted(name for name in placeholders if name not in params)
    if missing:
        raise ValueError(f"missing template parameters: {missing}")

    def replace_placeholder(match: re.Match[str]) -> str:
        name = match.group(1)
        return str(params[name])

    return PLACEHOLDER_PATTERN.sub(replace_placeholder, template)


def write_rendered_xs(template_path: str, params: dict, output_path: str) -> None:
    rendered = render_xs_template(template_path, params)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
