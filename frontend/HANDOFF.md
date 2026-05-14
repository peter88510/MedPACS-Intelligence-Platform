# frontend/HANDOFF.md — 後端狀態鏡像

> **文件定位**：本檔反映**當下後端狀態**，供前端 Agent 啟動時讀取以了解可用 API、DB Schema、CORS、env var 等資訊。
>
> **持續更新**：每次主 Agent 派發前端任務前，必須先更新此檔到最新狀態。前端 Agent **每次 session 啟動都要重讀**，不可假設仍是上次內容。
>
> **誰維護**：主 Agent（依根 [`CLAUDE.md`](./CLAUDE.md) §15.5 規定）。**前端 Agent 只讀不寫**。

---

## 目錄

1. [後端基本資訊](#1-後端基本資訊)
2. [環境變數](#2-環境變數)
3. [可用 API Endpoint](#3-可用-api-endpoint)
4. [DB Schema](#4-db-schema)
5. [驗證規則](#5-驗證規則)
6. [已知未實作的 endpoint](#6-已知未實作的-endpoint)
7. [最近重大變更](#7-最近重大變更)
8. [文件維護](#8-文件維護)

---

## 1. 後端基本資訊

| 項目 | 值 |
|---|---|
| 服務名稱 | MedPACS Intelligence Platform Backend |
| 框架 | FastAPI + SQLAlchemy 2.0 + pydicom |
| 預設 base URL（dev） | `http://localhost:8000` |
| 啟動指令 | `uvicorn main:app --reload` |
| CORS allowed origins | `["http://localhost:5173"]`（dev only） |
| CORS allow_credentials | `False` |
| CORS allow_methods | `["*"]` |
| CORS allow_headers | `["*"]` |
| Content-Type（一般）| `application/json` |
| Content-Type（DICOM 下載）| `application/dicom` |

> 修改 `vite.config.ts` 的 `server.port` 會破壞 CORS 對齊。若一定要改，需先回報主 Agent 更新後端 `CORSMiddleware`。

---

## 2. 環境變數

| 變數名 | 必填 | 預設 | 用途 |
|---|---|---|---|
| `DATABASE_URL` | ✅ 是 | 無（Pydantic Settings 會拋錯） | PostgreSQL 連線 URL |
| `UPLOAD_STORAGE_PATH` | ❌ 否 | `./storage` | DICOM 本地儲存根目錄 |

前端目前不直接使用任何 backend env var。Frontend 自己的 `VITE_API_BASE_URL`（未來才導入）由前端控制。

---

## 3. 可用 API Endpoint

> 所有 endpoint 來自 `main.py`。底下 schema 為實際 response 結構（含欄位順序）；型別參考 `models.py` 與 `db_service.py`。

### 3.1 系統

#### `GET /health`

**用途**：liveness check
**Response 200**：
```json
{ "status": "ok", "version": "2.0" }
```

### 3.2 Upload

#### `POST /upload`

**用途**：上傳 DICOM 檔（multipart）
**Body**：`multipart/form-data` with field `file` (binary DICOM)
**Response 200**：
```json
{
  "filename": "patient_001.dcm",
  "patient_id": "P12345",
  "study_instance_uid": "1.2.3.4.5.6.7",
  "modality": "US",
  "message": "DICOM file uploaded and processed successfully"
}
```
**Response 400**（驗證失敗 / 非合法 DICOM）：
```json
{ "error": "Missing or empty required DICOM field: PixelData" }
```
**Response 500**（後端 / 儲存錯誤）：標準 FastAPI `HTTPException` 格式

> ⚠️ **MVP 期間前端不實作 upload UI**（見 `PLAN.md` §10.5、`frontend/IMPLEMENTATION.md` §11）。Upload 流程仰賴 curl / Postman / 其他工具。

### 3.3 查詢

#### `GET /studies`

**用途**：列出所有 study
**Response 200**：
```json
{
  "studies": [
    { "id": 1, "study_instance_uid": "1.2.840...", "patient_id": "P12345", "modality": "US", "created_at": "..." },
    ...
  ]
}
```

> **欄位順序與型別由 `_row()` helper 從 ORM `__dict__` 還原**；目前回傳所有非 `_sa_instance_state` 欄位。若後端 schema 異動，response 會自動 reflect。

#### `GET /series/{id}`

**用途**：依 DB primary key 取單一 series
**URL param**：`id` (int) — Series 表的 DB id（非 UID）
**Response 200**：Series ORM dump
```json
{ "id": 10, "series_instance_uid": "1.2.3.4", "study_instance_uid": "1.2.3", "created_at": "..." }
```
**Response 404**：
```json
{ "detail": "Series with id 99 not found" }
```

#### `GET /instances/{id}`

**用途**：依 DB primary key 取單一 instance
**URL param**：`id` (int)
**Response 200**：
```json
{ "id": 100, "sop_instance_uid": "1.2.3.4.5", "file_path": "P001/1.2.3/file.dcm", "study_instance_uid": "1.2.3", "created_at": "..." }
```
**Response 404**：同上

### 3.4 Viewer-facing

#### `GET /instances/{id}/file`

**用途**：下載原始 DICOM 檔（給 CornerstoneJS `wadouri:` 使用）
**URL param**：`id` (int)
**Response 200**：
- `Content-Type: application/dicom`
- Body: binary DICOM
- Header: `Content-Disposition: attachment; filename=...`
**Response 404**：instance 不存在 **或** 檔案不在 disk

#### `GET /instances/{id}/metadata`

**用途**：取 instance metadata（flat dict）給 MetadataPanel 顯示
**URL param**：`id` (int)
**Response 200**：
```json
{ "id": 100, "sop_instance_uid": "1.2.3.4.5", "file_path": "...", "study_instance_uid": "1.2.3", "created_at": "..." }
```
**Response 404**：同上

### 3.5 AI（**目前皆為 stub**）

#### `POST /ai/segment/{id}`

**用途**：觸發 AI 分割（目前為 stub）
**URL param**：`id` (int)
**Response 200**（stub）：
```json
{ "instance_id": 1, "status": "queued", "message": "Segmentation job accepted (stub)" }
```
**Response 404**：instance 不存在

⚠️ **Stub limitation**：實際無分割邏輯、無 DB 寫入、無 mask 產生。Phase 3 才會接通 PyTorch。

#### `GET /ai/result/{id}`

**用途**：取 AI 分割結果（目前為 stub）
**URL param**：`id` (int)
**Response 200**（stub）：
```json
{ "instance_id": 1, "status": "completed", "result": { "mask": "stub_mask_data", "confidence": 0.95 } }
```

⚠️ **Stub limitation**：永遠回相同的 mock 結果，不論是否曾呼叫過 `POST /ai/segment`。`result.mask` 是字串 `"stub_mask_data"`，**不是真實 PNG URL**。

---

## 4. DB Schema

> 由 Alembic 管理（baseline migration `20809e26d134`）。詳見 `IMPLEMENTATION.md` 的 Database Schema 章節。

### 4 個表 + Alembic 追蹤表

| Table | PK | Unique | FK | 備註 |
|---|---|---|---|---|
| `patients` | `id` | `patient_id` | — | Patient upsert key |
| `studies` | `id` | `study_instance_uid` | `patient_id` → `patients.patient_id` | 含 `modality` |
| `series` | `id` | （無）| `study_instance_uid` → `studies.study_instance_uid` | `series_instance_uid` 有 index 但**不 unique** |
| `instances` | `id` | `sop_instance_uid` | `study_instance_uid` → `studies.study_instance_uid` | 含 `file_path` 相對路徑 |
| `alembic_version` | `version_num` | — | — | Alembic 內部使用、前端無關 |

### 前端要注意的 ID 語義差別

- **DB primary key (`id`)**：自增整數，每張表獨立 — 大部分 endpoint URL 使用此 ID
- **DICOM UID（`study_instance_uid` / `series_instance_uid` / `sop_instance_uid`）**：醫療影像產業標準的唯一識別字串，跨表用來建立關聯

前端 fetch 時：**用 DB id**（如 `/instances/{id}`），不要直接用 SOPInstanceUID 當 URL 參數。

---

## 5. 驗證規則

### 5.1 上傳必填欄位（拒絕 HTTP 400）

- PatientID
- StudyInstanceUID
- SeriesInstanceUID
- SOPInstanceUID
- Modality
- PixelData（二進位欄位，用 `hasattr` 檢查）

### 5.2 Modality 白名單

僅接受 **`US`**（Ultrasound）。其他值（CT / MR 等）→ HTTP 400 `Modality '<X>' is not accepted`。

### 5.3 Error response 格式

驗證失敗：
```json
{ "error": "<message>" }
```

其他錯誤（FastAPI default）：
```json
{ "detail": "<message>" }
```

> 前端錯誤處理時要區分 `error` 欄位（來自 `JSONResponse`）與 `detail` 欄位（來自 `HTTPException`）。

---

## 6. 已知未實作的 endpoint

> 前端規劃時可能會需要、但**目前後端未提供**。若前端任務需要這些，應產出「後端需求清單」回報主 Agent，**不可自行 mock**。

| 期望 endpoint | 用途 | 後端目前狀態 |
|---|---|---|
| `GET /studies/{id}/series` | 列出該 study 的所有 series | ❌ 不存在；目前只能透過 hack（fetch 全部 instances 過濾）|
| `GET /series/{id}/instances` | 列出該 series 的所有 instance | ❌ 不存在 |
| `GET /ai/result/{id}/mask` | 回真實 PNG mask（含 `image/png` content-type）| ❌ 不存在；現有 `/ai/result/{id}` 僅回 stub JSON |
| 真實 AI 推論（背後機制） | `POST /ai/segment/{id}` 實際跑 PyTorch | ❌ 僅 stub 回 `queued` |
| Cancel running AI job | 中止已觸發的 AI | ❌ Out of scope（MVP） |
| Server-Sent Events / WebSocket for AI progress | 串流推論進度 | ❌ Out of scope（MVP 同步推論） |

---

## 7. 最近重大變更

> 主 Agent 在每次重大後端變更後**必須更新此節**。前端 Agent 啟動時看到新項目應該重新確認自己的整合是否仍對齊。

| 日期 | 變更 | 對前端的影響 |
|---|---|---|
| 2026-05-12 | CORSMiddleware 加入、allow `localhost:5173` | 前端 dev origin 鎖定為 5173；改 port 需先同步後端 |
| 2026-05-12 | 驗證層補齊 — 上傳必填欄位從 3 個增為 6 個 | 不影響前端（前端不做 upload UI），但若前端日後加上傳功能，需了解這些必填要求 |
| 2026-05-12 | Alembic 導入 + baseline migration | 不影響前端，但表示後端 schema 從此走 migration 流程，前端不需擔心「DB schema 是否與 ORM 同步」 |
| 2026-05-12 | in-memory SQLite + StaticPool（測試用）| 不影響前端 |
| 2026-05-13 | 文件重組（後端 + 前端拆 hybrid 架構）| `IMPLEMENTATION.md` 加 Frontend Overview、`README.md` 拓寬為雙端視角 |
| 2026-05-13 | 建立前後端分工機制（CLAUDE.md §15.5、`frontend/CLAUDE.md`、本檔）| 前端 Agent 啟動流程改變：必讀本檔最新版 |

> ⏸ **目前無 in-flight 後端變更**。下次更新時機：當主 Agent 在派發新前端任務前發現有新的 API、schema、env var、CORS 異動時。

---

## 8. 文件維護

| 項目 | 說明 |
|---|---|
| 文件版本 | v1.0 |
| 建立日期 | 2026-05-13 |
| 維護者 | 主 Agent（依 CLAUDE.md §15.5）|
| 更新時機 | 派發前端任務前；後端 API / schema / CORS / env var 異動後 |
| 讀取頻率 | 前端 Agent 每次 session 啟動必讀 |
| 更新方式 | 主 Agent 直接編輯本檔；不需工程師 review，但**重大變更**仍應由工程師確認 |
