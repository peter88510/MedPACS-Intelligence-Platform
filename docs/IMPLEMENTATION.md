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

### models/ (orm.py)

- **Patient**: Stores unique `patient_id`; has a one-to-many relationship with studies.
- **Study**: Stores unique `study_instance_uid`; has a foreign key to patient; stores modality.
- **Series**: Stores series-level grouping with **unique `series_instance_uid`** (constraint added 2026-05-15); FK to study via `study_instance_uid`. One study has many series.
- **Instance**: Represents an individual DICOM file record; FK to study via `study_instance_uid`; **FK to series via `series_instance_uid` (added 2026-05-15)**; stores `file_path`. Legacy rows from before 2026-05-15 have NULL `series_instance_uid`.

### db/ (session.py)

- Creates the SQLAlchemy engine with a PostgreSQL connection.
- Provides the `get_db()` dependency for FastAPI.
- `init_db()` creates all tables on startup (idempotent).
- Uses `NullPool` to avoid connection pooling complexity.

### services/db_service.py

- `upsert_patient()`: Inserts a patient if not exists; returns the existing record on duplicate.
- `upsert_study()`: Inserts a study if not exists, keyed by `study_instance_uid`.
- **`upsert_series()` (added 2026-05-15)**: Dedupes on `series_instance_uid` — multiple instances within the same DICOM series share the same UID, so this must be called per-upload.
- `create_instance()`: Creates a new instance record. Signature gained `series_instance_uid` parameter (Optional) on 2026-05-15.
- `get_series_by_study_id()` / `get_instances_by_series_id()` (added 2026-05-15): Power the new listing endpoints. Return `None` if the parent doesn't exist (handler emits 404), `[]` if parent exists but has no children.

### services/storage.py

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

-- Series (one study, many series). UNIQUE/NOT NULL added 2026-05-15.
CREATE TABLE series (
    id SERIAL PRIMARY KEY,
    series_instance_uid VARCHAR(255) UNIQUE NOT NULL,
    study_instance_uid VARCHAR(255) NOT NULL REFERENCES studies(study_instance_uid),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Instances (one study, many DICOM files). series_instance_uid FK added 2026-05-15.
CREATE TABLE instances (
    id SERIAL PRIMARY KEY,
    sop_instance_uid VARCHAR(255) UNIQUE,
    file_path VARCHAR(500) NOT NULL,
    study_instance_uid VARCHAR(255) NOT NULL REFERENCES studies(study_instance_uid),
    series_instance_uid VARCHAR(255) REFERENCES series(series_instance_uid),  -- nullable; legacy rows are NULL
    created_at TIMESTAMP DEFAULT NOW()
);
```

> **Authoritative source**: `docs/generated/db_schema.md` (auto-regenerated from `models/` + alembic by pre-commit hook). The SQL above is illustrative and may lag. Migration history: `20809e26d134` (baseline) → `e25c80289a9c` (Series 補完, 2026-05-15).

## Upload Workflow

The following steps occur on every `/upload` request:

1. **Parse**: `pydicom.dcmread()` extracts `PatientID`, `StudyInstanceUID`, **`SeriesInstanceUID`**, `Modality`, and `SOPInstanceUID`.
2. **Validate**: 6-field required check + Modality whitelist (`US` only).
3. **Store**: Saves the file to `storage/{patient_id}/{study_uid}/{filename}`.
4. **Persist**:
  - Upsert patient (keyed by `patient_id`).
  - Upsert study (keyed by `study_instance_uid`).
  - **Upsert series (keyed by `series_instance_uid`, added 2026-05-15)** — if SeriesInstanceUID is missing, this step is skipped.
  - Create instance (new record, FK to study + FK to series).
5. **Respond**: Returns JSON with `instance_id` (added 2026-05-14) plus echoed DICOM tag values.

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

> Phase 2 工作目錄。完整詳述見 [`frontend/docs/IMPLEMENTATION.md`](../frontend/docs/IMPLEMENTATION.md)。

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

## Schema Evolution Beyond v2.0

Changes after the initial v2.0 cut:

| Date | Change | Migration / Commit |
|---|---|---|
| 2026-05-12 | Alembic baseline migration (4 tables; pre-Alembic state captured) | `20809e26d134` |
| 2026-05-14 | `POST /upload` response gained `instance_id` (int, DB pk of new instance). Non-breaking field add. | commit `40fd1e9` |
| 2026-05-15 | **Series 結構補完**: `series.series_instance_uid` UNIQUE+NOT NULL · `instances.series_instance_uid` ADD COLUMN+FK · upload pipeline 加 series upsert · 新 endpoints `GET /studies/{id}/series` + `GET /series/{id}/instances`. | migration `e25c80289a9c`, commit `9967f71` |

Legacy data note: instances and series rows created before 2026-05-15 do not participate in the new series listing endpoint (`series_instance_uid` is NULL on those instance rows; series table was empty pre-补完). MVP accepts this gap; no backfill script.

## Future Extensions

The current schema is designed to support the following future capabilities:

- Soft deletes (add `deleted_at` timestamps to tables).
- Audit logs (add a transaction history table).
- File metadata (add file hash, file size, and timestamp fields to the `instances` table).
- Phase 3 AI: `AIResult` model + migration + real `/ai/segment/{id}` + `/ai/result/{id}/mask` PNG endpoint.
