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
    def create_instance(
        db: Session,
        file_path: str,
        study_instance_uid: str,
        sop_instance_uid: Optional[str] = None
    ) -> Instance:
        """
        Create instance record (always new, never update).

        Args:
            db: SQLAlchemy session
            file_path: Relative file path from storage
            study_instance_uid: StudyInstanceUID (FK reference)
            sop_instance_uid: Optional SOPInstanceUID from DICOM

        Returns:
            Instance object
        """
        instance = Instance(
            file_path=file_path,
            study_instance_uid=study_instance_uid,
            sop_instance_uid=sop_instance_uid
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