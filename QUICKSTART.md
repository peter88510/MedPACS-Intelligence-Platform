# DICOM Upload Service - Quick Start

## 1. Install Dependencies
```bash
pip install -r requirements.txt
```

## 2. Run the Service
```bash
uvicorn main:app --reload
```

Service will be available at: **http://localhost:8000**

## 3. Test the API

### Option A: Using cURL
```bash
# Health check
curl http://localhost:8000/

# Create a test DICOM file (Python one-liner)
python -c "
import pydicom
from pydicom.dataset import Dataset, FileDataset

file_meta = Dataset()
file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
file_meta.MediaStorageSOPInstanceUID = '1.2.3'
file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian

ds = FileDataset('test.dcm', {}, file_meta=file_meta, preamble=b'\0'*128)
ds.PatientID = 'TEST001'
ds.StudyInstanceUID = '1.2.3.4.5'
ds.Modality = 'CT'
ds.save_as('test.dcm')
print('Created test.dcm')
"

# Upload the test file
curl -X POST -F "file=@test.dcm" http://localhost:8000/upload
```

### Option B: Using Python Test Script
```bash
# In one terminal:
uvicorn main:app --reload

# In another terminal:
python test_dicom_service.py
```

## 4. API Endpoints

### GET / (Health Check)
```
curl http://localhost:8000/
```

**Response:**
```json
{
  "status": "healthy",
  "service": "DICOM Upload Service"
}
```

### POST /upload (Upload DICOM)
```
curl -X POST -F "file=@path/to/file.dcm" http://localhost:8000/upload
```

**Success (200):**
```json
{
  "PatientID": "12345",
  "StudyInstanceUID": "1.2.3.4.5",
  "Modality": "CT"
}
```

**Errors:**
- **400** – Invalid file extension or empty file
- **422** – Invalid DICOM file

## 5. Files Included

- **main.py** – FastAPI application (production-ready)
- **requirements.txt** – Python dependencies
- **test_dicom_service.py** – Comprehensive test suite
- **README.md** – Full documentation

## 6. Key Features

✅ Single POST `/upload` endpoint  
✅ Validates `.dcm` file extension  
✅ Parses DICOM with pydicom  
✅ Extracts PatientID, StudyInstanceUID, Modality  
✅ In-memory processing (no disk persistence)  
✅ Comprehensive error handling  
✅ Structured logging  
✅ Health check endpoint  
✅ Clean, modular code  

## 7. Logs

Watch the console output for detailed logs:
```
2024-01-15 10:23:45,123 - __main__ - INFO - Received upload request for file: scan.dcm
2024-01-15 10:23:45,456 - __main__ - INFO - Successfully parsed DICOM: PatientID=12345
2024-01-15 10:23:45,789 - __main__ - INFO - Successfully processed DICOM file: scan.dcm
```

## 8. Interactive API Docs

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

You can test endpoints directly from the browser!

---

That's it! Your production-ready DICOM service is live. 🚀
