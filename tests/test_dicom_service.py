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
    DatabaseService.upsert_series(
        db,
        series_instance_uid="1.2.3.5.1",
        study_instance_uid="1.2.3.5"
    )

    # Create instance
    instance = DatabaseService.create_instance(
        db,
        file_path="PATIENT_003/1.2.3.5/file.dcm",
        study_instance_uid="1.2.3.5",
        sop_instance_uid="1.2.3.5.2",
        series_instance_uid="1.2.3.5.1"
    )

    assert instance.file_path == "PATIENT_003/1.2.3.5/file.dcm"
    assert instance.study_instance_uid == "1.2.3.5"
    assert instance.series_instance_uid == "1.2.3.5.1"


def test_database_upsert_series(db):
    """Series upsert dedupes on series_instance_uid (multi-instance series)."""

    # Setup parent study
    DatabaseService.upsert_patient(db, "PATIENT_004")
    DatabaseService.upsert_study(
        db,
        study_instance_uid="1.2.3.6",
        patient_id="PATIENT_004"
    )

    # First insert
    series1 = DatabaseService.upsert_series(
        db,
        series_instance_uid="1.2.3.6.1",
        study_instance_uid="1.2.3.6"
    )
    assert series1.series_instance_uid == "1.2.3.6.1"

    # Second insert with same series_instance_uid — dedupe, return existing
    series2 = DatabaseService.upsert_series(
        db,
        series_instance_uid="1.2.3.6.1",
        study_instance_uid="1.2.3.6"
    )
    assert series2.id == series1.id


def test_upload_creates_series_record(tmp_path, db_client, db):
    """Verify upload pipeline upserts Series (was previously skipped, leaving table empty)."""
    import pydicom
    from pydicom.dataset import FileDataset
    from models import Series

    file_meta = pydicom.dataset.FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
    file_meta.MediaStorageSOPInstanceUID = "1.2.3.4"
    file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian

    ds = FileDataset(
        str(tmp_path / "series_test.dcm"),
        {},
        file_meta=file_meta,
        preamble=b"\0" * 128,
    )
    ds.PatientID = "SERIES_TEST_PATIENT"
    ds.StudyInstanceUID = "9.9.9.9"
    ds.SeriesInstanceUID = "9.9.9.9.1"
    ds.SOPInstanceUID = "9.9.9.9.1.1"
    ds.Modality = "US"
    ds.Rows = 1
    ds.Columns = 1
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelData = b"\x00"

    test_file_path = tmp_path / "series_test.dcm"
    ds.save_as(test_file_path)

    with open(test_file_path, "rb") as f:
        response = db_client.post(
            "/upload",
            files={"file": ("series_test.dcm", f, "application/dicom")}
        )

    assert response.status_code == 200

    # Verify Series record was created with the expected uid
    series = db.query(Series).filter(Series.series_instance_uid == "9.9.9.9.1").first()
    assert series is not None
    assert series.study_instance_uid == "9.9.9.9"


def _build_minimal_dicom(tmp_path, filename, sop_uid, pixel_byte=b"\x00"):
    """Helper: 建一個最小可上傳的 DICOM 寫到 tmp_path，回傳檔案路徑。pixel_byte 用來改變 bytes。"""
    import pydicom
    from pydicom.dataset import FileDataset

    file_meta = pydicom.dataset.FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
    file_meta.MediaStorageSOPInstanceUID = sop_uid
    file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian

    ds = FileDataset(str(tmp_path / filename), {}, file_meta=file_meta, preamble=b"\0" * 128)
    ds.PatientID = "DUP_TEST_PATIENT"
    ds.StudyInstanceUID = "8.8.8.8"
    ds.SeriesInstanceUID = "8.8.8.8.1"
    ds.SOPInstanceUID = sop_uid
    ds.Modality = "US"
    ds.Rows = 1
    ds.Columns = 1
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelData = pixel_byte

    path = tmp_path / filename
    ds.save_as(path)
    return path


def test_upload_duplicate_same_bytes_returns_200_idempotent(tmp_path, monkeypatch, db_client):
    """同 SOP UID + 完全相同 bytes 重傳 → 200 + duplicate=true + 同 instance_id (PROGRESS §6.12)."""
    monkeypatch.setattr(storage_service, "base_path", tmp_path)

    sop_uid = "8.8.8.8.IDEMPOTENT"
    path = _build_minimal_dicom(tmp_path, "dup1.dcm", sop_uid)

    with open(path, "rb") as f:
        r1 = db_client.post("/upload", files={"file": ("dup1.dcm", f, "application/dicom")})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["duplicate"] is False
    first_id = d1["instance_id"]

    # 第二次 — 完全相同 bytes
    with open(path, "rb") as f:
        r2 = db_client.post("/upload", files={"file": ("dup1.dcm", f, "application/dicom")})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["duplicate"] is True
    assert d2["instance_id"] == first_id
    assert "identical content" in d2["message"]


def test_upload_duplicate_different_bytes_returns_409_conflict(tmp_path, monkeypatch, db_client):
    """同 SOP UID + bytes 不同 → 409 + 詳盡 conflict info (PROGRESS §6.12)."""
    monkeypatch.setattr(storage_service, "base_path", tmp_path)

    sop_uid = "8.8.8.8.CONFLICT"
    path_a = _build_minimal_dicom(tmp_path, "ver_a.dcm", sop_uid, pixel_byte=b"\x00")
    path_b = _build_minimal_dicom(tmp_path, "ver_b.dcm", sop_uid, pixel_byte=b"\xff")

    with open(path_a, "rb") as f:
        r1 = db_client.post("/upload", files={"file": ("ver_a.dcm", f, "application/dicom")})
    assert r1.status_code == 200
    first_id = r1.json()["instance_id"]

    with open(path_b, "rb") as f:
        r2 = db_client.post("/upload", files={"file": ("ver_b.dcm", f, "application/dicom")})
    assert r2.status_code == 409
    d2 = r2.json()
    assert d2["existing_instance_id"] == first_id
    assert d2["existing_hash"] != d2["new_hash"]
    assert "suggested_actions" in d2
    assert "save_as_new" in d2["suggested_actions"]


def test_upload_duplicate_existing_file_missing_returns_409(tmp_path, monkeypatch, db_client, db):
    """同 SOP UID 但 storage 上原檔不存在 → 409 + existing_file_missing=true (PROGRESS §6.12 邊角)."""
    from models import Instance, Patient, Study
    monkeypatch.setattr(storage_service, "base_path", tmp_path)

    # 直接在 DB 注入 instance 但不寫對應 file
    db.add(Patient(patient_id="DUP_TEST_PATIENT"))
    db.commit()
    db.add(Study(study_instance_uid="8.8.8.8", patient_id="DUP_TEST_PATIENT", modality="US"))
    db.commit()
    sop_uid = "8.8.8.8.MISSING_FILE"
    db.add(Instance(
        file_path="DUP_TEST_PATIENT/8.8.8.8/nonexistent.dcm",
        study_instance_uid="8.8.8.8",
        sop_instance_uid=sop_uid,
    ))
    db.commit()

    path = _build_minimal_dicom(tmp_path, "reupload.dcm", sop_uid)
    with open(path, "rb") as f:
        r = db_client.post("/upload", files={"file": ("reupload.dcm", f, "application/dicom")})

    assert r.status_code == 409
    d = r.json()
    assert d["existing_file_missing"] is True
    assert "manual cleanup required" in d["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
