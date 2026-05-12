---
docspec: "2.0"
type: API_REFERENCE
title: "MedDICOMParseAPI v2.0"
version: "2.1.0"
status: "update"
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
├── main.py                  # FastAPI entrypoint / API router
├── config.py                # System configuration and environment loader
├── db.py                    # Database connection/session management
├── db_service.py            # CRUD operations for DICOM metadata
├── models.py                # SQLAlchemy ORM models (Study/Series/Instance)
├── storage.py               # Storage abstraction layer (interface)
├── storage_backend.py       # Local storage implementation (extensible to S3)
├── requirements.txt         # Python dependencies
├── pytest.ini               # Test runner config: testpaths=tests, pythonpath=.
├── alembic.ini              # Alembic config (sqlalchemy.url injected at runtime)
├── alembic/                 # Alembic migrations directory
│   ├── env.py               # Loads DATABASE_URL from config.settings
│   └── versions/            # Migration scripts (baseline + future revisions)
├── storage/                 # Physical file storage directory (DICOM files)
├── validation/              # DICOM validation utilities / rules
├── test_dicom_files/        # Sample DICOM files for testing
├── .env.example             # Environment variable template
├── IMPLEMENTATION.md        # System architecture and technical design
├── QUICKSTART.md            # 5-minute setup guide
├── README.md                # Project overview and usage documentation
├── STORAGE_BACKEND.md       # Storage backend design and extension guide
└── tests/                   # All test files and shared test utilities
    ├── conftest.py          # Shared factory functions: _FakeRow / make_*()
    ├── test_dicom_service.py # Service-level tests for DICOM processing
    └── test_query_api.py    # API endpoint tests for query operations
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

### Step 4: Initialize Schema (Alembic)

After the database is created (Step 3), apply migrations to build the schema.

**Fresh database (no tables yet):**

```powershell
alembic upgrade head
```

**Existing database that already has the schema (e.g., pre-Alembic):**

Mark the DB as already at head — does **not** execute CREATE TABLE:

```powershell
alembic stamp head
```

> ⚠️ Choose `stamp head` (not `upgrade head`) when migrating a DB that pre-dates Alembic and already contains the four tables. Running `upgrade head` on a populated DB will fail with "relation already exists".

Verify migration state:

```powershell
alembic current
```

### Step 5: Run Application

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

## Database Migration (Alembic)

Schema changes are managed via Alembic. **Per CLAUDE.md §12, any schema change must go through a migration script** — direct `Base.metadata.create_all()` calls are reserved for tests only.

### Common commands

```powershell
# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# Roll back to empty schema
alembic downgrade base

# Show current revision
alembic current

# Show migration history
alembic history

# Generate a new migration after editing models.py
alembic revision --autogenerate -m "describe change"
```

### Authoring a new migration

1. Edit `models.py` (add column / table)
2. Run `alembic revision --autogenerate -m "<short description>"`
3. **Open the generated script in `alembic/versions/` and review it** — autogenerate is not perfect (it misses CHECK constraints, ENUM changes, server defaults, etc.)
4. Verify both `upgrade()` and `downgrade()` work on a scratch DB
5. Commit the script

### Notes

- `alembic.ini` does **not** contain credentials; `alembic/env.py` injects `DATABASE_URL` from `config.settings` (loaded from `.env`).
- Tests use in-memory SQLite + `Base.metadata.create_all()` (see `tests/conftest.py`) — they bypass Alembic for speed and isolation.

## Integration Notes

- **API Contract**: The `/upload` response is identical to v1.0. Clients require no changes.
- **Internal Changes**: File storage and database persistence are transparent to API consumers.
- **Database Initialization**: Schema is built by Alembic (`alembic upgrade head`). The legacy `init_db()` in `db.py` is retained for backwards compatibility but is no longer the canonical path — new schema changes must go through migrations.
- **Storage Directory**: The `./storage` directory is created automatically if it does not exist.

## Troubleshooting

### Database Connection Refused

- Ensure PostgreSQL is running.
- Verify `DATABASE_URL` in `.env` is correct.
- Check that the database exists: `createdb meddicom_db`.

### No Such Table

Run Alembic to build the schema:

```powershell
alembic upgrade head
```

If migrations are stuck or out of sync, see the **Database Migration (Alembic)** section above.

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
