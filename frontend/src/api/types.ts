export interface Study {
  id: number
  patient_id: string
  study_instance_uid: string
  modality: string | null
  created_at: string | null
}

export interface Series {
  id: number
  series_instance_uid: string | null
  study_instance_uid: string
  created_at: string | null
}

export interface Instance {
  id: number
  sop_instance_uid: string | null
  file_path: string
  study_instance_uid: string
  series_instance_uid?: string | null
  created_at: string | null
}

// DICOM metadata shape varies per file; keep loose. Keys are typically
// DICOM tag names (e.g. "PatientID", "Modality", "Rows", "Columns").
export type InstanceMetadata = Record<string, unknown>

export interface AISegmentResponse {
  instance_id: number
  status: string
  message: string
}

export interface AIResultResponse {
  instance_id: number
  status: string
  result: {
    mask: string
    confidence: number
  }
}
