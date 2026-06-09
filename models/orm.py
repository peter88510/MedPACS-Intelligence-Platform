from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Text, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

# result_json: PostgreSQL stores JSONB (indexable/queryable); the in-memory
# SQLite test engine falls back to text-backed JSON. Keeps the 52-test suite
# green without a Postgres dependency (see .work/ai_result_design.md §3.1).
_JSON_VARIANT = JSONB().with_variant(JSON(), "sqlite")

Base = declarative_base()


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    studies = relationship("Study", back_populates="patient")


class Study(Base):
    __tablename__ = "studies"

    id = Column(Integer, primary_key=True, index=True)
    study_instance_uid = Column(String(255), unique=True, nullable=False, index=True)
    patient_id = Column(String(255), ForeignKey("patients.patient_id"), nullable=False)
    modality = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="studies")
    series = relationship("Series", back_populates="study")
    instances = relationship("Instance", back_populates="study")


class Series(Base):
    __tablename__ = "series"

    id = Column(Integer, primary_key=True, index=True)
    series_instance_uid = Column(String(255), unique=True, nullable=False, index=True)
    study_instance_uid = Column(String(255), ForeignKey("studies.study_instance_uid"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    study = relationship("Study", back_populates="series")
    instances = relationship("Instance", back_populates="series")


class Instance(Base):
    __tablename__ = "instances"

    id = Column(Integer, primary_key=True, index=True)
    sop_instance_uid = Column(String(255), nullable=True, unique=True, index=True)
    file_path = Column(String(500), nullable=False)
    study_instance_uid = Column(String(255), ForeignKey("studies.study_instance_uid"), nullable=False)
    series_instance_uid = Column(String(255), ForeignKey("series.series_instance_uid"), nullable=True, index=True)
    # Device tags (added 2026-06-09): raw, auditable signal captured at upload time
    # for the measurement-type resolver (Manufacturer (0008,0070) / ModelName
    # (0008,1090)). Nullable — legacy rows have no value. See services/measurement_type.py.
    device_manufacturer = Column(String(255), nullable=True)
    device_model = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    study = relationship("Study", back_populates="instances")
    series = relationship("Series", back_populates="instances")
    ai_results = relationship("AIResult", back_populates="instance")


class AIResult(Base):
    __tablename__ = "ai_results"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(Integer, ForeignKey("instances.id"), nullable=False, index=True)
    model_name = Column(String(64), nullable=False)
    model_version = Column(String(32), nullable=False)
    status = Column(String(16), nullable=False)
    mask_path = Column(String(512), nullable=True)
    confidence = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    # Measurement-result fields (added 2026-06-09). The vendored AI is a
    # diaphragm measurement pipeline whose real output is clinical metrics
    # (excursion_cm, ...), not just a mask. result_json holds the full N
    # measurements per run; primary_value/_unit denormalize the headline
    # number for SQL query/sort. See .work/ai_result_design.md §3.1/§4.
    measurement_type = Column(String(32), nullable=False, server_default="excursion")
    result_json = Column(_JSON_VARIANT, nullable=True)
    primary_value = Column(Float, nullable=True)
    primary_unit = Column(String(16), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    instance = relationship("Instance", back_populates="ai_results")
