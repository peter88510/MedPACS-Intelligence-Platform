# MedDICOMParseAPI v2.0

FastAPI backend for DICOM file upload, parsing, and persistent storage with PostgreSQL.

## Features

- ✅ DICOM file upload and parsing
- ✅ Local file storage (hierarchical by PatientID → StudyInstanceUID)
- ✅ PostgreSQL persistence layer
- ✅ Backward-compatible API (v1 contract unchanged)

## Project Structure

```
MedPACS Intelligence Platform/
├── main.py                 # FastAPI application with /upload endpoint
├── models.py               # SQLAlchemy ORM models (Patient, Study, Instance)
├── db.py                   # Database connection and session management
├── db_service.py           # Database CRUD operations
├── storage.py              # Local file storage service
├── test_dicom_service.py   # Test suite
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
└── storage/                # Local DICOM file storage (auto-created)
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

#### Windows (PowerShell)
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

#### Windows (CMD)
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

#### Linux/macOS
```bash
cp .env.example .env

# Edit .env
nano .env
# or
vim .env
```

#### Configure Credentials

Edit `.env` and update with your actual PostgreSQL password:
```
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/meddicom_db
UPLOAD_STORAGE_PATH=./storage
```

### 3. Create PostgreSQL Database

#### Windows (PowerShell/CMD)
```cmd
createdb -U postgres -h 127.0.0.1 meddicom_db
```

#### Linux/macOS
```bash
createdb -U postgres -h localhost meddicom_db
```

#### Verify Database Creation

```bash
# List all databases
psql -U postgres -h 127.0.0.1 -c "\l"
```

Expected output: `meddicom_db` should appear in the list ✅

**Alternative: Using psql (All Platforms)**
```bash
# Connect to PostgreSQL and create database
psql -U postgres -h 127.0.0.1
```

Then execute:
```sql
CREATE DATABASE meddicom_db;
```

### 4. Run Application

```bash
uvicorn main:app --reload
```

Server runs at `http://localhost:8000`

## API Endpoints

### POST /upload
Upload and process a DICOM file.

**Request:**
```
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

**Response `200`**
```json
{
  "studies": [
    { "id": 1, "study_instance_uid": "1.2.840.10008..." },
    ...
  ]
}
```

---

### GET /series/{id}
Returns a single series record by its database ID.

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Database primary key of the series |

**Response `200`** — series object  
**Response `404`**
```json
{ "detail": "Series with id 99 not found" }
```

---

### GET /instances/{id}
Returns a single instance record by its database ID.

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Database primary key of the instance |

**Response `200`** — instance object  
**Response `404`**
```json
{ "detail": "Instance with id 99 not found" }
```


## Database Schema

### patients
- `id` (PK, Integer)
- `patient_id` (String, Unique, FK reference in studies)
- `created_at` (DateTime)

### studies
- `id` (PK, Integer)
- `study_instance_uid` (String, Unique, FK reference in instances)
- `patient_id` (String, FK → patients.patient_id)
- `modality` (String, nullable)
- `created_at` (DateTime)

### series
- `id` (PK, Integer)
- `series_instance_uid` (String, nullable)
- `study_instance_uid` (String, FK → studies.study_instance_uid)
- `created_at` (DateTime)

### instances
- `id` (PK, Integer)
- `sop_instance_uid` (String, nullable, unique)
- `file_path` (String, relative path to stored file)
- `study_instance_uid` (String, FK → studies.study_instance_uid)
- `created_at` (DateTime)

## Storage Structure

Files are stored locally in hierarchical structure:
```
storage/
└── {patient_id}/
    └── {study_instance_uid}/
        └── {filename}.dcm
```

Example:
```
storage/
└── P12345/
    └── 1.2.3.4.5.6.7/
        └── patient_001.dcm
```

If PatientID or StudyInstanceUID is missing:
```
storage/
└── unknown_patient/
    └── unknown_study/
        └── file.dcm
```

## Testing

Run tests with pytest:

```bash
pytest test_dicom_service.py -v
```

Tests cover:
- Health endpoint
- DICOM upload and parsing
- Local file storage
- Database operations (upsert patient, study, create instance)

## Integration Notes

- **API Contract:** The `/upload` response is identical to v1.0. Clients need no changes.
- **Internal Changes:** File storage and database persistence are transparent to API consumers.
- **Database:** On first run, tables are created automatically via `init_db()` at startup.
- **Storage:** The `./storage` directory is created automatically if it doesn't exist.

## Troubleshooting

### "Database connection refused"
- Ensure PostgreSQL is running
- Verify `DATABASE_URL` in `.env` is correct
- Check database exists: `createdb meddicom_db`

### "No such table"
- Database tables are created automatically on first startup
- If manual creation needed:
  ```python
  from db import init_db
  init_db()
  ```

### "Permission denied: ./storage"
- Ensure write permissions in project directory
- Check `UPLOAD_STORAGE_PATH` is correct in `.env`

## Version History

- **v2.0** (Current) - Added PostgreSQL persistence and local file storage
- **v1.0** - Initial DICOM parsing and upload
