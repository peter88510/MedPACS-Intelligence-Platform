<!-- AUTO-GENERATED — DO NOT EDIT -->
<!-- Source: main.py -->
<!-- Generator: scripts/gen_api_spec.py -->
<!-- Last regenerated against git HEAD: 9f00ac7 -->

# API Spec (Generated)

> 本檔由 `scripts/gen_api_spec.py` 從 `main.py` 自動產生。
> **不要人工編輯**。修改 `main.py` 後再次執行（或由 pre-commit hook 自動觸發）。

**Backend base URL (dev)**: `http://localhost:8000`

---

## `GET /ai/result/{id}`

**Handler**: `main.py:ai_result` (line 430)

回傳某 instance 最新一筆 AI 結果。尚未跑過 → 404（提示先 POST /ai/segment）。

    `?status=completed`（選用）：只取最新一筆 completed，繞過失敗重跑寫的 error 紀錄
    遮蔽好結果的問題；省略則回任意最新（向後相容）。

## `GET /ai/result/{id}/mask`

**Handler**: `main.py:ai_result_mask` (line 476)

回傳某 instance 最新一筆 AI 結果的 mask PNG（前端 overlay 用）。

    mask 由 POST /ai/segment 當下產生（paddleseg pseudo_color_prediction）並存於病患
    storage 樹；本 endpoint 純讀檔回傳、不重跑推論（對 AI stack 零依賴）。
    `?status=completed`（選用）：與 /ai/result 一致，只取最新 completed 那筆的 mask。
    無 instance / 無結果 / 該結果無 mask / 檔案不在磁碟 → 各自明確 404。

## `POST /ai/segment/{id}`

**Handler**: `main.py:ai_segment` (line 320)

對某 instance 跑 AI 橫膈膜量測，結果寫入 ai_results（同步、LEGACY mode）。

    流程（design §6）：解析 measurement type → 醫療安全分支（unknown 422 / thickness
    501）→ 跑引擎（缺相依 503 / 推論失敗 500）→ 序列化 envelope + 寫 ai_results。
    回應全 additive（取代原 stub 的 queued 回應）。

## `GET /health`

**Handler**: `main.py:health_check` (line 242)

Health check endpoint.

## `GET /instances/{id}`

**Handler**: `main.py:get_instance` (line 286)

_(no docstring)_

## `GET /instances/{id}/file`

**Handler**: `main.py:download_instance_file` (line 298)

_(no docstring)_

## `GET /instances/{id}/metadata`

**Handler**: `main.py:get_instance_meta` (line 312)

_(no docstring)_

## `GET /series/{id}`

**Handler**: `main.py:get_series` (line 262)

_(no docstring)_

## `GET /series/{id}/instances`

**Handler**: `main.py:list_instances_for_series` (line 278)

_(no docstring)_

## `GET /studies`

**Handler**: `main.py:list_studies` (line 256)

_(no docstring)_

## `GET /studies/{id}/series`

**Handler**: `main.py:list_series_for_study` (line 270)

_(no docstring)_

## `POST /upload`

**Handler**: `main.py:upload` (line 94)

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

_Generated 12 routes._
