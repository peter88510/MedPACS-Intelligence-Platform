# ============================================================
# PATCH: Day 5 – Validation Layer
# Apply these two changes to main.py. Nothing else changes.
# ============================================================

# ── 1. ADD these two imports at the top of main.py ──────────
from validation.dicom_validator import validate_dicom
from validation.exceptions import ValidationError


# ── 2. INSERT try/except block AFTER `ds = dcmread(...)` ────
#    (i.e. after pydicom parsing, before storage/DB calls)
#
#    BEFORE (existing code, untouched):
#        ds = dcmread(tmp_path)
#
#    ADD immediately after:
try:
    validate_dicom(ds)
except ValidationError as e:
    return JSONResponse(status_code=400, content={"error": str(e)})

#    The rest of the endpoint (storage + DB) remains unchanged.
