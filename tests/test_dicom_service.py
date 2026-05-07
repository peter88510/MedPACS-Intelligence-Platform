import pytest
import os
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db, storage_service
from models import Base, Patient, Study, Instance
from db_service import DatabaseService

from unittest.mock import patch, MagicMock
from validation.exceptions import ValidationError
from conftest import make_mock_ds

# Use in-memory SQLite for tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for each test."""
    # Setup
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown
    Base.metadata.drop_all(bind=engine)


def test_health_check():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_with_valid_dicom(tmp_path):
    """Test uploading a valid DICOM file."""
    # Create a minimal DICOM file for testing
    import pydicom
    from pydicom.dataset import FileDataset
    from datetime import datetime

    # Create test DICOM
    file_meta = pydicom.dataset.FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
    file_meta.MediaStorageSOPInstanceUID = "1.2.3.4"
    file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian

    ds = FileDataset(
        str(tmp_path / "test.dcm"),
        {},
        file_meta=file_meta,
        preamble=b"\0" * 128,
    )

    ds.PatientID = "TEST_PATIENT_001"
    ds.StudyInstanceUID = "1.2.3.4.5.6.7"
    ds.SOPInstanceUID = "1.2.3.4.5.6.7.8"
    ds.Modality = "US"
    ds.PatientName = "Test^Patient"

    test_file_path = tmp_path / "test.dcm"
    ds.save_as(test_file_path)

    # Upload file
    with open(test_file_path, "rb") as f:
        response = client.post(
            "/upload",
            files={"file": ("test.dcm", f, "application/dicom")}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "TEST_PATIENT_001"
    assert data["study_instance_uid"] == "1.2.3.4.5.6.7"
    assert data["modality"] == "US"


STORAGE_PATH = "./storage"


def test_upload_stores_file_locally(tmp_path):
    """Test that uploaded DICOM is stored locally."""
    import pydicom
    from pydicom.dataset import FileDataset

    file_meta = pydicom.dataset.FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
    file_meta.MediaStorageSOPInstanceUID = "1.2.3.4"
    file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian

    ds = FileDataset(
        str(tmp_path / "test2.dcm"),
        {},
        file_meta=file_meta,
        preamble=b"\0" * 128,
    )

    ds.PatientID = "STORAGE_TEST"
    ds.StudyInstanceUID = "1.2.3.4.5.6.8"
    ds.Modality = "US"

    test_file_path = tmp_path / "test2.dcm"
    ds.save_as(test_file_path)

    with open(test_file_path, "rb") as f:
        response = client.post(
            "/upload",
            files={"file": ("test2.dcm", f, "application/dicom")}
        )

    assert response.status_code == 200

    # Check if file exists in storage
    expected_path = Path(STORAGE_PATH) / "STORAGE_TEST" / "1.2.3.4.5.6.8" / "test2.dcm"
    assert expected_path.exists(), f"File not found at {expected_path}"


def test_database_upsert_patient():
    """Test patient upsert in database."""
    db = TestingSessionLocal()

    # First insert
    patient1 = DatabaseService.upsert_patient(db, "PATIENT_001")
    assert patient1.patient_id == "PATIENT_001"

    # Second insert (should return same)
    patient2 = DatabaseService.upsert_patient(db, "PATIENT_001")
    assert patient2.id == patient1.id
    assert patient2.patient_id == patient1.patient_id

    db.close()


def test_database_upsert_study():
    """Test study upsert in database."""
    db = TestingSessionLocal()

    # Create patient first
    patient = DatabaseService.upsert_patient(db, "PATIENT_002")

    # Create study
    study = DatabaseService.upsert_study(
        db,
        study_instance_uid="1.2.3.4",
        patient_id="PATIENT_002",
        modality="CT"
    )

    assert study.study_instance_uid == "1.2.3.4"
    assert study.patient_id == "PATIENT_002"
    assert study.modality == "CT"

    db.close()


def test_database_create_instance():
    """Test instance creation in database."""
    db = TestingSessionLocal()

    # Setup patient and study
    DatabaseService.upsert_patient(db, "PATIENT_003")
    DatabaseService.upsert_study(
        db,
        study_instance_uid="1.2.3.5",
        patient_id="PATIENT_003"
    )

    # Create instance
    instance = DatabaseService.create_instance(
        db,
        file_path="PATIENT_003/1.2.3.5/file.dcm",
        study_instance_uid="1.2.3.5",
        sop_instance_uid="1.2.3.5.1"
    )

    assert instance.file_path == "PATIENT_003/1.2.3.5/file.dcm"
    assert instance.study_instance_uid == "1.2.3.5"

    db.close()


# ── Validation Layer Tests ──────────────────────────────────


def test_valid_us_dicom_passes():
    """Valid US DICOM should raise nothing."""
    from validation.dicom_validator import validate_dicom
    ds = make_mock_ds()
    validate_dicom(ds)  # no exception = pass


def test_missing_patient_id_rejected():
    """Empty PatientID should raise ValidationError."""
    from validation.dicom_validator import validate_dicom
    ds = make_mock_ds(patient_id="")
    with pytest.raises(ValidationError, match="PatientID"):
        validate_dicom(ds)


def test_missing_study_uid_rejected():
    """Empty StudyInstanceUID should raise ValidationError."""
    from validation.dicom_validator import validate_dicom
    ds = make_mock_ds(study_uid="")
    with pytest.raises(ValidationError, match="StudyInstanceUID"):
        validate_dicom(ds)


def test_missing_modality_rejected():
    """Empty Modality should raise ValidationError."""
    from validation.dicom_validator import validate_dicom
    ds = make_mock_ds(modality="")
    with pytest.raises(ValidationError, match="Modality"):
        validate_dicom(ds)


def test_non_us_modality_rejected():
    """Modality CT should be rejected."""
    from validation.dicom_validator import validate_dicom
    ds = make_mock_ds(modality="CT")
    with pytest.raises(ValidationError, match="CT"):
        validate_dicom(ds)


def test_upload_rejects_invalid_dicom():
    """
    /upload with a non-US DICOM should return 400.
    Patches dcmread to return a controlled dataset.
    Requires a `client` fixture (FastAPI TestClient).
    """
    mock_ds = make_mock_ds(modality="MR")

    with patch("main.pydicom.dcmread", return_value=mock_ds):
        response = client.post(
            "/upload",
            files={"file": ("test.dcm", b"fake-content", "application/octet-stream")},
        )

    assert response.status_code == 400
    assert "error" in response.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
