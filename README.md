---
docspec: "2.0"
type: API_REFERENCE
title: "MedDICOMParseAPI v2.0"
version: "2.0.0"
status: "approved"
---

# MedDICOMParseAPI v2.0

FastAPI backend for DICOM file upload, parsing, and persistent storage with PostgreSQL.

## Features

- DICOM file upload and parsing
- Local file storage (hierarchical by PatientID → StudyInstanceUID)
- PostgreSQL persistence layer
- Backward-compatible API (v1 contract unchanged)

## Project Structure

```text
MedPACS Intelligence Platform/
├── main.py                # FastAPI entrypoint / API router
├── config.py              # System configuration and environment loader
├── db.py                  # Database connection/session management
├── db_service.py          # CRUD operations for DICOM metadata
├── models.py              # SQLAlchemy ORM models (Study/Series/Instance)
├── storage.py             # Storage abstraction layer (interface)
├── storage_backend.py     # Local storage implementation (extensible to S3)
├── test_dicom_service.py  # Service-level tests for DICOM processing
├── test_query_api.py      # API endpoint tests for query operations
├── requirements.txt       # Python dependencies
├── storage/               # Physical file storage directory (DICOM files)
├── validation/            # DICOM validation utilities / rules
├── test_dicom_files/      # Sample DICOM files for testing
├── .env.example           # Environment variable template
├── IMPLEMENTATION.md      # System architecture and technical design
├── QUICKSTART.md          # 5-minute setup guide
├── README.md              # Project overview and usage documentation
└── STORAGE_BACKEND.md     # Storage backend design and extension guide
```

## Setup

### Step 1: Install Dependencies

_Linux/macOS:_

```bash
pip install -r requirements.txt
```

_Windows:_

```powershell
pip install -r requirements.txt
```

### Step 2: Configure Environment

_Linux/macOS:_

```bash
cp .env.example .env

# Edit .env
nano .env
# or
vim .env
```

_Windows (PowerShell):_

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

# Edit .env with actual credentials
notepad .env
```

_Windows (CMD):_

```cmd
REM Create .env.example
echo # PostgreSQL Configuration > .env.example
echo DATABASE_URL=postgresql://postgres:password@localhost:5432/meddicom_db >> .env.example
echo # Server Configuration >> .env.example
echo UPLOAD_STORAGE_PATH=./storage >> .env.example

REM Copy to .env
copy .env.example .env

REM Edit .env
notepad .env
```

#### Configure Credentials

Edit `.env` and update with your actual PostgreSQL password:

```text
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/meddicom_db
UPLOAD_STORAGE_PATH=./storage
```

### Step 3: Create PostgreSQL Database

_Linux/macOS:_

```bash
createdb -U postgres -h localhost meddicom_db
```

_Windows:_

```cmd
createdb -U postgres -h 127.0.0.1 meddicom_db
```

#### Verify Database Creation

_Linux/macOS:_

```bash
psql -U postgres -h 127.0.0.1 -c "\l"
```

_Windows:_

```powershell
psql -U postgres -h 127.0.0.1 -c "\l"
```

Expected output: `meddicom_db` should appear in the list.

#### Alternative: Create Database via psql

Connect to PostgreSQL on any platform:

_Linux/macOS:_

```bash
psql -U postgres -h 127.0.0.1
```

_Windows:_

```powershell
psql -U postgres -h 127.0.0.1
```

Then execute:

```sql
CREATE DATABASE meddicom_db;
```

### Step 4: Run Application

_Linux/macOS:_

```bash
uvicorn main:app --reload
```

_Windows:_

```powershell
uvicorn main:app --reload
```

Server runs at `http://localhost:8000`.

## API Endpoints

### POST /upload

Upload and process a DICOM file.

**Request:**

```text
Content-Type: multipart/form-data
Body: file (binary DICOM)
```

**Response (200 OK):**

```json
{
  "filename": "patient_001.dcm",
  "patient_id": "P12345",
  "study_instance_uid": "1.2.3.4.5.6.7",
  "modality": "CT",
  "message": "DICOM file uploaded and processed successfully"
}
```

### GET /health

Health check endpoint.

**Response (200 OK):**

```json
{
  "status": "ok",
  "version": "2.0"
}
```

### GET /studies

Returns all studies stored in the database, ordered by most recently ingested.

**Response (200 OK):**

```json
{
  "studies": [
    { "id": 1, "study_instance_uid": "1.2.840.10008..." }
  ]
}
```

### GET /series/{id}

Returns a single series record by its database ID.

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Database primary key of the series |

**Response (200 OK):** Series object.

**Response (404 Not Found):**

```json
{ "detail": "Series with id 99 not found" }
```

### GET /instances/{id}

Returns a single instance record by its database ID.

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Database primary key of the instance |

**Response (200 OK):** Instance object.

**Response (404 Not Found):**

```json
{ "detail": "Instance with id 99 not found" }
```

### GET /instances/{id}/file

Streams the raw DICOM file for the specified instance.

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Database primary key of the instance |

**Response (200 OK):** `application/dicom` file stream.

**Response (404 Not Found):** Returned when the instance does not exist, or when the file is not present on disk.

### GET /instances/{id}/metadata

Returns all metadata fields for the specified instance.

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Database primary key of the instance |

**Response (200 OK):**

```json
{ "id": 1, "sop_instance_uid": "1.2.840...", "series_id": 10 }
```

**Response (404 Not Found):**

```json
{ "detail": "Instance with id 99 not found" }
```

## AI Endpoints (Stub)

### POST /ai/segment/{id}

Triggers AI segmentation for the specified instance. Currently implemented as a stub.

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Database primary key of the instance |

**Response (200 OK):**

```json
{ "instance_id": 1, "status": "queued", "message": "Segmentation job accepted (stub)" }
```

**Response (404 Not Found):**

```json
{ "detail": "Instance with id 99 not found" }
```

### GET /ai/result/{id}

Returns the AI segmentation result for the specified instance. Currently implemented as a stub.

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Database primary key of the instance |

**Response (200 OK):**

```json
{ "instance_id": 1, "status": "completed", "result": { "mask": "stub_mask_data", "confidence": 0.95 } }
```

**Response (404 Not Found):**

```json
{ "detail": "Instance with id 99 not found" }
```

## Database Schema

### patients

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | Primary key |
| `patient_id` | String | Unique; referenced as FK in studies |
| `created_at` | DateTime | Auto-set on insert |

### studies

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | Primary key |
| `study_instance_uid` | String | Unique; referenced as FK in instances |
| `patient_id` | String | FK → `patients.patient_id` |
| `modality` | String | Nullable |
| `created_at` | DateTime | Auto-set on insert |

### series

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | Primary key |
| `series_instance_uid` | String | Nullable |
| `study_instance_uid` | String | FK → `studies.study_instance_uid` |
| `created_at` | DateTime | Auto-set on insert |

### instances

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | Primary key |
| `sop_instance_uid` | String | Nullable; unique |
| `file_path` | String | Relative path to stored file |
| `study_instance_uid` | String | FK → `studies.study_instance_uid` |
| `created_at` | DateTime | Auto-set on insert |

## Storage Structure

Files are stored locally in a hierarchical directory structure:

```text
storage/
└── {patient_id}/
    └── {study_instance_uid}/
        └── {filename}.dcm
```

Example with known metadata:

```text
storage/
└── P12345/
    └── 1.2.3.4.5.6.7/
        └── patient_001.dcm
```

Example with missing PatientID or StudyInstanceUID:

```text
storage/
└── unknown_patient/
    └── unknown_study/
        └── file.dcm
```

## Testing

Run the core test suite:

_Linux/macOS:_

```bash
pytest test_dicom_service.py -v
```

_Windows:_

```powershell
pytest test_dicom_service.py -v
```

Tests cover:

- Health endpoint
- DICOM upload and parsing
- Local file storage
- Database operations (upsert patient, upsert study, create instance)

## Integration Notes

- **API Contract**: The `/upload` response is identical to v1.0. Clients require no changes.
- **Internal Changes**: File storage and database persistence are transparent to API consumers.
- **Database Initialization**: On first run, all tables are created automatically via `init_db()` at startup.
- **Storage Directory**: The `./storage` directory is created automatically if it does not exist.

## Troubleshooting

### Database Connection Refused

- Ensure PostgreSQL is running.
- Verify `DATABASE_URL` in `.env` is correct.
- Check that the database exists: `createdb meddicom_db`.

### No Such Table

Database tables are created automatically on first startup. If manual creation is required:

```python
from db import init_db
init_db()
```

### Permission Denied on ./storage

- Ensure write permissions exist in the project directory.
- Verify `UPLOAD_STORAGE_PATH` is correctly set in `.env`.

_Linux/macOS:_

```bash
chmod 755 .
```

## Version History

| Version | Status | Notes |
|---|---|---|
| v2.0 | Current | Added PostgreSQL persistence and local file storage |
| v1.0 | Superseded | Initial DICOM parsing and upload |
