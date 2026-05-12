# Validation Layer

## Active Rules

| Rule | Behaviour |
|---|---|
| Required string fields | `PatientID`, `StudyInstanceUID`, `SeriesInstanceUID`, `SOPInstanceUID`, `Modality` must be present and non-empty |
| Modality allowlist | Only `US` (Ultrasound) is accepted |
| PixelData presence | `PixelData` tag must exist (binary, checked via `hasattr`) |

Any violation returns **HTTP 400** with `{"error": "<reason>"}`. The upload is rejected before any storage or DB write occurs.

---

## How to Add a New Rule

1. Open `validation/dicom_validator.py`.
2. Write a new `_check_*` function that raises `ValidationError` on failure.
3. Call it from `validate_dicom()`.

No other file needs to change.
