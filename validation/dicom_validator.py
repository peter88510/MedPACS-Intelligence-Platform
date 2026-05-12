from validation.exceptions import ValidationError

# String-valued tags that must be present and non-empty.
# PixelData is binary, checked separately by _check_pixel_data().
REQUIRED_FIELDS = [
    "PatientID",
    "StudyInstanceUID",
    "SeriesInstanceUID",
    "SOPInstanceUID",
    "Modality",
]

# Only this modality is accepted
ALLOWED_MODALITIES = {"US"}


def validate_dicom(ds) -> None:
    """
    Validate a pydicom Dataset before storage and DB write.

    Raises:
        ValidationError: if any required field is missing/empty,
                         if Modality is not in ALLOWED_MODALITIES,
                         or if PixelData is absent.
    """
    _check_required_fields(ds)
    _check_modality(ds)
    _check_pixel_data(ds)


# ---------------------------------------------------------------------------
# Internal rule functions — add new rules here as standalone functions
# ---------------------------------------------------------------------------

def _check_required_fields(ds) -> None:
    """Reject if any required DICOM tag is absent or blank."""
    for field in REQUIRED_FIELDS:
        value = getattr(ds, field, None)
        if value is None or str(value).strip() == "":
            raise ValidationError(
                f"Missing or empty required DICOM field: {field}"
            )


def _check_modality(ds) -> None:
    """Reject if Modality is not in the allowed set."""
    modality = str(getattr(ds, "Modality", "")).strip()
    if modality not in ALLOWED_MODALITIES:
        raise ValidationError(
            f"Modality '{modality}' is not accepted. "
            f"Allowed: {', '.join(sorted(ALLOWED_MODALITIES))}"
        )


def _check_pixel_data(ds) -> None:
    """Reject if PixelData tag is absent — image cannot be rendered without it."""
    if not hasattr(ds, "PixelData"):
        raise ValidationError("Missing required DICOM field: PixelData")
