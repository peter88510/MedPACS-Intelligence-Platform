"""
Test script to create sample DICOM files and test the FastAPI service.
Run the API first: uvicorn main:app --reload
Then in another terminal: python test_dicom_service.py
"""

import os
import pydicom
from pydicom.dataset import Dataset, FileDataset, FileMetaDataset
from datetime import datetime
import requests
import json

# Create test directory
TEST_DIR = "./test_dicom_files"
os.makedirs(TEST_DIR, exist_ok=True)


def create_sample_dicom(filename: str, patient_id: str, modality: str = "CT"):
    """Create a minimal valid DICOM file for testing."""
    file_path = os.path.join(TEST_DIR, filename)

    # Create file meta
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"  # CT Image Storage
    file_meta.MediaStorageSOPInstanceUID = "1.2.3.4.5"
    file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian

    # Create dataset
    ds = FileDataset(
        filename_or_obj=file_path,
        dataset={},
        file_meta=file_meta,
        preamble=b"\0" * 128,
    )

    # Add required DICOM fields
    ds.PatientName = f"Test^{patient_id}"
    ds.PatientID = patient_id
    ds.StudyInstanceUID = "1.2.3.4.5.6.7.8.9"
    ds.SeriesInstanceUID = "1.2.3.4.5.6.7.8.9.1"
    ds.SOPInstanceUID = "1.2.3.4.5.6.7.8.9.1.1"
    ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
    ds.Modality = modality
    ds.PatientAge = "042Y"
    ds.PatientSex = "M"

    ds.save_as(file_path)
    print(f"✓ Created test DICOM: {file_path}")
    return file_path


def test_health_check():
    """Test the health check endpoint."""
    print("\n=== Testing Health Check ===")
    response = requests.get("http://localhost:8000/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200


def test_upload_valid_dicom(file_path: str):
    """Test uploading a valid DICOM file."""
    print(f"\n=== Testing Valid DICOM Upload ===")
    print(f"File: {file_path}")

    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post("http://localhost:8000/upload", files=files)

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert response.json()["PatientID"] is not None


def test_upload_invalid_extension():
    """Test uploading a file with invalid extension."""
    print("\n=== Testing Invalid File Extension ===")

    # Create a dummy file with .txt extension
    dummy_file = os.path.join(TEST_DIR, "invalid.txt")
    with open(dummy_file, "w") as f:
        f.write("This is not a DICOM file")

    with open(dummy_file, "rb") as f:
        files = {"file": f}
        response = requests.post("http://localhost:8000/upload", files=files)

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 400
    assert "Invalid file format" in response.json()["detail"]

    os.remove(dummy_file)


def test_upload_invalid_dicom():
    """Test uploading a file with .dcm extension but invalid DICOM content."""
    print("\n=== Testing Invalid DICOM Content ===")

    # Create a fake DICOM file with wrong content
    fake_dcm = os.path.join(TEST_DIR, "fake.dcm")
    with open(fake_dcm, "wb") as f:
        f.write(b"This is not valid DICOM content")

    with open(fake_dcm, "rb") as f:
        files = {"file": f}
        response = requests.post("http://localhost:8000/upload", files=files)

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 422
    assert "not a valid DICOM file" in response.json()["detail"]

    os.remove(fake_dcm)


def test_upload_empty_file():
    """Test uploading an empty .dcm file."""
    print("\n=== Testing Empty File ===")

    empty_file = os.path.join(TEST_DIR, "empty.dcm")
    open(empty_file, "w").close()  # Create empty file

    with open(empty_file, "rb") as f:
        files = {"file": f}
        response = requests.post("http://localhost:8000/upload", files=files)

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 400

    os.remove(empty_file)


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("DICOM Upload Service - Integration Tests")
    print("=" * 60)
    print("\nMake sure the FastAPI service is running:")
    print("  uvicorn main:app --reload")
    print()

    try:
        # Create test DICOM files
        print("Creating test DICOM files...")
        dcm1 = create_sample_dicom("patient_001.dcm", "12345", "CT")
        dcm2 = create_sample_dicom("patient_002.dcm", "67890", "MR")

        # Run tests
        test_health_check()
        test_upload_valid_dicom(dcm1)
        test_upload_valid_dicom(dcm2)
        test_upload_invalid_extension()
        test_upload_invalid_dicom()
        test_upload_empty_file()

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to http://localhost:8000")
        print("Make sure the FastAPI service is running:")
        print("  uvicorn main:app --reload")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    run_all_tests()
