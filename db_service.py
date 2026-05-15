from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import insert, update
from models import Patient, Study, Instance, Series


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
            series_instance_uid: Optional[str] = None
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

        Returns:
            Instance object
        """
        instance = Instance(
            file_path=file_path,
            study_instance_uid=study_instance_uid,
            sop_instance_uid=sop_instance_uid,
            series_instance_uid=series_instance_uid
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
