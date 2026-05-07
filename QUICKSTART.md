---
docspec: "2.0"
type: RUNBOOK
title: "MedDICOMParseAPI v2.0 Quickstart Guide"
version: "2.0.0"
status: "approved"
---

# MedDICOMParseAPI v2.0 Quickstart Guide

Get up and running in 5 minutes.

## Prerequisites

- Python 3.8+
- PostgreSQL installed and running
- pip

## Installation and Setup

### Step 1: Install Dependencies

_Linux/macOS:_

```bash
cd MedPACS Intelligence Platform
pip install -r requirements.txt
```

_Windows:_

```powershell
cd "MedPACS Intelligence Platform"
pip install -r requirements.txt
```

### Step 2: Create PostgreSQL Database

_Linux/macOS:_

```bash
createdb -U postgres -h localhost meddicom_db
```

_Windows:_

```powershell
createdb -U postgres -h 127.0.0.1 meddicom_db
```

### Step 3: Setup Environment Configuration

_Linux/macOS:_

```bash
cp .env.example .env
nano .env
```

_Windows:_

```powershell
# Create .env.example if not exists
@"
# PostgreSQL Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/meddicom_db

# Server Configuration
UPLOAD_STORAGE_PATH=./storage
"@ | Set-Content -Path ".env.example" -Encoding UTF8

# Copy to .env
Copy-Item .env.example .env

# Edit .env
notepad .env
```

Windows CMD alternative:

```cmd
copy .env.example .env
notepad .env
```

### Step 4: Configure Credentials

Edit `.env` and update with your actual PostgreSQL password:

```text
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/meddicom_db
UPLOAD_STORAGE_PATH=./storage
```

Important notes:

- Replace `your_actual_password` with your PostgreSQL password.
- `.env` MUST NOT be committed to version control (add to `.gitignore`).
- `.env.example` SHOULD be committed as a template (contains no secrets).

### Step 5: Verify Database Connection

_Linux/macOS:_

```bash
psql -U postgres -h 127.0.0.1 -d meddicom_db -c "SELECT version();"
```

_Windows:_

```powershell
psql -U postgres -h 127.0.0.1 -d meddicom_db -c "SELECT version();"
```

Expected output: PostgreSQL version information confirming a successful connection.

### Step 6: Run the Server

_Linux/macOS:_

```bash
uvicorn main:app --reload
```

_Windows:_

```powershell
uvicorn main:app --reload
```

Expected output:

```text
INFO:     Uvicorn running on http://127.0.0.1:8000
✓ Database tables initialized
```

## Quick Tests

### Test: Health Check

**Purpose**: Validates that the server is running and reachable, and that the API is reporting the correct version.

**Command**:

_Linux/macOS:_

```bash
curl http://localhost:8000/health
```

_Windows:_

```powershell
curl.exe http://localhost:8000/health
```

**Expected Result**:

HTTP 200 OK

```json
{"status": "ok", "version": "2.0"}
```

Success Condition: The response body contains `"status": "ok"` and `"version": "2.0"`.

**Failure Case**:

- `Connection refused`: The server is not running — start it with `uvicorn main:app --reload`.
- `404`: Incorrect URL or route not registered — verify the server started without errors.

---

### Test: Upload DICOM File

**Purpose**: Validates that a DICOM file can be uploaded, parsed, stored to local disk, and persisted to PostgreSQL, and that the API returns a correctly structured response.

**Command**:

_Linux/macOS:_

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@test_dicom_files/patient_001.dcm"
```

_Windows:_

```powershell
# Option 1: curl.exe
curl.exe -X POST http://localhost:8000/upload -F "file=@test_dicom_files/patient_001.dcm"

# Option 2: Invoke-RestMethod
$form = @{ file = Get-Item -Path "test_dicom_files/patient_001.dcm" }
Invoke-RestMethod -Uri "http://localhost:8000/upload" -Method Post -Form $form
```

**Expected Result**:

HTTP 200 OK

```json
{
  "filename": "patient_001.dcm",
  "patient_id": "...",
  "study_instance_uid": "...",
  "modality": "...",
  "message": "DICOM file uploaded and processed successfully"
}
```

Success Condition: The response body contains `filename`, `patient_id`, `study_instance_uid`, `modality`, and `message` fields with non-empty values.

**Failure Case**:

- `400`: Invalid or malformed DICOM file — verify the file is a valid `.dcm` file.
- `500`: Database error — check PostgreSQL is running and `DATABASE_URL` is correctly set in `.env`.
- `No such file or directory`: The specified DICOM file path does not exist — verify the path to the test file.

---

### Test: List Studies

**Purpose**: Validates that the studies listing endpoint returns a well-formed response after at least one DICOM file has been uploaded.

**Command**:

_Linux/macOS:_

```bash
curl http://localhost:8000/studies
```

_Windows:_

```powershell
curl.exe http://localhost:8000/studies
```

**Expected Result**:

HTTP 200 OK

```json
[
  {
    "id": 1,
    "study_instance_uid": "...",
    "patient_id": "...",
    "modality": "..."
  }
]
```

Success Condition: The response is a JSON array. An empty array (`[]`) is valid when no studies have been uploaded yet.

**Failure Case**:

- `404`: Endpoint not registered — verify the server started without errors and the route exists.
- `500`: Database error — verify PostgreSQL connection and that tables were initialized on startup.

---

### Test: Fetch Series by ID

**Purpose**: Validates that a specific series record can be retrieved by its integer ID.

**Command**:

_Linux/macOS:_

```bash
curl http://localhost:8000/series/1
```

_Windows:_

```powershell
curl.exe http://localhost:8000/series/1
```

**Expected Result**:

HTTP 200 OK

```json
{
  "id": 1,
  "series_instance_uid": "...",
  "study_instance_uid": "..."
}
```

Success Condition: The response body contains a series object with the requested `id`.

**Failure Case**:

- `404`: Series with the given ID does not exist — response shape is `{ "detail": "Series with id 1 not found" }`.
- `500`: Database error — verify PostgreSQL connection.

---

### Test: Fetch Instance by ID

**Purpose**: Validates that a specific DICOM instance record can be retrieved by its integer ID.

**Command**:

_Linux/macOS:_

```bash
curl http://localhost:8000/instances/1
```

_Windows:_

```powershell
curl.exe http://localhost:8000/instances/1
```

**Expected Result**:

HTTP 200 OK

```json
{
  "id": 1,
  "sop_instance_uid": "...",
  "file_path": "...",
  "study_instance_uid": "..."
}
```

Success Condition: The response body contains an instance object with the requested `id`.

**Failure Case**:

- `404`: Instance with the given ID does not exist — response shape is `{ "detail": "Series with id 1 not found" }`.
- `500`: Database error — verify PostgreSQL connection.

---

### Test: Download DICOM Instance File

**Purpose**: Validates that the raw DICOM file for a given instance can be downloaded from the server.

**Command**:

_Linux/macOS:_

```bash
curl http://localhost:8000/instances/1/file --output test.dcm
```

_Windows:_

```powershell
curl.exe http://localhost:8000/instances/1/file --output test.dcm
```

**Expected Result**:

HTTP 200 OK

Success Condition: A file named `test.dcm` is created in the working directory and is a valid DICOM file.

**Failure Case**:

- `404`: Instance ID not found in database, or the file is missing from disk — verify the upload step succeeded and the `./storage` directory is intact.
- `500`: Server-side file read error — check file permissions on the storage directory.

---

### Test: Fetch Instance Metadata

**Purpose**: Validates that parsed DICOM metadata for a given instance can be retrieved as JSON.

**Command**:

_Linux/macOS:_

```bash
curl http://localhost:8000/instances/1/metadata
```

_Windows:_

```powershell
curl.exe http://localhost:8000/instances/1/metadata
```

**Expected Result**:

HTTP 200 OK

```json
{
  "patient_id": "...",
  "study_instance_uid": "...",
  "modality": "..."
}
```

Success Condition: The response body contains a JSON object with DICOM metadata fields.

**Failure Case**:

- `404`: Instance ID not found — verify the instance exists in the database.
- `500`: Metadata extraction error — verify the underlying DICOM file is intact on disk.

---

### Test: Trigger AI Segmentation

**Purpose**: Validates that an AI segmentation job can be queued for a given DICOM instance.

**Command**:

_Linux/macOS:_

```bash
curl -X POST http://localhost:8000/ai/segment/1
```

_Windows:_

```powershell
curl.exe -X POST http://localhost:8000/ai/segment/1
```

**Expected Result**:

HTTP 200 OK

```json
{
  "status": "queued",
  "instance_id": 1
}
```

Success Condition: The response body contains `"status": "queued"` for the requested instance ID.

**Failure Case**:

- `404`: Instance with the given ID does not exist — verify the instance was uploaded and persisted.
- `500`: AI pipeline error — check server logs for details.

---

### Test: Fetch AI Segmentation Result

**Purpose**: Validates that a completed AI segmentation result can be retrieved for a given instance.

**Command**:

_Linux/macOS:_

```bash
curl http://localhost:8000/ai/result/1
```

_Windows:_

```powershell
curl.exe http://localhost:8000/ai/result/1
```

**Expected Result**:

HTTP 200 OK

```json
{
  "instance_id": 1,
  "result": "..."
}
```

Success Condition: The response body contains the AI result for the requested instance ID.

**Failure Case**:

- `404`: No result found for the given instance ID — the segmentation job may not have completed yet.
- `500`: Result retrieval error — check server logs for details.

---

## Platform Compatibility Note

`curl` is available natively on Linux, macOS, and Windows 10/11 (build 1803 and later). On Windows PowerShell, use `curl.exe` explicitly to avoid the `Invoke-WebRequest` alias.

For Windows 7, Windows 8, or Windows Server 2012 (no built-in curl), install [curl for Windows](https://curl.se/windows/) or use PowerShell's native `Invoke-WebRequest`:

```powershell
Invoke-WebRequest -Uri http://localhost:8000/studies | Select-Object -ExpandProperty Content
```

## Verify Data in PostgreSQL

_Linux/macOS:_

```bash
psql -U postgres -d meddicom_db
```

_Windows:_

```powershell
psql -U postgres -d meddicom_db
```

Once connected, run the following queries:

```sql
-- View patients
SELECT id, patient_id, created_at FROM patients;

-- View studies
SELECT id, study_instance_uid, patient_id, modality FROM studies;

-- View instances
SELECT id, file_path, study_instance_uid FROM instances;
```

## Verify Files on Disk

_Linux/macOS:_

```bash
ls -la storage/
```

_Windows:_

```powershell
Get-ChildItem -Path storage\ -Recurse
```

Expected storage directory structure:

```text
storage/
  └── {patient_id}/
      └── {study_instance_uid}/
          └── filename.dcm
```

## Run the Core Test Suite

_Linux/macOS:_

```bash
pytest tests/test_dicom_service.py -v
```

_Windows:_

```powershell
pytest tests/test_dicom_service.py -v
```

Expected output:

```text
test_dicom_service.py::test_health_check PASSED
test_dicom_service.py::test_upload_with_valid_dicom PASSED
test_dicom_service.py::test_upload_stores_file_locally PASSED
test_dicom_service.py::test_database_upsert_patient PASSED
test_dicom_service.py::test_database_upsert_study PASSED
test_dicom_service.py::test_database_create_instance PASSED

====== 6 passed ======
```

## Run the Query API Test Suite

Run individual test classes:

_Linux/macOS:_

```bash
pytest tests/test_query_api.py::TestGetInstanceFile -v
pytest tests/test_query_api.py::TestGetInstanceMetadata -v
pytest tests/test_query_api.py::TestAiSegment -v
pytest tests/test_query_api.py::TestAiResult -v
```

_Windows:_

```powershell
pytest tests/test_query_api.py::TestGetInstanceFile -v
pytest tests/test_query_api.py::TestGetInstanceMetadata -v
pytest tests/test_query_api.py::TestAiSegment -v
pytest tests/test_query_api.py::TestAiResult -v
```

Or run all query API tests together:

_Linux/macOS:_

```bash
pytest tests/test_query_api.py -v
```

_Windows:_

```powershell
pytest tests/test_query_api.py -v
```

Expected output:

```text
collected 16 items

test_query_api.py::TestListStudies::test_returns_empty_list PASSED
test_query_api.py::TestListStudies::test_returns_list_of_studies PASSED
test_query_api.py::TestGetSeries::test_returns_series_when_found PASSED
test_query_api.py::TestGetSeries::test_returns_404_when_not_found PASSED
test_query_api.py::TestGetSeries::test_id_passed_correctly PASSED
test_query_api.py::TestGetInstance::test_returns_instance_when_found PASSED
test_query_api.py::TestGetInstance::test_returns_404_when_not_found PASSED
test_query_api.py::TestGetInstance::test_id_passed_correctly PASSED
test_query_api.py::TestGetInstanceFile::test_returns_file_when_found PASSED
test_query_api.py::TestGetInstanceFile::test_returns_404_when_instance_not_found PASSED
test_query_api.py::TestGetInstanceFile::test_returns_404_when_file_missing_on_disk PASSED
test_query_api.py::TestGetInstanceFile::test_id_passed_correctly PASSED
test_query_api.py::TestGetInstanceMetadata::test_returns_metadata_when_found PASSED
test_query_api.py::TestGetInstanceMetadata::test_returns_404_when_not_found PASSED
test_query_api.py::TestGetInstanceMetadata::test_id_passed_correctly PASSED
test_query_api.py::TestAiSegment::test_returns_queued_status_when_found PASSED
test_query_api.py::TestAiSegment::test_returns_404_when_not_found PASSED
test_query_api.py::TestAiSegment::test_id_passed_correctly PASSED
test_query_api.py::TestAiResult::test_returns_result_when_found PASSED
test_query_api.py::TestAiResult::test_returns_404_when_not_found PASSED
test_query_api.py::TestAiResult::test_id_passed_correctly PASSED

=============================== 21 passed in 0.XXs ===============================
```

## What's New in v2.0

| Feature | v1.0 | v2.0 |
|---|---|---|
| DICOM Upload | Yes | Yes |
| DICOM Parsing | Yes | Yes |
| Local Storage | No | Yes |
| PostgreSQL | No | Yes |
| API Contract | - | Unchanged |

## File Locations After First Upload

```text
MedDICOMParseAPI/
├── main.py
├── storage/                        ← NEW: Local DICOM storage
│   └── P12345/
│       └── 1.2.3.4.5.6.7/
│           └── patient_001.dcm
├── test.db                         ← SQLite (for tests only)
├── .env                            ← Your environment config
└── ...
```

PostgreSQL database `meddicom_db` contains the following tables after first upload:

- `patients`
- `studies`
- `series`
- `instances`

## Common Commands Reference

_Linux/macOS:_

```bash
# Start server
uvicorn main:app --reload

# Run core tests
pytest test_dicom_service.py -v

# Check server health
curl http://localhost:8000/health

# View patients table
psql meddicom_db -c "SELECT * FROM patients;"

# Delete test database
dropdb meddicom_db

# Recreate test database
createdb meddicom_db
```

_Windows:_

```powershell
# Start server
uvicorn main:app --reload

# Run core tests
pytest test_dicom_service.py -v

# Check server health
curl.exe http://localhost:8000/health

# View patients table
psql meddicom_db -c "SELECT * FROM patients;"

# Delete test database
dropdb meddicom_db

# Recreate test database
createdb meddicom_db
```

## Environment Variables

Required entries in `.env`:

```text
DATABASE_URL=postgresql://postgres:password@localhost:5432/meddicom_db
UPLOAD_STORAGE_PATH=./storage
```

## Troubleshooting

| Issue | Solution |
|---|---|
| `Connection refused` | Check PostgreSQL is running: `psql -l` |
| `database does not exist` | Run: `createdb meddicom_db` |
| `No such file or directory` | Run from project root: `pwd` should show `MedDICOMParseAPI` |
| `Permission denied ./storage` | Check write permissions: `chmod 755 .` |
| `ModuleNotFoundError` | Reinstall dependencies: `pip install -r requirements.txt` |

## Next Steps Checklist

1. Server running? Verify with `curl http://localhost:8000/health`.
2. Database connected? Verify tables with `psql meddicom_db -l`.
3. Upload a DICOM file (see the Upload DICOM File test above).
4. Verify data in PostgreSQL: `psql meddicom_db -c "SELECT * FROM patients;"`.
5. Check the storage directory: `ls -la storage/`.
