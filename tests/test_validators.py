# filename: test_validators.py
"""
Validation unit tests.
Pure logic only — NO DB, NO HTTP, NO TestClient.
"""

import pytest
from unittest.mock import patch
from validation.exceptions import ValidationError
from conftest import make_mock_ds


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


def test_upload_rejects_invalid_dicom(api_client):
    mock_ds = make_mock_ds(modality="MR")
    with patch("main.pydicom.dcmread", return_value=mock_ds):
        response = api_client.post(
            "/upload",
            files={"file": ("test.dcm", b"fake-content", "application/octet-stream")},
        )

    assert response.status_code == 400
    assert "error" in response.json()