import io
import os
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
import pydicom
from db import get_db, init_db
from db_service import DatabaseService
from storage import StorageService
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="MedDICOMParseAPI", version="2.0")

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
