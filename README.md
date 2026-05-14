---
docspec: "2.0"
type: PROJECT_OVERVIEW
title: "MedPACS Intelligence Platform v2.0"
version: "2.2.0"
status: "update"
---

# MedPACS Intelligence Platform

A two-tier system for ultrasound DICOM workflow:

- **Backend** — FastAPI + PostgreSQL + SQLAlchemy + pydicom. DICOM upload, parsing, validation, persistence, and stub AI inference endpoints.
- **Frontend** — React 19 + Vite + TypeScript + CornerstoneJS. Single-page DICOM viewer with metadata panel and AI overlay.

> See [`docs/PLAN.md`](./docs/PLAN.md) for MVP scope and roadmap, [`PROGRESS.md`](./PROGRESS.md) for current status.

## Features

### Backend
- DICOM file upload and parsing
- 6-field DICOM validation (PatientID / StudyInstanceUID / SeriesInstanceUID / SOPInstanceUID / Modality / PixelData)
- Modality whitelist (`US` only)
- Local file storage (hierarchical by `PatientID` → `StudyInstanceUID`)
- PostgreSQL persistence with Alembic migrations
- Stub AI segmentation endpoints (real inference is Phase 3)
- CORS middleware for `http://localhost:5173` dev origin

### Frontend (Phase 2, in progress)
- React + Vite + TypeScript scaffolding (Cornerstone3D deps installed)
- Planned: 4 components (StudyList / DicomViewer / MetadataPanel / AIPanel)
- Planned: CornerstoneJS DICOM rendering with AI mask overlay

## Project Structure

```text
MedPACS Intelligence Platform/
├── main.py                  # FastAPI entrypoint / API router
├── config.py                # Pydantic Settings (env loader)
├── db.py                    # SQLAlchemy engine + session
├── db_service.py            # DB CRUD (service layer)
├── models.py                # SQLAlchemy ORM (Patient/Study/Series/Instance)
├── storage.py               # Storage service interface
├── storage_backend.py       # Local storage impl (S3 extensible)
├── requirements.txt         # Python deps
├── pytest.ini               # pytest config
├── alembic.ini              # Alembic config (sqlalchemy.url injected at runtime)
├── alembic/                 # DB migration scripts
│   ├── env.py               # Loads DATABASE_URL from config.settings
│   └── versions/            # Migration revisions (baseline + future)
├── storage/                 # Physical DICOM storage (runtime-created)
├── validation/              # DICOM validation rules + VALIDATION.md
├── tests/                   # Backend test suite (pytest, 36 tests)
├── test_dicom_files/        # Sample DICOM files for tests
│
├── frontend/                # Frontend (Phase 2)
│   ├── README.md            # Frontend dev guide (新手向中文)
│   ├── IMPLEMENTATION.md    # Frontend architecture (components, Context, API client, Cornerstone)
│   ├── package.json
│   ├── vite.config.ts
│   └── src/                 # App source (components/ / context/ / api/ / cornerstone/)
│
├── .env.example             # Environment variable template
├── README.md                # This file (project overview)
├── PLAN.md                  # MVP scope + roadmap + non-goals
├── PROGRESS.md              # Current project status
├── IMPLEMENTATION.md        # System architecture (backend internals + frontend overview)
├── docs/                    # Detail docs (read on demand)
│   └── archive/             # Archived docs (low traffic)
│       ├── QUICKSTART.md
│       ├── STORAGE_BACKEND.md
│       └── COMMIT_GUIDE.md
├── SESSION_HISTORY.md       # AI session working memory
└── CLAUDE.md                # AI operating contract
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

### Step 6: Start Frontend (Optional, Phase 2)

Skip this if you only need the backend API. In a **new terminal** (keep backend running):

```powershell
cd frontend
npm install        # first time, or after pulling new deps
npm run dev
```

Opens at `http://localhost:5173`. The backend's CORS middleware already allows this origin.

> Frontend developer guide: [`frontend/README.md`](./frontend/README.md)
> Frontend architecture: [`frontend/IMPLEMENTATION.md`](./frontend/IMPLEMENTATION.md)

## Frontend Overview

The frontend is a single-page application (SPA) under `frontend/`:

- **Stack**: React 19 + TypeScript 6 + Vite 8 + CornerstoneJS 4.22 (Cornerstone3D family)
- **State management**: React Context (5 fields) — no Redux/Zustand
- **Components**: 4 business (`StudyList` / `DicomViewer` / `MetadataPanel` / `AIPanel`) + 4 structural = 8 total
- **Styling**: CSS Modules, no UI framework
- **Backend coupling**: hard-coded `API_BASE = 'http://localhost:8000'` during MVP (env var later)

See [`frontend/IMPLEMENTATION.md`](./frontend/IMPLEMENTATION.md) for component design, Context shape, API client structure, and CornerstoneJS integration plan.

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

## CORS (Dev)

`main.py` enables `CORSMiddleware` for development so the frontend (Phase 2 — React + Vite, default port `5173`) can call this API from a browser.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

To allow another origin during development (e.g., `http://localhost:3000`), append it to `allow_origins`. **Production CORS is a deployment decision and is intentionally out of MVP scope** (PLAN §8.6).

## Integration Notes

- **API Contract**: The `/upload` response is identical to v1.0. Clients require no changes.
- **Internal Changes**: File storage and database persistence are transparent to API consumers.
- **Database Initialization**: Schema is built by Alembic (`alembic upgrade head`). The legacy `init_db()` in `db.py` is retained for backwards compatibility but is no longer the canonical path — new schema changes must go through migrations.
- **CORS**: Dev origin is `http://localhost:5173`. See the **CORS (Dev)** section above to add more.
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
