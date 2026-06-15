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

// ---- AI 量測 contract（對齊後端真實形狀，見 HANDOFF.md §3.3 / §3.3.1）----

// 單筆量測。crest / trough 為 [x, y] 像素座標（column, row），落在完整原圖座標系
// （instance 12 實測：x∈[103,699]≈Columns 720、y∈[285,326]<Rows 930）。
// 前端 overlay 直接用這組座標在原影像上畫 marker（不需 mask PNG）。
export interface Measurement {
  batch_index: number
  excursion_cm: number | null
  excursion_pixel: number | null
  time_pixel: number | null
  time_sec: number | null
  velocity: number | null
  crest: [number, number]
  trough: [number, number]
}

// result 欄的完整 envelope
export interface AIResultEnvelope {
  schema_version: number
  measurement_type: string
  pipeline_mode: string
  model_name: string
  model_version: string
  measurements: Measurement[]
  primary: { label: string; value: number | null; unit: string | null }
}

// POST /ai/segment/{id} 成功回傳
export interface AISegmentResponse {
  instance_id: number
  ai_result_id: number
  status: string
  measurement_type: string
  primary_value: number | null
  primary_unit: string | null
  measurement_count: number
}

// GET /ai/result/{id} 回最新一筆；status="error" 時 result 可能為 null
export interface AIResultResponse {
  instance_id: number
  ai_result_id: number
  status: string
  measurement_type: string
  model_name: string
  model_version: string
  primary_value: number | null
  primary_unit: string | null
  confidence: number | null
  mask_url: string | null
  result: AIResultEnvelope | null
  error_message: string | null
  created_at: string
}
