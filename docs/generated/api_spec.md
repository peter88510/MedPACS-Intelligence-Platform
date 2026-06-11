<!-- AUTO-GENERATED — DO NOT EDIT -->
<!-- Source: main.py -->
<!-- Generator: scripts/gen_api_spec.py -->
<!-- Last regenerated against git HEAD: 39821ce -->

# API Spec (Generated)

> 本檔由 `scripts/gen_api_spec.py` 從 `main.py` 自動產生。
> **不要人工編輯**。修改 `main.py` 後再次執行（或由 pre-commit hook 自動觸發）。

**Backend base URL (dev)**: `http://localhost:8000`

---

## `GET /ai/result/{id}`

**Handler**: `main.py:ai_result` (line 401)

回傳某 instance 最新一筆 AI 結果。尚未跑過 → 404（提示先 POST /ai/segment）。

## `POST /ai/segment/{id}`

**Handler**: `main.py:ai_segment` (line 306)

對某 instance 跑 AI 橫膈膜量測，結果寫入 ai_results（同步、LEGACY mode）。

    流程（design §6）：解析 measurement type → 醫療安全分支（unknown 422 / thickness
    501）→ 跑引擎（缺相依 503 / 推論失敗 500）→ 序列化 envelope + 寫 ai_results。
    回應全 additive（取代原 stub 的 queued 回應）。

## `GET /health`

**Handler**: `main.py:health_check` (line 228)

Health check endpoint.

## `GET /instances/{id}`

**Handler**: `main.py:get_instance` (line 272)

_(no docstring)_

## `GET /instances/{id}/file`

**Handler**: `main.py:download_instance_file` (line 284)

_(no docstring)_

## `GET /instances/{id}/metadata`

**Handler**: `main.py:get_instance_meta` (line 298)

_(no docstring)_

## `GET /series/{id}`

**Handler**: `main.py:get_series` (line 248)

_(no docstring)_

## `GET /series/{id}/instances`

**Handler**: `main.py:list_instances_for_series` (line 264)

_(no docstring)_

## `GET /studies`

**Handler**: `main.py:list_studies` (line 242)

_(no docstring)_

## `GET /studies/{id}/series`

**Handler**: `main.py:list_series_for_study` (line 256)

_(no docstring)_

## `POST /upload`

**Handler**: `main.py:upload` (line 80)

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
