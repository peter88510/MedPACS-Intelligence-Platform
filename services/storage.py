import os
import shutil
from pathlib import Path
from typing import Optional


class StorageService:
    """Handle local file storage for DICOM files."""

    def __init__(self, base_path: str = "./storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_dicom(
        self,
        file_content: bytes,
        patient_id: Optional[str],
        study_instance_uid: Optional[str],
        filename: str
    ) -> str:
        """
        Save DICOM file to local storage.

        Args:
            file_content: Raw file bytes
            patient_id: PatientID from DICOM, or None
            study_instance_uid: StudyInstanceUID from DICOM, or None
            filename: Original filename

        Returns:
            Relative file path from base_path (for DB storage)
        """
        # Handle missing metadata
        patient_dir = patient_id if patient_id else "unknown_patient"
        study_dir = study_instance_uid if study_instance_uid else "unknown_study"

        # Create directory structure
        file_path = self.base_path / patient_dir / study_dir
        file_path.mkdir(parents=True, exist_ok=True)

        # Save file
        full_file_path = file_path / filename
        with open(full_file_path, "wb") as f:
            f.write(file_content)

        # Return relative path for DB storage
        return str(Path(patient_dir) / study_dir / filename)

    def get_full_path(self, relative_path: str) -> str:
        """Get full filesystem path from relative storage path."""
        return str(self.base_path / relative_path)

    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists."""
        return (self.base_path / relative_path).exists()
