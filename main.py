import hashlib
import io
import os
from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
import pydicom
from db import get_db, init_db
from services.db_service import DatabaseService
from services.storage import StorageService
from dotenv import load_dotenv

from validation.dicom_validator import validate_dicom
from validation.exceptions import ValidationError

from fastapi import HTTPException
from services.db_service import (
    get_all_studies,
    get_series_by_id,
    get_instance_by_id,
    get_instance_by_sop_uid,
    get_instance_file_path,
    get_instance_metadata,
    get_series_by_study_id,
    get_instances_by_series_id,
    create_ai_result,
    get_latest_ai_result_by_instance,
)
from services.storage_backend import LocalStorageBackend
from core.config import settings
from services.measurement_type import (
    MachineModelResolver,
    MeasurementType,
    ResolveContext,
)
from services.ai_engine import (
    DiaphragmEngine,
    EngineError,
    EngineUnavailableError,
    get_engine,
    primary_value_unit,
    to_result_json,
)

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
    """
    Schema 由 Alembic 統一管理 (PROGRESS §6.13 根治、2026-05-19)。
    startup 不再呼叫 init_db() — 避免 Base.metadata.create_all 搶在 alembic 前建表
    導致下次 `alembic upgrade head` 撞 DuplicateTable。
    新 clone / fresh DB 啟動前須先跑：`alembic upgrade head`。
    `db.init_db` 仍保留供 emergency reset 手動呼叫。
    """
    print("✓ FastAPI startup — schema managed by Alembic (run `alembic upgrade head` before launch)")


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
        # Device tags (added 2026-06-09) — raw signal for the measurement-type
        # resolver, captured at upload for auditability. Safe access (§13);
        # absent tags simply stay None. Resolved lazily at /ai/segment time.
        device_manufacturer = getattr(dicom_data, "Manufacturer", None)
        device_model = getattr(dicom_data, "ManufacturerModelName", None)

        # Duplicate detection (PROGRESS §6.12) — must run BEFORE storage write
        # so a conflicting upload leaves no orphan file. Idempotent path returns
        # the existing instance unchanged; bytes-mismatch returns 409 per
        # CLAUDE.md §13 (UID uniqueness violations must not be silently overwritten).
        if sop_instance_uid:
            existing = get_instance_by_sop_uid(db, sop_instance_uid)
            if existing:
                new_hash = hashlib.sha256(file_content).hexdigest()
                existing_abs_path = storage_service.get_full_path(existing.file_path)
                try:
                    with open(existing_abs_path, "rb") as f:
                        existing_bytes = f.read()
                    existing_hash = hashlib.sha256(existing_bytes).hexdigest()
                except FileNotFoundError:
                    return JSONResponse(status_code=409, content={
                        "detail": (
                            f"SOPInstanceUID {sop_instance_uid} exists in DB "
                            f"(instance_id={existing.id}) but the stored file is missing on disk; "
                            f"manual cleanup required before re-uploading."
                        ),
                        "existing_instance_id": existing.id,
                        "existing_file_missing": True,
                    })

                if new_hash == existing_hash:
                    return {
                        "instance_id": existing.id,
                        "filename": file.filename,
                        "patient_id": existing.study.patient_id if existing.study else patient_id,
                        "study_instance_uid": existing.study_instance_uid,
                        "modality": existing.study.modality if existing.study else modality,
                        "message": "DICOM already exists with identical content; returning existing instance",
                        "duplicate": True,
                    }

                return JSONResponse(status_code=409, content={
                    "detail": (
                        f"SOPInstanceUID {sop_instance_uid} already exists but the uploaded "
                        f"file differs (content hash mismatch). DICOM standard requires "
                        f"reassigning SOPInstanceUID before uploading a modified version. "
                        f"See suggested_actions for resolution paths."
                    ),
                    "existing_instance_id": existing.id,
                    "existing_hash": existing_hash,
                    "new_hash": new_hash,
                    "suggested_actions": {
                        "keep_existing": "Take no action — existing DICOM is preserved",
                        "save_as_new": "Reassign SOPInstanceUID in the source DICOM and re-upload (DICOM-standard path)",
                        "manual_overwrite": "Not supported in MVP; pending §6.14 / auth (§6.4)",
                    },
                })

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

        # Upsert series (added 2026-05-15: previously skipped, leaving series table empty)
        series_instance_uid = getattr(dicom_data, "SeriesInstanceUID", None)
        if series_instance_uid:
            DatabaseService.upsert_series(
                db,
                series_instance_uid=series_instance_uid,
                study_instance_uid=study_instance_uid
            )

        # Create instance record (linked to both study and series)
        instance = DatabaseService.create_instance(
            db,
            file_path=relative_file_path,
            study_instance_uid=study_instance_uid,
            sop_instance_uid=sop_instance_uid,
            series_instance_uid=series_instance_uid,
            device_manufacturer=device_manufacturer,
            device_model=device_model
        )

        # Step 3: Return response (instance_id added 2026-05-14 for client drill-down;
        # duplicate flag added 2026-05-19 per PROGRESS §6.12 — false for new instances)
        return {
            "instance_id": instance.id,
            "filename": file.filename,
            "patient_id": patient_id,
            "study_instance_uid": study_instance_uid,
            "modality": modality,
            "message": "DICOM file uploaded and processed successfully",
            "duplicate": False,
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


@app.get("/studies/{id}/series")
def list_series_for_study(id: int, db: Session = Depends(get_db)):
    series_list = get_series_by_study_id(db, id)
    if series_list is None:
        raise HTTPException(status_code=404, detail=f"Study with id {id} not found")
    return {"series": [_row(s) for s in series_list]}


@app.get("/series/{id}/instances")
def list_instances_for_series(id: int, db: Session = Depends(get_db)):
    instances = get_instances_by_series_id(db, id)
    if instances is None:
        raise HTTPException(status_code=404, detail=f"Series with id {id} not found")
    return {"instances": [_row(i) for i in instances]}


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
def ai_segment(
    id: int,
    db: Session = Depends(get_db),
    engine: DiaphragmEngine = Depends(get_engine),
):
    """對某 instance 跑 AI 橫膈膜量測，結果寫入 ai_results（同步、LEGACY mode）。

    流程（design §6）：解析 measurement type → 醫療安全分支（unknown 422 / thickness
    501）→ 跑引擎（缺相依 503 / 推論失敗 500）→ 序列化 envelope + 寫 ai_results。
    回應全 additive（取代原 stub 的 queued 回應）。
    """
    instance = get_instance_by_id(db, id)
    if not instance:
        raise HTTPException(status_code=404, detail=f"Instance with id {id} not found")

    # 1. 依上傳時抽存的 device model 解析 measurement type
    device_model = getattr(instance, "device_model", None)
    ctx = ResolveContext(
        device_manufacturer=getattr(instance, "device_manufacturer", None),
        device_model=device_model,
    )
    measurement_type = MachineModelResolver().resolve(ctx)

    # 2. 醫療安全分支：不猜（CLAUDE.md §10/§13）
    if measurement_type == MeasurementType.UNKNOWN:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Cannot resolve measurement type: device model {device_model!r} "
                f"is not in the machine-model map. AI segmentation refuses to guess."
            ),
        )
    if measurement_type == MeasurementType.THICKNESS:
        raise HTTPException(
            status_code=501,
            detail=(
                "Thickness measurement is not implemented yet (forward-design); "
                "only excursion / sniff are supported."
            ),
        )

    # 3. 取 DICOM 檔絕對路徑
    file_path = get_instance_file_path(db, id)
    if not file_path or not storage.exists(file_path):
        raise HTTPException(
            status_code=404, detail=f"File not found on disk for instance {id}"
        )
    abs_path = storage.absolute_path(file_path)

    # 4. 跑引擎（缺相依 → 503；推論失敗 → 留 error 結果後 500）
    try:
        result = engine.analyze(abs_path, measurement_type)
    except EngineUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except EngineError as e:
        create_ai_result(
            db,
            instance_id=id,
            model_name=engine.model_name,
            model_version=engine.model_version,
            status="error",
            measurement_type=measurement_type.value,
            error_message=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))

    # 5. 序列化 envelope + 寫 ai_results
    envelope = to_result_json(result)
    primary_value, primary_unit = primary_value_unit(result)
    ai_row = create_ai_result(
        db,
        instance_id=id,
        model_name=result.model_name,
        model_version=result.model_version,
        status="completed",
        measurement_type=measurement_type.value,
        result_json=envelope,
        primary_value=primary_value,
        primary_unit=primary_unit,
        mask_path=result.mask_path,
    )

    # 6. additive response
    return {
        "instance_id": id,
        "ai_result_id": ai_row.id,
        "status": "completed",
        "measurement_type": measurement_type.value,
        "primary_value": primary_value,
        "primary_unit": primary_unit,
        "measurement_count": len(result.measurements),
    }


@app.get("/ai/result/{id}")
def ai_result(id: int, db: Session = Depends(get_db)):
    """回傳某 instance 最新一筆 AI 結果。尚未跑過 → 404（提示先 POST /ai/segment）。"""
    instance = get_instance_by_id(db, id)
    if not instance:
        raise HTTPException(status_code=404, detail=f"Instance with id {id} not found")

    ai_row = get_latest_ai_result_by_instance(db, id)
    if not ai_row:
        raise HTTPException(
            status_code=404,
            detail=f"No AI result for instance {id}; run POST /ai/segment/{id} first",
        )

    return {
        "instance_id": id,
        "ai_result_id": ai_row.id,
        "status": ai_row.status,
        "measurement_type": ai_row.measurement_type,
        "model_name": ai_row.model_name,
        "model_version": ai_row.model_version,
        "primary_value": ai_row.primary_value,
        "primary_unit": ai_row.primary_unit,
        "confidence": ai_row.confidence,
        "mask_url": None,  # mask PNG endpoint 屬下游（design §8）
        "result": ai_row.result_json,
        "error_message": ai_row.error_message,
        "created_at": ai_row.created_at.isoformat() if ai_row.created_at else None,
    }
