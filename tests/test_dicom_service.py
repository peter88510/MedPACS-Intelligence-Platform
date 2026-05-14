import pytest
import os
import tempfile
from pathlib import Path

from main import app, get_db, storage_service
from db_service import DatabaseService
from unittest.mock import patch, MagicMock
from validation.exceptions import ValidationError
from conftest import make_mock_ds


def test_health_check(db_client):
    """Test health endpoint."""
    response = db_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_with_valid_dicom(tmp_path, db_client):
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
    ds.SeriesInstanceUID = "1.2.3.4.5.6.7.1"
    ds.SOPInstanceUID = "1.2.3.4.5.6.7.8"
    ds.Modality = "US"
    ds.PatientName = "Test^Patient"
    # Minimum image metadata to satisfy validator + pydicom save_as.
    ds.Rows = 1
    ds.Columns = 1
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelData = b"\x00"

    test_file_path = tmp_path / "test.dcm"
    ds.save_as(test_file_path)

    # Upload file
    with open(test_file_path, "rb") as f:
        response = db_client.post(
            "/upload",
            files={"file": ("test.dcm", f, "application/dicom")}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "TEST_PATIENT_001"
    assert data["study_instance_uid"] == "1.2.3.4.5.6.7"
    assert data["modality"] == "US"
    assert isinstance(data["instance_id"], int) and data["instance_id"] > 0


def test_upload_stores_file_locally(tmp_path, monkeypatch, db_client):
    """Test that uploaded DICOM is stored locally (CI-safe, isolated)."""
    import pydicom
    from pydicom.dataset import FileDataset
    # ✅ 將 storage 環境變數重導向至 tmp_path
    monkeypatch.setenv("STORAGE_PATH", str(tmp_path))

    # ✅ 同步覆寫 storage_service 所使用的實際路徑
    monkeypatch.setattr(storage_service, "base_path", tmp_path)

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
    ds.SeriesInstanceUID = "1.2.3.4.5.6.8.1"
    ds.SOPInstanceUID = "1.2.3.4.5.6.8.1.1"
    ds.Modality = "US"
    # Minimum image metadata to satisfy validator + pydicom save_as.
    ds.Rows = 1
    ds.Columns = 1
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelData = b"\x00"

    test_file_path = tmp_path / "test2.dcm"
    ds.save_as(test_file_path)

    with open(test_file_path, "rb") as f:
        response = db_client.post(
            "/upload",
            files={"file": ("test2.dcm", f, "application/dicom")}
        )

    assert response.status_code == 200

    # Check if file exists in storage
    expected_path = tmp_path / "STORAGE_TEST" / "1.2.3.4.5.6.8" / "test2.dcm"
    assert expected_path.exists(), f"File not found at {expected_path}"


def test_database_upsert_patient(db):
    """Test patient upsert in database."""

    # First insert
    patient1 = DatabaseService.upsert_patient(db, "PATIENT_001")
    assert patient1.patient_id == "PATIENT_001"

    # Second insert (should return same)
    patient2 = DatabaseService.upsert_patient(db, "PATIENT_001")
    assert patient2.id == patient1.id
    assert patient2.patient_id == patient1.patient_id


def test_database_upsert_study(db):
    """Test study upsert in database."""

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


def test_database_create_instance(db):
    """Test instance creation in database."""

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
