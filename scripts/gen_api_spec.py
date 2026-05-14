"""
scripts/gen_api_spec.py — Auto-generate docs/generated/api_spec.md from FastAPI routes.

DO NOT EDIT THE GENERATED FILE. Re-run this script when main.py changes.

Triggered automatically by scripts/hooks/pre-commit on relevant source changes.

Usage:
    .venv/Scripts/python.exe scripts/gen_api_spec.py
"""
from __future__ import annotations

import inspect
import subprocess
import sys
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.routing import APIRoute  # noqa: E402

from main import app  # noqa: E402

OUTPUT = PROJECT_ROOT / "docs" / "generated" / "api_spec.md"
SOURCE = "main.py"


def get_git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(PROJECT_ROOT),
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def render() -> None:
    git_hash = get_git_head()
    lines: list[str] = [
        "<!-- AUTO-GENERATED — DO NOT EDIT -->",
        f"<!-- Source: {SOURCE} -->",
        "<!-- Generator: scripts/gen_api_spec.py -->",
        f"<!-- Last regenerated against git HEAD: {git_hash} -->",
        "",
        "# API Spec (Generated)",
        "",
        f"> 本檔由 `scripts/gen_api_spec.py` 從 `{SOURCE}` 自動產生。",
        "> **不要人工編輯**。修改 `main.py` 後再次執行（或由 pre-commit hook 自動觸發）。",
        "",
        "**Backend base URL (dev)**: `http://localhost:8000`",
        "",
        "---",
        "",
    ]

    routes = sorted(
        (r for r in app.routes if isinstance(r, APIRoute)),
        key=lambda r: (r.path, sorted(r.methods)),
    )

    for route in routes:
        methods = sorted(route.methods - {"HEAD", "OPTIONS"})
        for method in methods:
            handler = route.endpoint.__name__
            try:
                source_line = inspect.getsourcelines(route.endpoint)[1]
            except (OSError, TypeError):
                source_line = "?"
            doc = (route.endpoint.__doc__ or "").strip()
            if not doc:
                doc = "_(no docstring)_"
            lines.append(f"## `{method} {route.path}`")
            lines.append("")
            lines.append(f"**Handler**: `{SOURCE}:{handler}` (line {source_line})")
            lines.append("")
            lines.append(doc)
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"_Generated {len(routes)} routes._")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Generated {OUTPUT} ({len(routes)} routes)")


if __name__ == "__main__":
    render()
