import io
import os
from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
import pydicom
from db import get_db, init_db
from db_service import DatabaseService
from storage import StorageService
from dotenv import load_dotenv

from validation.dicom_validator import validate_dicom
from validation.exceptions import ValidationError

from fastapi import HTTPException
from db_service import get_all_studies, get_series_by_id, get_instance_by_id, get_instance_file_path, get_instance_metadata
from storage_backend import LocalStorageBackend
from config import settings

load_dotenv()

app = FastAPI(title="MedDICOMParseAPI", version="2.0")

# CORS — dev only. Allow Vite default origin so the React frontend (Phase 2)
# can call the API from http://localhost:5173. Production CORS is a deployment
# decision and is intentionally out of MVP scope (PLAN §8.6).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize storage service
STORAGE_PATH = os.getenv("UPLOAD_STORAGE_PATH", "./storage")
storage_service = StorageService(STORAGE_PATH)


@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    try:
        init_db()
        print("✓ Database tables initialized")
    except Exception as e:
        print(f"⚠ Database initialization warning: {e}")


@app.post("/upload")
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload and process DICOM file.
    
    API CONTRACT UNCHANGED:
    - Input: multipart file upload
    - Output: JSON with metadata (same as before)
    
    NEW INTERNAL BEHAVIOR:
    - Parse DICOM (existing logic)
    - Save file to local storage
    - Upsert into PostgreSQL
    - Return same response
    """
    try:
        # Read file
        file_content = await file.read()

        # Parse DICOM (existing logic unchanged)
        dicom_data = pydicom.dcmread(io.BytesIO(file_content))

        try:
            validate_dicom(dicom_data)
        except ValidationError as e:
            return JSONResponse(status_code=400, content={"error": str(e)})

        # Extract metadata
        patient_id = getattr(dicom_data, "PatientID", "unknown_patient")
        study_instance_uid = getattr(dicom_data, "StudyInstanceUID", "unknown_study")
        modality = getattr(dicom_data, "Modality", None)
        sop_instance_uid = getattr(dicom_data, "SOPInstanceUID", None)

        # Step 1: Save to local storage
        relative_file_path = storage_service.save_dicom(
            file_content=file_content,
            patient_id=patient_id,
            study_instance_uid=study_instance_uid,
            filename=file.filename or "unknown.dcm"
        )

        # Step 2: Upsert into database
        # Upsert patient
        DatabaseService.upsert_patient(db, patient_id=patient_id)

        # Upsert study
        DatabaseService.upsert_study(
            db,
            study_instance_uid=study_instance_uid,
            patient_id=patient_id,
            modality=modality
        )

        # Create instance record
        DatabaseService.create_instance(
            db,
            file_path=relative_file_path,
            study_instance_uid=study_instance_uid,
            sop_instance_uid=sop_instance_uid
        )

        # Step 3: Return same response as before (API contract preserved)
        return {
            "filename": file.filename,
            "patient_id": patient_id,
            "study_instance_uid": study_instance_uid,
            "modality": modality,
            "message": "DICOM file uploaded and processed successfully"
        }

    except pydicom.errors.InvalidDicomError:
        raise HTTPException(status_code=400, detail="Invalid DICOM file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "2.0"}


# --- Day 6-7: Query endpoints ---

def _row(obj) -> dict:
    d = obj.__dict__.copy()
    d.pop("_sa_instance_state", None)
    return d


@app.get("/studies")
def list_studies(db: Session = Depends(get_db)):
    studies = get_all_studies(db)
    return {"studies": [_row(s) for s in studies]}


@app.get("/series/{id}")
def get_series(id: int, db: Session = Depends(get_db)):
    series = get_series_by_id(db, id)
    if not series:
        raise HTTPException(status_code=404, detail=f"Series with id {id} not found")
    return _row(series)


@app.get("/instances/{id}")
def get_instance(id: int, db: Session = Depends(get_db)):
    instance = get_instance_by_id(db, id)
    if not instance:
        raise HTTPException(status_code=404, detail=f"Instance with id {id} not found")
    return _row(instance)


# --- Day 8-9: Frontend-facing endpoints ---
storage = LocalStorageBackend(base_dir=settings.UPLOAD_STORAGE_PATH)


@app.get("/instances/{id}/file")
def download_instance_file(id: int, db: Session = Depends(get_db)):
    file_path = get_instance_file_path(db, id)
    if not file_path:
        raise HTTPException(status_code=404, detail=f"Instance with id {id} not found")
    if not storage.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found on disk for instance {id}")
    return FileResponse(
        path=storage.absolute_path(file_path),
        media_type="application/dicom",
        filename=os.path.basename(file_path)
    )


@app.get("/instances/{id}/metadata")
def get_instance_meta(id: int, db: Session = Depends(get_db)):
    metadata = get_instance_metadata(db, id)
    if metadata is None:
        raise HTTPException(status_code=404, detail=f"Instance with id {id} not found")
    return metadata


@app.post("/ai/segment/{id}")
def ai_segment(id: int, db: Session = Depends(get_db)):
    instance = get_instance_by_id(db, id)
    if not instance:
        raise HTTPException(status_code=404, detail=f"Instance with id {id} not found")
    # Stub: AI segmentation placeholder
    return {
        "instance_id": id,
        "status": "queued",
        "message": "Segmentation job accepted (stub)"
    }


@app.get("/ai/result/{id}")
def ai_result(id: int, db: Session = Depends(get_db)):
    instance = get_instance_by_id(db, id)
    if not instance:
        raise HTTPException(status_code=404, detail=f"Instance with id {id} not found")
    # Stub: return fixed mock result
    return {
        "instance_id": id,
        "status": "completed",
        "result": {
            "mask": "stub_mask_data",
            "confidence": 0.95
        }
    }
