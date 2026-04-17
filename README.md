# DICOM Upload Service

A minimal, production-ready FastAPI service for uploading and parsing DICOM files.

## Features

- ✅ POST `/upload` endpoint for single DICOM file upload
- ✅ Validates `.dcm` file extension
- ✅ Extracts key metadata: PatientID, StudyInstanceUID, Modality
- ✅ In-memory processing (no persistence)
- ✅ Comprehensive error handling
- ✅ Structured logging for debugging
- ✅ Health check endpoint GET `/`
- ✅ Clean, modular, production-ready code

## Requirements

- Python 3.10+
- FastAPI
- pydicom
- uvicorn

## Installation

```bash
pip install -r requirements.txt
```

## Running the Service

### Development mode (with auto-reload):
```bash
uvicorn main:app --reload
```

### Production mode:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The service will be available at `http://localhost:8000`

## API Endpoints

### Health Check
```
GET /
```

**Response:**
```json
{
  "status": "healthy",
  "service": "DICOM Upload Service"
}
```

### Upload DICOM File
```
POST /upload
Content-Type: multipart/form-data

file: <binary DICOM file>
```

**Successful Response (200):**
```json
{
  "PatientID": "12345",
  "StudyInstanceUID": "1.2.3.4.5.6.7",
  "Modality": "CT"
}
```

**Error Responses:**
- **400 Bad Request** – Invalid file extension (not .dcm) or empty file
- **422 Unprocessable Entity** – File is not valid DICOM or parsing failed

## Testing with cURL

### Health check:
```bash
curl http://localhost:8000/
```

### Upload a DICOM file:
```bash
curl -X POST -F "file=@path/to/file.dcm" http://localhost:8000/upload
```

### With a test DICOM file (using pydicom to create one):
```python
import pydicom
from pydicom.dataset import Dataset, FileDataset
from datetime import datetime
import os

# Create a minimal valid DICOM file
file_meta = Dataset()
file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
file_meta.MediaStorageSOPInstanceUID = '1.2.3.4.5'
file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian

ds = FileDataset(
    filename="test.dcm",
    dataset={},
    file_meta=file_meta,
    preamble=b"\0" * 128,
)

ds.PatientName = "Test^Patient"
ds.PatientID = "12345"
ds.StudyInstanceUID = "1.2.3.4.5.6.7"
ds.Modality = "CT"
ds.SeriesInstanceUID = "1.2.3.4.5.6.7.8"
ds.SOPInstanceUID = "1.2.3.4.5"
ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.2'

ds.save_as("test.dcm")
```

Then upload:
```bash
curl -X POST -F "file=@test.dcm" http://localhost:8000/upload
```

## Code Structure

- **`main.py`** – Single-file FastAPI application containing:
  - `DicomMetadata` – Data class for parsed metadata
  - `validate_dcm_extension()` – File extension validation
  - `parse_dicom_file()` – DICOM parsing logic
  - Route handlers: `health_check()`, `upload_dicom()`
  - Logging configuration

## Error Handling

| Scenario | Status | Response |
|----------|--------|----------|
| File extension not `.dcm` | 400 | "Invalid file format" |
| Empty file | 400 | "File is empty" |
| Invalid DICOM format | 422 | "File is not a valid DICOM file" |
| Parsing error | 422 | Error details |
| Missing metadata field | 200 | Field set to `null` |

## Logging

All operations are logged with timestamps and levels (INFO, WARNING, ERROR). Check console output for debugging:

```
2024-01-15 10:23:45,123 - __main__ - INFO - Received upload request for file: scan.dcm
2024-01-15 10:23:45,456 - __main__ - INFO - Successfully parsed DICOM: PatientID=12345, StudyInstanceUID=1.2.3.4.5.6.7, Modality=CT
2024-01-15 10:23:45,789 - __main__ - INFO - Successfully processed DICOM file: scan.dcm
```

## Design Decisions

1. **Single file** – All code in `main.py` for simplicity; easy to refactor into modules later
2. **In-memory processing** – No disk writes; file read directly into bytes
3. **Optional metadata fields** – Missing fields return as `null` rather than erroring
4. **Structured logging** – Replaces print statements; better for production
5. **Comprehensive error handling** – Explicit HTTP status codes with descriptive messages
6. **No database** – No persistence layer; ephemeral in-memory only
7. **Minimal dependencies** – Only FastAPI, uvicorn, python-multipart, pydicom

## Performance Notes

- Handles file size up to FastAPI's default upload limit (~1GB)
- In-memory processing suitable for typical DICOM files (2-50 MB)
- For very large files or high concurrency, consider:
  - Streaming to disk before parsing
  - Async worker pool with celery
  - Kubernetes horizontal scaling

## Future Enhancements (Optional)

- Extract additional metadata fields (PatientAge, PatientSex, etc.)
- Async DICOM parsing with thread pool
- Database persistence with SQLAlchemy
- Batch upload endpoint
- DICOM validation/compliance checking
- Image pixel data extraction
- Support for DICOM series/studies
- Authentication/authorization
