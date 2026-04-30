# Validation Layer

## Active Rules

| Rule | Behaviour |
|---|---|
| Required fields | `PatientID`, `StudyInstanceUID`, `Modality` must be present and non-empty |
| Modality allowlist | Only `US` (Ultrasound) is accepted |

Any violation returns **HTTP 400** with `{"error": "<reason>"}`. The upload is rejected before any storage or DB write occurs.

---

## How to Add a New Rule

1. Open `validation/dicom_validator.py`.
2. Write a new `_check_*` function that raises `ValidationError` on failure.
3. Call it from `validate_dicom()`.

```python
# Example: reject datasets with no pixel data
def _check_pixel_data(ds) -> None:
    if not hasattr(ds, "PixelData"):
        raise ValidationError("DICOM file contains no pixel data")

def validate_dicom(ds) -> None:
    _check_required_fields(ds)
    _check_modality(ds)
    _check_pixel_data(ds)   # ← add here
```

No other file needs to change.
