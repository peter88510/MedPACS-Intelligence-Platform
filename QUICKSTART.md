# QUICKSTART Guide - MedDICOMParseAPI v2.0

Get up and running in 5 minutes.

## Prerequisites

- Python 3.8+
- PostgreSQL installed and running
- pip

## Installation & Setup

### 1. Install Dependencies

```bash
cd MedPACS Intelligence Platform
pip install -r requirements.txt
```

### 2. Setup Database

#### Step 1: Create PostgreSQL Database

**Windows (PowerShell/CMD):**
```powershell
createdb -U postgres -h 127.0.0.1 meddicom_db
```

**Linux/macOS:**
```bash
createdb -U postgres -h localhost meddicom_db
```

#### Step 2: Setup Environment Configuration

**Windows (PowerShell):**
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

**Windows (CMD):**
```cmd
copy .env.example .env
notepad .env
```

**Linux/macOS:**
```bash
cp .env.example .env
nano .env
```

#### Step 3: Configure Credentials

Edit `.env` and update with your actual PostgreSQL password:

````
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/meddicom_db
UPLOAD_STORAGE_PATH=./storage
````
**⚠️ Important:**
- Replace `your_actual_password` with your PostgreSQL password
- `.env` should **NOT** be committed to version control (add to `.gitignore`)
- `.env.example` should be committed (template only, no secrets)

#### Step 4: Verify Database Connection

**All Platforms (PowerShell/CMD/Bash):**
````bash
# Test connection
psql -U postgres -h 127.0.0.1 -d meddicom_db -c "SELECT version();"
````

Expected output: PostgreSQL version information ✅

### 3. Run Server

```bash
uvicorn main:app --reload
```

Output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
✓ Database tables initialized
```

## Quick Test

### Health Check

**All Platforms:**
```bash
curl http://localhost:8000/health
```

Response:
```json
{"status":"ok","version":"2.0"}
```

### Upload DICOM

**Linux/macOS:**
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@test_dicom_files/patient_001.dcm"
```
**Windows (PowerShell):**
```powershell
curl.exe -X POST http://localhost:8000/upload -F "file=@test_dicom_files/patient_001.dcm"
```

**Windows (Alternative - PowerShell):**
```powershell
$form = @{ file = Get-Item -Path "test_dicom_files/patient_001.dcm" }
Invoke-RestMethod -Uri "http://localhost:8000/upload" -Method Post -Form $form
```

Response (All Platforms):
```json
{
  "filename": "patient_001.dcm",
  "patient_id": "...",
  "study_instance_uid": "...",
  "modality": "...",
  "message": "DICOM file uploaded and processed successfully"
}
```

## Verify Data in PostgreSQL

```bash
# Connect to database
psql meddicom_db

# View patients
SELECT id, patient_id, created_at FROM patients;

# View studies
SELECT id, study_instance_uid, patient_id, modality FROM studies;

# View instances
SELECT id, file_path, study_instance_uid FROM instances;
```

## Verify Files on Disk

```bash
# Check storage directory
ls -la storage/

# Expected structure:
# storage/
#   └── {patient_id}/
#       └── {study_instance_uid}/
#           └── filename.dcm
```

## Run Tests

```bash
pytest test_dicom_service.py -v
```

Expected output:
```
test_dicom_service.py::test_health_check PASSED
test_dicom_service.py::test_upload_with_valid_dicom PASSED
test_dicom_service.py::test_upload_stores_file_locally PASSED
test_dicom_service.py::test_database_upsert_patient PASSED
test_dicom_service.py::test_database_upsert_study PASSED
test_dicom_service.py::test_database_create_instance PASSED

====== 6 passed ======
```

## What's New (v1.0 → v2.0)

| Feature | v1.0 | v2.0 |
|---------|------|------|
| DICOM Upload | ✅ | ✅ |
| DICOM Parsing | ✅ | ✅ |
| Local Storage | ❌ | ✅ |
| PostgreSQL | ❌ | ✅ |
| API Contract | - | **Unchanged** ✅ |

## File Locations

After first upload, you'll have:

```
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

PostgreSQL database `meddicom_db` now contains:
- `patients` table
- `studies` table
- `series` table
- `instances` table

## Common Commands

```bash
# Start server
uvicorn main:app --reload

# Run tests
pytest test_dicom_service.py -v

# Check server health
curl http://localhost:8000/health

# View database
psql meddicom_db -c "SELECT * FROM patients;"

# Delete test database
dropdb meddicom_db

# Recreate test database
createdb meddicom_db
```

## Environment Variables

Required in `.env`:

```
DATABASE_URL=postgresql://postgres:password@localhost:5432/meddicom_db
UPLOAD_STORAGE_PATH=./storage
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Connection refused` | Check PostgreSQL is running: `psql -l` |
| `database does not exist` | Run: `createdb meddicom_db` |
| `No such file or directory` | Run from project root: `pwd` should show `MedDICOMParseAPI` |
| `Permission denied ./storage` | Check write permissions: `chmod 755 .` |
| `ModuleNotFoundError` | Reinstall deps: `pip install -r requirements.txt` |

## Next Steps

1. ✅ Server running? Check with `curl http://localhost:8000/health`
2. ✅ Database connected? Check tables: `psql meddicom_db -l`
3. ✅ Upload a DICOM file (see "Quick Test" above)
4. ✅ Verify in PostgreSQL: `psql meddicom_db -c "SELECT * FROM patients;"`
5. ✅ Check storage directory: `ls -la storage/`

You're all set! 🎉
