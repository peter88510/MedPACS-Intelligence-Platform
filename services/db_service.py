from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import insert, update
from models import Patient, Study, Instance, Series, AIResult


class DatabaseService:
    """Handle database operations for DICOM metadata."""

    @staticmethod
    def upsert_patient(db: Session, patient_id: str) -> Patient:
        """
        Upsert patient record. If exists, return existing; if not, create.

        Args:
            db: SQLAlchemy session
            patient_id: PatientID from DICOM

        Returns:
            Patient object
        """
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            patient = Patient(patient_id=patient_id)
            db.add(patient)
            db.commit()
            db.refresh(patient)
        return patient

    @staticmethod
    def upsert_study(
            db: Session,
            study_instance_uid: str,
            patient_id: str,
            modality: Optional[str] = None
    ) -> Study:
        """
        Upsert study record.

        Args:
            db: SQLAlchemy session
            study_instance_uid: StudyInstanceUID from DICOM
            patient_id: PatientID (FK reference)
            modality: Optional modality from DICOM

        Returns:
            Study object
        """
        study = db.query(Study).filter(Study.study_instance_uid == study_instance_uid).first()
        if not study:
            study = Study(
                study_instance_uid=study_instance_uid,
                patient_id=patient_id,
                modality=modality
            )
            db.add(study)
            db.commit()
            db.refresh(study)
        return study

    @staticmethod
    def upsert_series(
            db: Session,
            series_instance_uid: str,
            study_instance_uid: str
    ) -> Series:
        """
        Upsert series record. If exists (matched by series_instance_uid), return existing;
        if not, create. Multiple instances within the same DICOM series will share the
        same series_instance_uid, so this must dedupe on each upload.

        Args:
            db: SQLAlchemy session
            series_instance_uid: SeriesInstanceUID from DICOM
            study_instance_uid: StudyInstanceUID (FK reference, parent study)

        Returns:
            Series object
        """
        series = db.query(Series).filter(Series.series_instance_uid == series_instance_uid).first()
        if not series:
            series = Series(
                series_instance_uid=series_instance_uid,
                study_instance_uid=study_instance_uid
            )
            db.add(series)
            db.commit()
            db.refresh(series)
        return series

    @staticmethod
    def create_instance(
            db: Session,
            file_path: str,
            study_instance_uid: str,
            sop_instance_uid: Optional[str] = None,
            series_instance_uid: Optional[str] = None,
            device_manufacturer: Optional[str] = None,
            device_model: Optional[str] = None
    ) -> Instance:
        """
        Create instance record (always new, never update).

        Args:
            db: SQLAlchemy session
            file_path: Relative file path from storage
            study_instance_uid: StudyInstanceUID (FK reference)
            sop_instance_uid: Optional SOPInstanceUID from DICOM
            series_instance_uid: Optional SeriesInstanceUID (FK to series.series_instance_uid).
                                 Added 2026-05-15 along with Series upsert pipeline.
            device_manufacturer: Optional Manufacturer (0008,0070). Added 2026-06-09 for
                                 the measurement-type resolver (raw, auditable signal).
            device_model: Optional ManufacturerModelName (0008,1090). Added 2026-06-09.

        Returns:
            Instance object
        """
        instance = Instance(
            file_path=file_path,
            study_instance_uid=study_instance_uid,
            sop_instance_uid=sop_instance_uid,
            series_instance_uid=series_instance_uid,
            device_manufacturer=device_manufacturer,
            device_model=device_model
        )
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance


# --- Day 6-7: Query functions ---

def get_all_studies(db: Session) -> list:
    return db.query(Study).order_by(Study.created_at.desc()).all()


def get_series_by_id(db: Session, series_id: int):
    return db.query(Series).filter(Series.id == series_id).first()


def get_instance_by_id(db: Session, instance_id: int):
    return db.query(Instance).filter(Instance.id == instance_id).first()


def get_instance_by_sop_uid(db: Session, sop_instance_uid: str) -> Optional[Instance]:
    """
    Lookup instance by SOPInstanceUID (DICOM-level unique identifier).
    Used by /upload duplicate detection (PROGRESS §6.12).
    """
    return db.query(Instance).filter(Instance.sop_instance_uid == sop_instance_uid).first()


def get_series_by_study_id(db: Session, study_id: int) -> Optional[list]:
    """
    Return all series for a given study DB id. Returns None if study doesn't exist
    (lets handler emit 404); empty list if study exists but has no series yet.
    """
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        return None
    return (db.query(Series)
            .filter(Series.study_instance_uid == study.study_instance_uid)
            .order_by(Series.created_at.asc())
            .all())


def get_instances_by_series_id(db: Session, series_id: int) -> Optional[list]:
    """
    Return all instances for a given series DB id. Returns None if series doesn't exist;
    empty list if series exists but has no instances (e.g., legacy NULL series_instance_uid
    rows from before the 2026-05-15 schema upgrade).
    """
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        return None
    return (db.query(Instance)
            .filter(Instance.series_instance_uid == series.series_instance_uid)
            .order_by(Instance.created_at.asc())
            .all())


# --- Day 8-9: Frontend API support functions ---

def get_instance_file_path(db: Session, instance_id: int):
    instance = db.query(Instance).filter(Instance.id == instance_id).first()
    if not instance:
        return None
    return instance.file_path


def get_instance_metadata(db: Session, instance_id: int):
    instance = db.query(Instance).filter(Instance.id == instance_id).first()
    if not instance:
        return None
    return {k: v for k, v in instance.__dict__.items() if not k.startswith("_")}


# --- Phase 3: AI 結果寫入 / 查詢 ---

def create_ai_result(
    db: Session,
    instance_id: int,
    model_name: str,
    model_version: str,
    status: str,
    measurement_type: str,
    result_json: Optional[dict] = None,
    primary_value: Optional[float] = None,
    primary_unit: Optional[str] = None,
    mask_path: Optional[str] = None,
    confidence: Optional[float] = None,
    error_message: Optional[str] = None,
) -> AIResult:
    """新增一筆 AI 推論結果（always new，每次 /ai/segment 一筆）。

    Args:
        db: SQLAlchemy session
        instance_id: 對應 instances.id（FK）
        model_name / model_version: 引擎識別（audit）
        status: completed / error（與既有欄位語義一致）
        measurement_type: excursion / sniff / thickness / unknown（discriminator）
        result_json: design §4 envelope（JSONB；SQLite 走 JSON variant）
        primary_value / primary_unit: denormalized headline，供 SQL 查詢/排序
        mask_path: 預留（mask PNG 屬下游 §8）
        confidence: 模型信心（與 primary_value 語義不同，各自保留）
        error_message: status=error 時的訊息

    Returns:
        AIResult
    """
    ai_result = AIResult(
        instance_id=instance_id,
        model_name=model_name,
        model_version=model_version,
        status=status,
        measurement_type=measurement_type,
        result_json=result_json,
        primary_value=primary_value,
        primary_unit=primary_unit,
        mask_path=mask_path,
        confidence=confidence,
        error_message=error_message,
    )
    db.add(ai_result)
    db.commit()
    db.refresh(ai_result)
    return ai_result


def get_latest_ai_result_by_instance(
    db: Session, instance_id: int
) -> Optional[AIResult]:
    """取某 instance 最新一筆 AI 結果（依 id 降序）。無結果回 None。"""
    return (
        db.query(AIResult)
        .filter(AIResult.instance_id == instance_id)
        .order_by(AIResult.id.desc())
        .first()
    )
