from validation.exceptions import ValidationError

# Tags that must be present and non-empty
REQUIRED_FIELDS = ["PatientID", "StudyInstanceUID", "Modality"]

# Only this modality is accepted
ALLOWED_MODALITIES = {"US"}


def validate_dicom(ds) -> None:
    """
    Validate a pydicom Dataset before storage and DB write.

    Raises:
        ValidationError: if any required field is missing/empty,
                         or if Modality is not in ALLOWED_MODALITIES.
    """
    _check_required_fields(ds)
    _check_modality(ds)


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
