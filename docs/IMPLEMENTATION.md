---
docspec: "2.0"
type: ARCHITECTURE
title: "MedDICOMParseAPI v2.0 Implementation Summary"
version: "2.1.0"
status: "updated"
---

# MedDICOMParseAPI v2.0 Implementation Summary

## Overview

Extended FastAPI DICOM parser with PostgreSQL persistence layer and local file storage. The API contract is unchanged from v1.0 to v2.0 (fully backward compatible).

## New and Updated Files

The following files were added or modified in v2.0:

```text
MedDICOMParseAPI/
├── main.py                  (UPDATED) 
├── models.py                (UPDATED)
├── db.py                    (UPDATED)
├── db_service.py            (UPDATED)
├── storage.py               (UPDATED)
├── requirements.txt         (UPDATED)
├── pytest.ini               (NEW) testpaths + pythonpath 設定
├── .env.example             (UPDATED)
├── README.md                (UPDATED)
├── docs/archive/QUICKSTART.md (UPDATED) 測試指令改為 pytest tests/ -v
└── tests/                   (NEW) 測試目錄
    ├── conftest.py          (NEW) 共用工廠函式 _FakeRow / make_*()
    ├── test_dicom_service.py (MOVED) 從根目錄移入
    └── test_query_api.py    (MOVED) 從根目錄移入，移除本地 make_*() 改用 import
```

## System Architecture

The following diagram describes the data flow through the system on each `/upload` request:

```text
┌─────────────────────────────────────────────┐
│         FastAPI /upload Endpoint            │
└──────────────┬──────────────────────────────┘
               │
        1. Parse DICOM (pydicom)
               │
        2. Extract Metadata
               │
        ┌──────┴───────────────────────┐
        ▼                              ▼
   StorageService              DatabaseService
   (save to disk)              (upsert DB)
        │                              │
        ├──> ./storage/               │
        │    {patient_id}/            │
        │    {study_uid}/             │
        │    {filename}.dcm           │
        │                          ┌──┴──────────┐
        │                          ▼             ▼
        │                      PostgreSQL     SQLAlchemy
        │                      ├─ patients
        │                      ├─ studies
        │                      ├─ series
        │                      └─ instances
        │
        └──> Return JSON (same as v1.0)
```

## Key Changes to main.py

### Before: v1.0 Upload Endpoint

```python
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    dicom = pydicom.dcmread(file.file)
    return {
        "patient_id": dicom.PatientID,
        "study_instance_uid": dicom.StudyInstanceUID,
        ...
    }
```

### After: v2.0 Upload Endpoint

```python
@app.post("/upload")
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 1. Parse DICOM (existing logic)
    dicom = pydicom.dcmread(file.file)

    # 2. Save to local storage
    file_path = storage_service.save_dicom(...)

    # 3. Upsert to PostgreSQL
    DatabaseService.upsert_patient(db, patient_id)
    DatabaseService.upsert_study(db, study_instance_uid, patient_id, modality)
    DatabaseService.create_instance(db, file_path, study_instance_uid, sop_uid)

    # 4. Return same response as v1.0 (API contract preserved)
    return { "patient_id": patient_id, ... }
```

## Module Responsibilities

### models.py

- **Patient**: Stores unique `patient_id`; has a one-to-many relationship with studies.
- **Study**: Stores unique `study_instance_uid`; has a foreign key to patient; stores modality.
- **Series**: Provides series-level grouping; extensible for future use.
- **Instance**: Represents an individual DICOM file record; has a foreign key to study; stores `file_path`.

### db.py

- Creates the SQLAlchemy engine with a PostgreSQL connection.
- Provides the `get_db()` dependency for FastAPI.
- `init_db()` creates all tables on startup (idempotent).
- Uses `NullPool` to avoid connection pooling complexity.

### db_service.py

- `upsert_patient()`: Inserts a patient if not exists; returns the existing record on duplicate.
- `upsert_study()`: Inserts a study if not exists, keyed by `study_instance_uid`.
- `create_instance()`: Always creates a new instance record (no upsert required).

### storage.py

- `save_dicom()`: Writes the DICOM file to `storage/{patient_id}/{study_uid}/{filename}`.
- Handles missing metadata with `"unknown_patient"` and `"unknown_study"` fallbacks.
- Returns a relative path for storage in the database.

## Database Schema

```sql
-- Patients (root)
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Studies (one patient, many studies)
CREATE TABLE studies (
    id SERIAL PRIMARY KEY,
    study_instance_uid VARCHAR(255) UNIQUE NOT NULL,
    patient_id VARCHAR(255) NOT NULL REFERENCES patients(patient_id),
    modality VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Series (one study, many series)
CREATE TABLE series (
    id SERIAL PRIMARY KEY,
    series_instance_uid VARCHAR(255),
    study_instance_uid VARCHAR(255) NOT NULL REFERENCES studies(study_instance_uid),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Instances (one study, many DICOM files)
CREATE TABLE instances (
    id SERIAL PRIMARY KEY,
    sop_instance_uid VARCHAR(255) UNIQUE,
    file_path VARCHAR(500) NOT NULL,
    study_instance_uid VARCHAR(255) NOT NULL REFERENCES studies(study_instance_uid),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Upload Workflow

The following steps occur on every `/upload` request:

1. **Parse**: `pydicom.dcmread()` extracts `PatientID`, `StudyInstanceUID`, `Modality`, and `SOPInstanceUID`.
2. **Store**: Saves the file to `storage/{patient_id}/{study_uid}/{filename}`.
3. **Persist**:
  - Upsert patient (keyed by `patient_id`).
  - Upsert study (keyed by `study_instance_uid`).
  - Create instance (new record, foreign key to study).
4. **Respond**: Returns JSON response identical to v1.0 API.

## Error Handling

| Error Condition | Handling |
|---|---|
| Invalid DICOM (`pydicom.errors.InvalidDicomError`) | Returns HTTP 400 |
| Database error (generic exception) | Returns HTTP 500 |
| Missing metadata fields | Replaced with `"unknown_patient"` or `"unknown_study"` placeholders |

## Environment Variables

```text
DATABASE_URL=postgresql://postgres:password@localhost:5432/meddicom_db
UPLOAD_STORAGE_PATH=./storage
```

## Dependencies Added in v2.0

```text
sqlalchemy==2.0.23      # ORM
psycopg2-binary==2.9.9  # PostgreSQL driver
python-dotenv==1.0.0    # Environment variables
```

## Test Coverage

The test suite covers the following areas:

- Health endpoint
- DICOM upload and parsing
- Local file storage
- Patient upsert
- Study upsert
- Instance creation

Tests use an SQLite in-memory database for isolation.

## Backward Compatibility

The API contract is fully unchanged between v1.0 and v2.0:

- **Input**: `multipart/form-data` with a DICOM file (unchanged).
- **Output**: Same JSON response structure (unchanged).
- **Client changes required**: None. All v1.0 consumers work with v2.0 without modification.

## Deployment Checklist (Backend)

- [ ] PostgreSQL database created (`createdb meddicom_db`)
- [ ] `.env` configured with `DATABASE_URL`
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Storage directory is writable (`./storage`)
- [ ] Server started (`uvicorn main:app`)
- [ ] Health check passes (`curl http://localhost:8000/health`)
- [ ] Test DICOM upload succeeds
- [ ] PostgreSQL contains patient, study, and instance records
- [ ] Files exist in `./storage/{patient_id}/{study_uid}/`

---

## Frontend Architecture (Overview)

> Phase 2 工作目錄。完整詳述見 [`frontend/IMPLEMENTATION.md`](../frontend/IMPLEMENTATION.md)。

### Layout

Single-page application (SPA) — one URL, no router. CSS Grid three-column layout:

```
┌────────────────────────────────────────────────────────────┐
│ TopBar                                                      │
├──────────────┬─────────────────────────┬───────────────────┤
│              │                         │ MetadataPanel     │
│ StudyList    │     DicomViewer         │ ──────────────    │
│              │   (CornerstoneJS)       │ AIPanel           │
└──────────────┴─────────────────────────┴───────────────────┘
```

### Stack

- **React 19** + **TypeScript 6** + **Vite 8** (dev server + bundler)
- **CornerstoneJS 4.22** (Cornerstone3D family) for DICOM rendering
- **CSS Modules** for styling — no UI framework
- **React Context** for state — no Redux/Zustand/TanStack Query (5 fields, simple)

### Components

| Component | Responsibility | Backend endpoint |
|---|---|---|
| `<StudyList>` | List studies, click to switch | `GET /studies` |
| `<DicomViewer>` | Render DICOM + optional AI mask overlay | `GET /instances/{id}/file`, `GET /ai/result/{id}/mask` |
| `<MetadataPanel>` | Show current instance metadata | `GET /instances/{id}/metadata` |
| `<AIPanel>` | Run AI button + result display | `POST /ai/segment/{id}`, `GET /ai/result/{id}` |

Plus structural components: `<App>` / `<TopBar>` / `<Layout>` / `<AppContextProvider>` — **8 .tsx files total**, ~500–800 lines of TS/TSX.

### CORS Coupling

Backend `main.py` registers `CORSMiddleware` allowing `http://localhost:5173` (Vite default). The frontend hard-codes `API_BASE = 'http://localhost:8000'` during MVP — will move to `VITE_API_BASE_URL` env var for non-dev deploy.

### Integration Status

- ✅ Scaffolding (React + Vite + TS) — commit `2d055de`
- ✅ CornerstoneJS dependencies installed — commit `83b8c9a`
- ⚪ CornerstoneJS init (Stage B) — planned
- ⚪ DICOM rendering (Stage C) — planned
- ⚪ Four business components — planned

### Deployment Checklist (Frontend, planned)

- [ ] Node.js 22+ installed
- [ ] `cd frontend && npm install` succeeds
- [ ] `npm run dev` starts at `http://localhost:5173`
- [ ] Backend reachable at `http://localhost:8000` with CORS allowing 5173
- [ ] StudyList renders study count from `/studies`
- [ ] DicomViewer renders a DICOM image
- [ ] Run AI button receives stub response

---

## Future Extensions

The current schema is designed to support the following future capabilities:

- Multiple series per study (via the existing `series` table).
- Series-level metadata (extensible schema).
- Soft deletes (add `deleted_at` timestamps to tables).
- Audit logs (add a transaction history table).
- File metadata (add file hash, file size, and timestamp fields to the `instances` table).
