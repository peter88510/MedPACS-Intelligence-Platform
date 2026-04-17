"""
FastAPI service for DICOM file upload and metadata parsing.
Minimal, clean, and production-sane implementation.
"""

import io
import logging
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pydicom
from pydicom.errors import InvalidDicomError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="DICOM Upload Service", version="1.0.0")


# Response models (using dict for simplicity, could use Pydantic models)
class DicomMetadata:
    """Container for parsed DICOM metadata."""

    def __init__(
        self,
        patient_id: Optional[str] = None,
        study_instance_uid: Optional[str] = None,
        modality: Optional[str] = None,
    ):
        self.patient_id = patient_id
        self.study_instance_uid = study_instance_uid
        self.modality = modality

    def to_dict(self) -> dict:
        """Convert metadata to dictionary for JSON response."""
        return {
            "PatientID": self.patient_id,
            "StudyInstanceUID": self.study_instance_uid,
            "Modality": self.modality,
        }


def validate_dcm_extension(filename: str) -> bool:
    """Validate that filename has .dcm extension."""
    return filename.lower().endswith(".dcm")


def parse_dicom_file(file_content: bytes) -> DicomMetadata:
    """
    Parse DICOM file content and extract key metadata.

    Args:
        file_content: Raw file bytes

    Returns:
        DicomMetadata object with parsed fields

    Raises:
        InvalidDicomError: If file is not valid DICOM
        Exception: For other parsing errors
    """
    try:
        # Read DICOM file from bytes
        dataset = pydicom.dcmread(io.BytesIO(file_content))

        # Extract metadata fields, using None for missing fields
        patient_id = getattr(dataset, "PatientID", None)
        study_instance_uid = getattr(dataset, "StudyInstanceUID", None)
        modality = getattr(dataset, "Modality", None)

        logger.info(
            f"Successfully parsed DICOM: PatientID={patient_id}, "
            f"StudyInstanceUID={study_instance_uid}, Modality={modality}"
        )

        return DicomMetadata(
            patient_id=patient_id,
            study_instance_uid=study_instance_uid,
            modality=modality,
        )

    except InvalidDicomError as e:
        logger.error(f"Invalid DICOM file: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error parsing DICOM file: {str(e)}")
        raise


@app.get("/", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    logger.info("Health check request")
    return {"status": "healthy", "service": "DICOM Upload Service"}


@app.post("/upload", tags=["DICOM"])
async def upload_dicom(file: UploadFile = File(...)):
    """
    Upload and parse a DICOM file.

    Args:
        file: DICOM file to upload

    Returns:
        JSON with extracted metadata

    Raises:
        HTTPException 400: If file extension is not .dcm
        HTTPException 422: If DICOM parsing fails
    """
    logger.info(f"Received upload request for file: {file.filename}")

    # Validate file extension
    if not validate_dcm_extension(file.filename):
        logger.warning(f"Invalid file extension: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Expected .dcm file, got {file.filename}",
        )

    try:
        # Read file content into memory
        file_content = await file.read()

        if not file_content:
            logger.warning("Empty file received")
            raise HTTPException(status_code=400, detail="File is empty")

        # Parse DICOM
        metadata = parse_dicom_file(file_content)

        logger.info(f"Successfully processed DICOM file: {file.filename}")
        return JSONResponse(content=metadata.to_dict(), status_code=200)

    except InvalidDicomError as e:
        logger.error(f"DICOM parsing failed for {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=f"File is not a valid DICOM file: {str(e)}",
        )
    except HTTPException:
        # Re-raise HTTPExceptions (400 Bad Request, etc.)
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=f"Error parsing DICOM file: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
