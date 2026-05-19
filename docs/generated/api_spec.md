<!-- AUTO-GENERATED — DO NOT EDIT -->
<!-- Source: main.py -->
<!-- Generator: scripts/gen_api_spec.py -->
<!-- Last regenerated against git HEAD: e8d4250 -->

# API Spec (Generated)

> 本檔由 `scripts/gen_api_spec.py` 從 `main.py` 自動產生。
> **不要人工編輯**。修改 `main.py` 後再次執行（或由 pre-commit hook 自動觸發）。

**Backend base URL (dev)**: `http://localhost:8000`

---

## `GET /ai/result/{id}`

**Handler**: `main.py:ai_result` (line 297)

_(no docstring)_

## `POST /ai/segment/{id}`

**Handler**: `main.py:ai_segment` (line 284)

_(no docstring)_

## `GET /health`

**Handler**: `main.py:health_check` (line 206)

Health check endpoint.

## `GET /instances/{id}`

**Handler**: `main.py:get_instance` (line 250)

_(no docstring)_

## `GET /instances/{id}/file`

**Handler**: `main.py:download_instance_file` (line 262)

_(no docstring)_

## `GET /instances/{id}/metadata`

**Handler**: `main.py:get_instance_meta` (line 276)

_(no docstring)_

## `GET /series/{id}`

**Handler**: `main.py:get_series` (line 226)

_(no docstring)_

## `GET /series/{id}/instances`

**Handler**: `main.py:list_instances_for_series` (line 242)

_(no docstring)_

## `GET /studies`

**Handler**: `main.py:list_studies` (line 220)

_(no docstring)_

## `GET /studies/{id}/series`

**Handler**: `main.py:list_series_for_study` (line 234)

_(no docstring)_

## `POST /upload`

**Handler**: `main.py:upload` (line 65)

Upload and process DICOM file.
    
    API CONTRACT UNCHANGED:
    - Input: multipart file upload
    - Output: JSON with metadata (same as before)
    
    NEW INTERNAL BEHAVIOR:
    - Parse DICOM (existing logic)
    - Save file to local storage
    - Upsert into PostgreSQL
    - Return same response

---

_Generated 11 routes._
