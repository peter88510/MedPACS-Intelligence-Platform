"""
scripts/gen_db_schema.py — Auto-generate docs/generated/db_schema.md from SQLAlchemy models.

DO NOT EDIT THE GENERATED FILE. Re-run when models.py or alembic/ changes.

Triggered automatically by scripts/hooks/pre-commit on relevant source changes.

Usage:
    .venv/Scripts/python.exe scripts/gen_db_schema.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models import Base  # noqa: E402

OUTPUT = PROJECT_ROOT / "docs" / "generated" / "db_schema.md"
SOURCE = "models.py + alembic/versions/"


def get_git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(PROJECT_ROOT),
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def get_latest_alembic_rev() -> str:
    versions_dir = PROJECT_ROOT / "alembic" / "versions"
    if not versions_dir.exists():
        return "no migrations"
    revs = [p for p in versions_dir.glob("*.py") if not p.name.startswith("__")]
    if not revs:
        return "no migrations"
    latest = max(revs, key=lambda p: p.stat().st_mtime)
    return latest.name.split("_")[0]


def render() -> None:
    git_hash = get_git_head()
    alembic_rev = get_latest_alembic_rev()
    lines: list[str] = [
        "<!-- AUTO-GENERATED — DO NOT EDIT -->",
        "<!-- Source: models.py + alembic/versions/ -->",
        "<!-- Generator: scripts/gen_db_schema.py -->",
        f"<!-- Last regenerated against git HEAD: {git_hash} / alembic latest: {alembic_rev} -->",
        "",
        "# DB Schema (Generated)",
        "",
        f"> 本檔由 `scripts/gen_db_schema.py` 從 `{SOURCE}` 自動產生。",
        "> **不要人工編輯**。修改 `models.py` 或 alembic migration 後再次執行（或由 pre-commit hook 自動觸發）。",
        "",
        f"**最新 Alembic revision**：`{alembic_rev}`",
        "",
        "---",
        "",
    ]

    for table_name, table in sorted(Base.metadata.tables.items()):
        lines.append(f"## `{table_name}`")
        lines.append("")
        lines.append("| Column | Type | Nullable | PK | Unique | Index | FK |")
        lines.append("|---|---|---|---|---|---|---|")

        unique_cols: set[str] = set()
        indexed_cols: set[str] = set()
        for idx in table.indexes:
            for col in idx.columns:
                indexed_cols.add(col.name)
                if idx.unique:
                    unique_cols.add(col.name)

        for col in table.columns:
            col_type = str(col.type)
            nullable = "yes" if col.nullable else "no"
            pk = "✓" if col.primary_key else ""
            unique = "✓" if (col.unique or col.name in unique_cols) else ""
            indexed = "✓" if (col.index or col.name in indexed_cols) else ""
            fk = ""
            for fk_obj in col.foreign_keys:
                fk = f"→ `{fk_obj.target_fullname}`"
            lines.append(
                f"| `{col.name}` | `{col_type}` | {nullable} | {pk} | {unique} | {indexed} | {fk} |"
            )
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"_Generated {len(Base.metadata.tables)} tables._")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Generated {OUTPUT} ({len(Base.metadata.tables)} tables)")


if __name__ == "__main__":
    render()
