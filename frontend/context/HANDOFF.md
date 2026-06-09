# frontend/context/HANDOFF.md — 後端狀態鏡像

> **文件定位**：本檔反映**當下後端狀態**，供前端 Agent 啟動時讀取以了解可用 API、DB Schema、CORS、env var 等資訊。
>
> **持續更新**：每次主 Agent 派發前端任務前，必須先更新此檔到最新狀態。前端 Agent **每次 session 啟動都要重讀**，不可假設仍是上次內容。
>
> **誰維護**：主 Agent（依根 [`CLAUDE.md`](../../CLAUDE.md) §15.5 規定）。**前端 Agent 只讀不寫**。

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

> **完整 endpoint 清單**（path / method / handler / line / docstring）由 generator 自動從 `main.py` 抓出：
> → [`../../docs/generated/api_spec.md`](../../docs/generated/api_spec.md)（**權威來源、自動產生**）
>
> 本節僅補充 generator 抓不到的設計細節。

### 3.1 Response 欄位由 `_row()` helper 推導

查詢類 endpoint（`/studies`、`/series/{id}`、`/instances/{id}`、`/instances/{id}/metadata`）使用 `main.py:_row()` helper 從 ORM `__dict__` 還原，**回傳所有非 `_sa_instance_state` 欄位**。

含意：DB schema 變動時，response 欄位自動 reflect（無需改 handler）。前端應假設「欄位 ≈ DB 欄位」並參考 `docs/generated/db_schema.md`。

`POST /upload` 例外：response 為 handler 內手組 dict（非 `_row()`），包含 `instance_id`（int，新建 instance 的 DB pk）+ `filename` / `patient_id` / `study_instance_uid` / `modality` / `message` + **`duplicate` (bool，2026-05-19 加)**。**`instance_id` 是後續 `/instances/{id}/file` 等 endpoint 的入口參數**（2026-05-14 加入）。

**Duplicate detection (2026-05-19)**：
- `duplicate=false`：新 instance 建立（既有行為）
- `duplicate=true` + 200：同 SOPInstanceUID + 同 bytes 重傳 → idempotent、回既有 `instance_id`、不寫新檔
- HTTP **409 Conflict**：同 SOPInstanceUID 但 bytes 不同（hash mismatch）→ response 含 `existing_instance_id` / `existing_hash` / `new_hash` / `suggested_actions` 三選一 (keep_existing / save_as_new / manual_overwrite)；額外 `existing_file_missing=true` 表 DB 有記錄但 storage 上原檔被誤刪、需手動清理

### 3.2 Error response 兩種格式

| 觸發情境 | 來源 | 格式 |
|---|---|---|
| DICOM 驗證失敗（`POST /upload`） | `JSONResponse` | `{"error": "..."}` |
| **Duplicate 衝突**（`POST /upload` 同 SOP UID 不同 bytes、2026-05-19 加） | `JSONResponse` 409 | `{"detail": "...", "existing_instance_id": int, "existing_hash": "...", "new_hash": "...", "suggested_actions": {...}}` |
| 其他錯誤（404、500、`InvalidDicomError`...） | FastAPI `HTTPException` | `{"detail": "..."}` |

前端錯誤處理要區分這三類欄位結構。

### 3.3 Stub endpoints 限制（Phase 3 才會接通）

| Endpoint | 目前行為 |
|---|---|
| `POST /ai/segment/{id}` | 不實際做事，僅回 `{"instance_id": id, "status": "queued", "message": "Segmentation job accepted (stub)"}` |
| `GET /ai/result/{id}` | 永遠回固定 mock：`{"instance_id": id, "status": "completed", "result": {"mask": "stub_mask_data", "confidence": 0.95}}` |

⚠️ `result.mask` 是**字串** `"stub_mask_data"`，**不是真實 PNG URL**。前端 mask overlay 渲染卡在這（見 §6）。

### 3.4 Upload UI 不在 MVP 範圍

> ⚠️ MVP 期間前端不實作 upload UI（見 `docs/PLAN.md` §10.5、`frontend/docs/IMPLEMENTATION.md` §11）。Upload 流程仰賴 curl / Postman / 其他工具。但 backend `POST /upload` 仍是完整實作（非 stub）。

---

## 4. DB Schema

> **完整 schema**（欄位、型別、PK / Unique / Index / FK、最新 Alembic revision）由 generator 自動從 `models/` + alembic 抓出：
> → [`../../docs/generated/db_schema.md`](../../docs/generated/db_schema.md)（**權威來源、自動產生**）
>
> 本節僅補充 generator 抓不到的設計細節。

### 4.1 DB id vs DICOM UID 語義差別（前端必懂）

- **DB primary key (`id`)**：自增整數，每張表獨立 — **大部分 endpoint URL 使用此 ID**
- **DICOM UID**（`study_instance_uid` / `series_instance_uid` / `sop_instance_uid`）：醫療影像產業標準的唯一識別字串，跨表用來建立關聯

前端 fetch 時：用 `/instances/{db_id}`，**不要**用 SOPInstanceUID 當 URL 參數。

### 4.2 alembic_version 表（generator 不列）

Alembic 在 DB 多建一張 `alembic_version`（單欄、單列、記錄目前 migration revision）。**前端無關**、不會出現在任何 API。`docs/generated/db_schema.md` 由 `Base.metadata.tables` 推導，**不含**此表 — 描述正確。

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
| `GET /studies/{id}/series` | 列出該 study 的所有 series | ✅ **已實作（2026-05-15）**；response `{"series": [...]}`；2026-05-15 前 upload 沒寫 series 表，舊 study 會回 `[]` 直到累積新上傳資料 |
| `GET /series/{id}/instances` | 列出該 series 的所有 instance | ✅ **已實作（2026-05-15）**；response `{"instances": [...]}`；2026-05-15 前 upload 的 instances `series_instance_uid` 為 NULL、無法被新 endpoint 匹配（legacy gap，MVP 接受） |
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
| 2026-05-14 | API spec / DB schema 改為 auto-generated（`docs/generated/`） | 前端應從 generated 檔讀完整 spec；本檔 §3 / §4 退化為「補充說明」，不再 duplicate spec |
| 2026-05-14 | `POST /upload` response 加 `instance_id`（int、新建 instance 的 DB pk）| 前端任務 #9 的 upload UI（若日後實作）+ MVP 期間工程師驗收都能單一 round-trip 拿到 id，不用繞 psql |
| 2026-05-15 | **Series 結構補完**（migration `e25c80289a9c`）：① `series.series_instance_uid` UNIQUE+NOT NULL ② `instances.series_instance_uid` ADD COLUMN+FK→series ③ upload pipeline 加 series upsert ④ 新 endpoints `GET /studies/{id}/series` + `GET /series/{id}/instances` | 解除前端 §6 兩個「不存在」endpoint 的阻擋；StudyList 完整版可實作；DicomViewer 可在同一 series 內切換 instance。**注意**：2026-05-15 前 upload 的 instances 與 series 都沒 series link，新 endpoints 對舊資料會回空陣列 |
| 2026-05-18 | **§5.4 backfill apply** — `scripts/backfill_series_uid.py --apply` 補 3 個 pre-2026-05-15 orphan instances (id=1/3/4) 的 `series_instance_uid='...593537'` | 前端 StudyList 重整後會看到完整 8 個 instances（從 5 個變 8 個）；API `/series/1/instances` 從 5 筆 → 8 筆；schema 未變、API contract 未變 |
| 2026-05-19 | **Phase 3 task #10：AIResult 表** (Alembic migration `91725486ef55`) | DB schema 新增 `ai_results` 表（5 tables total）；前端目前不直接 query、僅當 `/ai/result/{id}` endpoint 真實實作後才會反映；schema 詳細見 `docs/generated/db_schema.md` |
| 2026-05-19 | **`POST /upload` duplicate detection** (PROGRESS §6.12 修復) | response 新增 `duplicate` bool；新增 409 conflict status code；若前端日後加 upload UI，需處理 200+duplicate / 409 兩個新分支。詳 §3.1 / §3.2 |

> ⏸ **目前無 in-flight 後端變更**。下次更新時機：當主 Agent 在派發新前端任務前發現有新的 API、schema、env var、CORS 異動時（spec 變動會自動進 `docs/generated/`，本檔 §3.x / §4.x 只在「補充說明」需新增 / 修正時動）。

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
