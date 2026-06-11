---
docspec: "2.0"
type: PROJECT_OVERVIEW
title: "MedPACS Intelligence Platform v2.0"
version: "2.2.0"
status: "update"
---

# MedPACS Intelligence Platform

A two-tier system for ultrasound DICOM workflow:

- **Backend** — FastAPI + PostgreSQL + SQLAlchemy + pydicom. DICOM upload, parsing, validation, persistence, and AI measurement endpoints (diaphragm excursion, paddle; real inference needs the AI runtime — see Step 7).
- **Frontend** — React 19 + Vite + TypeScript + CornerstoneJS. Single-page DICOM viewer with metadata panel and AI overlay.

> See [`docs/PLAN.md`](./docs/PLAN.md) for MVP scope and roadmap, [`PROGRESS.md`](./PROGRESS.md) for current status.

## Features

### Backend
- DICOM file upload and parsing
- 6-field DICOM validation (PatientID / StudyInstanceUID / SeriesInstanceUID / SOPInstanceUID / Modality / PixelData)
- Modality whitelist (`US` only)
- Local file storage (hierarchical by `PatientID` → `StudyInstanceUID`)
- PostgreSQL persistence with Alembic migrations
- AI measurement endpoints (`/ai/segment`, `/ai/result`) — swappable engine layer wrapping the vendored `./AI` diaphragm pipeline; end-to-end inference needs the AI runtime (Step 7)
- CORS middleware for `http://localhost:5173` dev origin

### Frontend (Phase 2, in progress)
- React + Vite + TypeScript scaffolding (Cornerstone3D deps installed)
- Planned: 4 components (StudyList / DicomViewer / MetadataPanel / AIPanel)
- Planned: CornerstoneJS DICOM rendering with AI mask overlay

## Project Structure

> Reorganized 2026-05-14 (Phase 1 + 2 doc重組): root-level deep docs moved into `docs/`; cross-session working memory moved into `context/`; frontend mirrors the same `context/` + `docs/` layout. The authoritative full tree lives in [`PROGRESS.md`](./PROGRESS.md) §7.

```text
MedPACS Intelligence Platform/
├── main.py                          # API layer entrypoint (uvicorn main:app)
├── core/                            # config (settings)
├── db/                              # session / engine
├── models/                          # SQLAlchemy ORM
├── services/                        # db_service / storage / storage_backend / measurement_type
├── requirements.txt / pytest.ini / alembic.ini
├── alembic/                          # DB migration scripts (env.py + versions/)
├── storage/                          # Physical DICOM storage (runtime-created)
├── validation/                       # DICOM validation rules
├── tests/                            # Backend pytest suite (36 tests)
├── test_dicom_files/                 # Sample DICOM fixtures
│
├── frontend/                         # Phase 2 frontend (React + Vite + TS + Cornerstone3D)
│   ├── CLAUDE.md / README.md / PROGRESS.md
│   ├── context/                      # Small must-read state files
│   │   ├── HANDOFF.md                # Backend-state mirror (main-Agent maintained)
│   │   ├── DISPATCH.md               # Current task (overwritten per dispatch)
│   │   └── SESSION_HISTORY.md        # Frontend-Agent working memory
│   ├── docs/                         # Detail docs (read on demand)
│   │   ├── IMPLEMENTATION.md         # Frontend architecture
│   │   └── archive/                  # Frontend-side archive
│   ├── package.json / vite.config.ts / tsconfig.*.json
│   └── src/                          # main.tsx / App.tsx / cornerstone/setup.ts / components/
│
├── context/                          # Main-Agent small must-read state
│   └── SESSION_HISTORY.md            # AI session working memory (A/B sections)
│
├── docs/                             # Detail docs (read on demand)
│   ├── PLAN.md                       # MVP scope + roadmap + non-goals
│   ├── IMPLEMENTATION.md             # System architecture (backend internals + frontend overview)
│   ├── generated/                    # 🤖 auto-generated (do not hand-edit)
│   │   ├── api_spec.md               # FastAPI routes (from main.py)
│   │   └── db_schema.md              # DB schema (from models/ + alembic)
│   └── archive/                      # Low-traffic archived docs
│       ├── QUICKSTART.md             # 5-min API walkthrough
│       ├── STORAGE_BACKEND.md        # Storage backend design
│       └── COMMIT_GUIDE.md           # Commit flow (superseded by system prompt)
│
├── scripts/                          # Tooling
│   ├── gen_api_spec.py               # → docs/generated/api_spec.md
│   ├── gen_db_schema.py              # → docs/generated/db_schema.md
│   └── hooks/pre-commit              # git hook: source change → auto regen
│
├── .env.example                      # Env var template (DATABASE_URL / UPLOAD_STORAGE_PATH)
├── .env                              # Real env config (git ignored)
├── README.md                         # This file (project overview)
├── PROGRESS.md                       # Current project status
├── CLAUDE.md                         # AI operating contract
└── .venv/                            # Python virtualenv (git ignored)
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
> Frontend architecture: [`frontend/docs/IMPLEMENTATION.md`](./frontend/docs/IMPLEMENTATION.md)

### Step 7: Optional — AI inference setup (Phase 3 prep)

The AI diaphragm-excursion inference pipeline is vendored under [`AI/`](./AI/) (source-only;
heavy deps and model weights are excluded from git). Skip this section unless you plan to
run real AI inference (Phase 3 backend integration; see PROGRESS §5 Phase 3).

**1. Pull heavy artifacts** (excluded from this repo by `.gitignore`):

```powershell
# paddleseglibs/ — vendored PaddleSeg with Patch 2A-2C modifications (~27 MB)
git clone --depth 1 https://github.com/peter88510/diaphragm_excursion.git temp-ai
Copy-Item -Recurse temp-ai/paddleseglibs ./AI/
Remove-Item -Recurse -Force temp-ai

# Model weights (5 × 323 MB) — obtain from lab storage and place under:
#     AI/paddleseglibs/output/model/<model_name>/best_model/model.pdparams
```

**2. Install AI Python deps** (separate from MedPACS backend):

```powershell
pip install -r requirements-ai.txt
```

> ⚠️ `paddlepaddle` may need a version pin matching your CUDA / CPU environment.
> Edit `requirements-ai.txt` as needed.

**3. Smoke test** the standalone AI pipeline:

```powershell
cd AI
python main.py  # edit `image_path` at the bottom of main.py first
```

Expected: `[done] N frames, ..., excursion_runs=M` log line with `excursion_cm` values
in the 1-7 cm range (typical diaphragm range). See [`AI/README.md`](./AI/README.md) §3
for full Quick Start.

> Backend integration is done (2026-06-10): `/ai/segment/{id}` calls `AI.main.run`
> via the swappable `services/ai_engine` layer. Once this AI runtime is installed,
> `/ai/segment` runs real inference; otherwise it returns 503. See PROGRESS §5 Phase 3.

## Frontend Overview

The frontend is a single-page application (SPA) under `frontend/`:

- **Stack**: React 19 + TypeScript 6 + Vite 8 + CornerstoneJS 4.22 (Cornerstone3D family)
- **State management**: React Context (5 fields) — no Redux/Zustand
- **Components**: 4 business (`StudyList` / `DicomViewer` / `MetadataPanel` / `AIPanel`) + 4 structural = 8 total
- **Styling**: CSS Modules, no UI framework
- **Backend coupling**: hard-coded `API_BASE = 'http://localhost:8000'` during MVP (env var later)

See [`frontend/docs/IMPLEMENTATION.md`](./frontend/docs/IMPLEMENTATION.md) for component design, Context shape, API client structure, and CornerstoneJS integration plan.

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
  "instance_id": 1,
  "filename": "patient_001.dcm",
  "patient_id": "P12345",
  "study_instance_uid": "1.2.3.4.5.6.7",
  "modality": "CT",
  "message": "DICOM file uploaded and processed successfully"
}
```

| Field | Type | Notes |
|---|---|---|
| `instance_id` | integer | DB primary key of the newly-created instance. Use this to drill down via `GET /instances/{id}` / `/instances/{id}/file` / `/instances/{id}/metadata`. Added 2026-05-14. |
| `filename` | string | Echoed from upload |
| `patient_id` | string | DICOM `PatientID` tag value (not the DB primary key) |
| `study_instance_uid` | string | DICOM `StudyInstanceUID` tag value |
| `modality` | string | DICOM `Modality` tag value |

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

### GET /studies/{id}/series

Returns all series for the given study (added 2026-05-15).

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Database primary key of the study |

**Response (200 OK):**

```json
{ "series": [ { "id": 10, "series_instance_uid": "1.2.3.4", "study_instance_uid": "1.2.3" } ] }
```

Empty `series: []` is valid when the study has no series records yet (e.g., legacy uploads from before 2026-05-15 when the upload pipeline did not write to the series table).

**Response (404 Not Found):** Returned when the study itself does not exist.

### GET /series/{id}/instances

Returns all instances for the given series (added 2026-05-15).

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Database primary key of the series |

**Response (200 OK):**

```json
{ "instances": [ { "id": 100, "sop_instance_uid": "1.2.3.4.5", "series_instance_uid": "1.2.3.4" } ] }
```

Empty `instances: []` is valid when the series exists but its child instances were uploaded before the 2026-05-15 schema upgrade (their `series_instance_uid` column is NULL and they cannot be matched).

**Response (404 Not Found):** Returned when the series itself does not exist.

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

## AI Endpoints

> Real integration layer since 2026-06-10 (replaces the previous stubs). The
> **end-to-end inference** requires the AI runtime (paddle + model weights, see
> [Step 7](#step-7-optional--ai-inference-setup-phase-3-prep)); without it
> `/ai/segment` returns **503**. The measurement type is resolved from the DICOM
> device model (`ManufacturerModelName`): `C62` → excursion, `L154` → thickness.

### POST /ai/segment/{id}

Runs diaphragm measurement for the instance (synchronous, LEGACY mode) and writes
a row into `ai_results`.

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Database primary key of the instance |

**Response (200 OK):**

```json
{ "instance_id": 1, "ai_result_id": 42, "status": "completed",
  "measurement_type": "excursion", "primary_value": 2.31, "primary_unit": "cm",
  "measurement_count": 1 }
```

| Status | When |
|---|---|
| 422 | Device model not in the machine-model map (cannot resolve type — refuses to guess) |
| 501 | Thickness measurement (forward-design; algorithm not implemented) |
| 503 | AI runtime deps not installed (install `requirements-ai.txt` + Step 7) |
| 500 | Inference attempted but failed (an `error` row is recorded) |
| 404 | Instance not found |

### GET /ai/result/{id}

Returns the latest AI result for the instance.

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Database primary key of the instance |

**Response (200 OK):**

```json
{ "instance_id": 1, "ai_result_id": 42, "status": "completed",
  "measurement_type": "excursion", "model_name": "diaphragm_excursion",
  "model_version": "6139799", "primary_value": 2.31, "primary_unit": "cm",
  "confidence": null, "mask_url": null,
  "result": { "schema_version": 1, "measurements": [ ... ], "primary": { ... } },
  "error_message": null, "created_at": "..." }
```

> `mask_url` is currently `null` — the mask PNG endpoint is a downstream task.

**Response (404 Not Found):** instance missing, or no AI result yet (run `POST /ai/segment/{id}` first).

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
| `series_instance_uid` | String | **Unique, NOT NULL** (since 2026-05-15 migration `e25c80289a9c`) |
| `study_instance_uid` | String | FK → `studies.study_instance_uid` |
| `created_at` | DateTime | Auto-set on insert |

### instances

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | Primary key |
| `sop_instance_uid` | String | Nullable; unique |
| `file_path` | String | Relative path to stored file |
| `study_instance_uid` | String | FK → `studies.study_instance_uid` |
| `series_instance_uid` | String | Nullable; FK → `series.series_instance_uid` (added 2026-05-15; legacy rows are NULL) |
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

# Generate a new migration after editing models/orm.py
alembic revision --autogenerate -m "describe change"
```

### Authoring a new migration

1. Edit `models/orm.py` (add column / table)
2. Run `alembic revision --autogenerate -m "<short description>"`
3. **Open the generated script in `alembic/versions/` and review it** — autogenerate is not perfect (it misses CHECK constraints, ENUM changes, server defaults, etc.)
4. Verify both `upgrade()` and `downgrade()` work on a scratch DB
5. Commit the script

### Notes

- `alembic.ini` does **not** contain credentials; `alembic/env.py` injects `DATABASE_URL` from `core.config.settings` (loaded from `.env`).
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
- **Database Initialization**: Schema is built by Alembic (`alembic upgrade head` — required before first `uvicorn main:app` launch on a fresh DB). The legacy `init_db()` in `db/session.py` is retained as a callable for emergency reset but is **no longer invoked at startup** (since 2026-05-19, PROGRESS §6.13 root-cause fix to avoid `Base.metadata.create_all` racing alembic and causing DuplicateTable on next `alembic upgrade head`).
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
