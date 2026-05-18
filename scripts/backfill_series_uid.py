"""
scripts/backfill_series_uid.py

一次性修舊資料 — 補 pre-2026-05-15 upload 的 instances 表 series_instance_uid 欄位。

背景：migration e25c80289a9c (2026-05-15) 加 instances.series_instance_uid 欄並讓 upload
pipeline 補寫；但 pre-migration upload 的 instances 仍是 NULL（DB-level orphan、前端
StudyList 看不到）。本 script 重讀 DICOM file 取 SeriesInstanceUID、與現有 series 表
比對後補寫該欄位。

安全機制：
- dry-run 為 default、必須加 --apply 才實際寫入
- 對每個 orphan 重讀 DICOM、確認 SeriesInstanceUID
- 若 SeriesInstanceUID 不在 series 表 → log warning + skip（不自行 create series）
- Apply 後重新 query 驗證 orphan count

使用方式：
    python scripts/backfill_series_uid.py            # dry-run
    python scripts/backfill_series_uid.py --apply    # 實際寫入
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pydicom
from sqlalchemy.exc import SQLAlchemyError

from db import SessionLocal
from models import Instance, Series
from config import settings


def audit_orphans(db):
    """掃 orphan、重讀 DICOM、與 series 表比對；回傳 (plan, skipped) 兩 list。"""
    orphans = (
        db.query(Instance)
        .filter(Instance.series_instance_uid.is_(None))
        .order_by(Instance.id)
        .all()
    )
    if not orphans:
        return [], []

    storage_root = Path(settings.UPLOAD_STORAGE_PATH).resolve()
    existing_series = {s.series_instance_uid for s in db.query(Series).all()}

    plan = []
    skipped = []
    for inst in orphans:
        abs_path = (storage_root / inst.file_path).resolve()
        if not abs_path.exists():
            skipped.append((inst, f"DICOM file missing on disk: {abs_path}"))
            continue
        try:
            ds = pydicom.dcmread(str(abs_path), stop_before_pixels=True)
        except Exception as e:
            skipped.append((inst, f"DICOM read error: {e}"))
            continue
        dicom_series_uid = ds.get("SeriesInstanceUID")
        if not dicom_series_uid:
            skipped.append((inst, "DICOM file missing SeriesInstanceUID tag"))
            continue
        dicom_series_uid = str(dicom_series_uid)
        if dicom_series_uid not in existing_series:
            skipped.append((
                inst,
                f"SeriesInstanceUID {dicom_series_uid} not in series table "
                f"(would need to create series record — skipped for safety; "
                f"re-upload the DICOM via /upload to trigger series upsert)"
            ))
            continue
        plan.append((inst, dicom_series_uid))
    return plan, skipped


def main():
    parser = argparse.ArgumentParser(
        description="Backfill instances.series_instance_uid for pre-2026-05-15 orphan rows."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually execute the UPDATE (default: dry-run).",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        plan, skipped = audit_orphans(db)
        mode = "APPLY" if args.apply else "DRY-RUN"

        print(f"=== {mode} ===")
        print(f"Plan: {len(plan)} instance(s) to backfill, {len(skipped)} skipped\n")

        if plan:
            print("=== Backfill plan ===")
            for inst, series_uid in plan:
                print(f"  Instance id={inst.id} sop={inst.sop_instance_uid}")
                print(f"    file = {inst.file_path}")
                print(f"    -> series_instance_uid = {series_uid}")
        if skipped:
            print("\n=== Skipped ===")
            for inst, reason in skipped:
                print(f"  Instance id={inst.id}: {reason}")

        if not args.apply:
            print("\n[dry-run] No changes made. Re-run with --apply to execute.")
            return 0

        if not plan:
            print("\nNothing to apply.")
            return 0

        print("\n=== Applying ===")
        for inst, series_uid in plan:
            inst.series_instance_uid = series_uid
            db.add(inst)
        db.commit()
        print(f"Updated {len(plan)} instance(s).")

        remaining = (
            db.query(Instance)
            .filter(Instance.series_instance_uid.is_(None))
            .count()
        )
        print("\n=== Post-apply verification ===")
        print(f"Remaining orphan instances: {remaining}")
        if remaining > 0 and not skipped:
            print("WARNING: orphans remain but no skip recorded — unexpected state.")
            return 1
        return 0
    except SQLAlchemyError as e:
        db.rollback()
        print(f"ERROR (SQLAlchemy): {e}")
        return 2
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
