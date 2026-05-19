# PROGRESS.md — 專案現況 (Project Status)

> **文件定位**：本檔僅記錄「狀態與進度」。
> 架構說明請見 [docs/IMPLEMENTATION.md](./docs/IMPLEMENTATION.md)、操作教學請見 [docs/archive/QUICKSTART.md](./docs/archive/QUICKSTART.md)、AI 行為約束請見 [CLAUDE.md](./CLAUDE.md)。
>
> **更新規則**：每完成一項任務、變更狀態、或調整下一步時，同步更新本檔。

---

## 目錄

1. [已完成功能](#1-已完成功能)
2. [API 端點狀態表](#2-api-端點狀態表)
3. [測試覆蓋簡況](#3-測試覆蓋簡況)
4. [進行中](#4-進行中)
5. [下一步（短期、已排程）](#5-下一步短期已排程)
6. [已知缺口（中長期、未排程）](#6-已知缺口中長期未排程)
7. [目錄結構](#7-目錄結構)
8. [文件維護](#8-文件維護)

---

## 1. 已完成功能

### 核心業務
- [x] DICOM 上傳 API（POST /upload）
- [x] **Upload duplicate detection**（2026-05-19）— SOP UID + SHA256 hash 偵測；同 SOP+同 bytes → 200 idempotent + `duplicate=true`；同 SOP+不同 bytes → 409 + existing_instance_id/hashes/suggested_actions（CLAUDE.md §13 「不靜默覆蓋」遵循）
- [x] DICOM magic bytes 驗證
- [x] DICOM 必填欄位驗證（PatientID / StudyInstanceUID / SeriesInstanceUID / SOPInstanceUID / Modality / PixelData）
- [x] Modality 白名單驗證（目前僅允許 `US`）
- [x] Patient upsert（依 patient_id 唯一性）
- [x] Study upsert(依 study_instance_uid 唯一性)
- [x] **Series upsert（依 series_instance_uid，2026-05-15 補完 — 此前 upload pipeline 跳過 series 表寫入）**
- [x] Instance 建立（依 sop_instance_uid 唯一性 + 2026-05-15 加 series_instance_uid FK）
- [x] DICOM 檔案本地儲存（路徑：`{storage}/{patient_id}/{study_uid}/{filename}.dcm`）

### 查詢能力
- [x] 列出所有研究（GET /studies）
- [x] 取得指定系列（GET /series/{id}）
- [x] **列出指定研究的所有系列（GET /studies/{id}/series，2026-05-15）**
- [x] **列出指定系列的所有實例（GET /series/{id}/instances，2026-05-15）**
- [x] 取得指定實例（GET /instances/{id}）
- [x] 下載原始 DICOM 檔案（GET /instances/{id}/file）
- [x] 取得實例 metadata（GET /instances/{id}/metadata）
- [x] 健康檢查（GET /health）

### 架構與基礎設施
- [x] 四層分離架構（API → Service → Model → DB）
- [x] FastAPI dependency injection
- [x] SQLAlchemy 2.0 ORM 整合 PostgreSQL
- [x] Pydantic v2 Settings 環境配置
- [x] StorageBackend 抽象層（為未來 S3 遷移預留）
- [x] LocalStorageBackend 實作
- [x] 自動 DB 初始化（`init_db()`，已被 Alembic 取代為 canonical 路徑，保留向後相容） — ⚠️ 仍有 race condition with alembic、見 §6.13
- [x] 驗證層模組化（`validation/`）
- [x] **Alembic 導入 + baseline migration**（涵蓋 patients / studies / series / instances 四表，upgrade/downgrade 雙向已驗證）
- [x] **AIResult model + Alembic migration `91725486ef55`**（Phase 3 task #10、2026-05-19）— PLAN §9.3 schema scaffolding；不接 PyTorch（工程師親自串接演算法/模型）；upgrade/downgrade round-trip 驗證通過

### 測試與品質
- [x] 33 個測試案例（單元 / 整合 / API 三層）
- [x] 共用 fixtures（`tests/conftest.py`）
- [x] pytest 配置（`pytest.ini`）
- [x] 測試隔離機制（記憶體 SQLite + monkeypatch）

### Frontend（Phase 2 進行中）
- [x] React 19 + Vite 8 + TypeScript 6 專案骨架（2026-05-13、commit `2d055de`）
- [x] Cornerstone3D v4.22 套件安裝（`@cornerstonejs/core` + `dicom-image-loader` + `tools` + `dicom-parser`）（Stage A、2026-05-13、commit `83b8c9a`）
- [x] CornerstoneJS 初始化設定（`src/cornerstone/setup.ts` idempotent `initCornerstone()` + `main.tsx` async bootstrap）（Stage B、2026-05-14、commit `8cd61f3`）
- [x] **第一張 DICOM 渲染**（`<DicomViewer />` + wadouri scheme + StrictMode-safe + metadata-aware aspect-ratio + 二次 setStack + destroy/recreate engine）（Stage C、2026-05-16、commit `13cccd3`）— UX 缺口已於 task #9 commit 7 `40d766d` (Fix-J) 解決，見 §6.11
- [x] **業務元件層完整 SPA**（task #9、2026-05-16 → 2026-05-18、11 commits `fb656c6` → `fa0dd34`）：API client + `VITE_API_BASE_URL` env var 制度 + AppContext (5 fields + cascade) + Layout/TopBar/StudyList/MetadataPanel/AIPanel + DicomViewer ← AppContext + Vite scaffold 清掉 + Fix-J（CSS 層偵錯解 Stage C UX 缺口）；E2E 瀏覽器驗收 ✅

### 文件
- [x] README.md — 功能概覽與設置指南
- [x] IMPLEMENTATION.md — 架構與模組責任
- [x] QUICKSTART.md — 5 分鐘 API 操作範例（2026-05-14 移至 docs/archive/）
- [x] STORAGE_BACKEND.md — 儲存後端設計與 S3 遷移指南（2026-05-14 移至 docs/archive/）
- [x] CLAUDE.md — AI 操作規範
- [x] PLAN.md — MVP 開發規劃（scope / architecture / API / roadmap / non-goals）

---

## 2. API 端點狀態表

| 方法 | 路徑 | 功能 | 狀態 | 備註 |
|---|---|---|---|---|
| POST | `/upload` | 上傳並處理 DICOM 檔案 | ✅ 完整 | response 含 `instance_id`（2026-05-14 加）+ `duplicate` 欄位（2026-05-19 加，dedup 結果指示）；409 表 SOP UID 衝突 |
| GET | `/health` | 健康檢查 | ✅ 完整 | — |
| GET | `/studies` | 列出所有研究 | ✅ 完整 | — |
| GET | `/studies/{id}/series` | 列出該研究的所有系列 | ✅ 完整 | 2026-05-15 加；舊 study 可能回 `[]` |
| GET | `/series/{id}` | 取得指定系列 | ✅ 完整 | — |
| GET | `/series/{id}/instances` | 列出該系列的所有實例 | ✅ 完整 | 2026-05-15 加；2026-05-15 前的 instances `series_instance_uid` 為 NULL、不會列出 |
| GET | `/instances/{id}` | 取得指定實例 | ✅ 完整 | — |
| GET | `/instances/{id}/file` | 下載原始 DICOM 檔案 | ✅ 完整 | 透過 FileResponse |
| GET | `/instances/{id}/metadata` | 取得實例 metadata | ✅ 完整 | — |
| POST | `/ai/segment/{id}` | 觸發 AI 分割 | ⚠️ **Stub** | 僅回傳 `{"status": "queued"}`，無實作 |
| GET | `/ai/result/{id}` | 取得 AI 分割結果 | ⚠️ **Stub** | 僅回傳 mock 結果 |

**完整度**：9/11 完整實作，2/11 為 stub。

---

## 3. 測試覆蓋簡況

### 總覽
- **總測試數**：52 個
- **執行方式**：`pytest tests/ -v`
- **隔離機制**：記憶體 SQLite + monkeypatch 臨時 storage，每個測試獨立

### 三層分布

| 層級 | 檔案 | 測試數 | 風格 |
|---|---|---|---|
| 整合測試 | `tests/test_dicom_service.py` | 11 | 真實 SQLite 記憶體 DB + 臨時 storage（含 2026-05-15 series upsert / upload-creates-series 兩項 + 2026-05-19 duplicate detection 三項：idempotent / 409 conflict / existing_file_missing） |
| API 測試 | `tests/test_query_api.py` | 29 | TestClient + mock `db_service`（含 2026-05-15 加的 /studies/{id}/series 與 /series/{id}/instances 各 4 cases） |
| ORM 測試 | `tests/test_ai_result_model.py` | 3 | 純 SQLAlchemy model 層（Phase 3 task #10：AIResult CRUD + nullable + Instance.ai_results back-relationship） |
| 單元測試 | `tests/test_validators.py` | 9 | 純邏輯，無 DB / HTTP |

### 已覆蓋路徑
- ✅ DICOM 上傳完整流程（解析 / 儲存 / DB 寫入）
- ✅ Patient / Study upsert 行為
- ✅ Instance 建立行為
- ✅ 所有查詢端點（成功、404、空集合）
- ✅ AI stub 端點回傳格式
- ✅ 驗證層所有規則（必填、Modality 白名單）

### 尚未覆蓋的路徑
- ⚠️ 大檔案上傳（boundary / OOM 行為）
- ⚠️ 並發上傳同一 SOP UID 時的競態
- ⚠️ DB connection 失敗時的 fallback
- ⚠️ 損毀 DICOM 檔案的細部錯誤訊息一致性
- ⚠️ Storage backend 寫入失敗時的 DB rollback

---

## 4. 進行中

> **目前無進行中項目。**

---

## 5. 下一步（短期、已排程）

> 完整規劃見 [docs/PLAN.md](./docs/PLAN.md)。本區塊摘要當前需推進的具體任務，依 PLAN Phase 排序。

### Phase 1 收尾
- [x] 補齊驗證層：`SeriesInstanceUID` / `SOPInstanceUID` / `PixelData` 必填檢查（PLAN §7.1）— ✅ 完成 2026-05-12
- [x] CORS middleware（dev 環境，allow `http://localhost:5173`）（PLAN §8.6）— ✅ 完成 2026-05-12
- [x] **Alembic 導入 + baseline migration**（PLAN §5、§9.3；解除 §6.2 缺口）— ✅ 完成 2026-05-12

**Phase 1 全部完成 — 後續進入 Phase 2（Frontend Viewer）。**

### Phase 2：Frontend Viewer（PLAN §10、§12）
- [x] React + Vite + TypeScript 專案初始化（2026-05-13、commit `2d055de`）
- [x] CornerstoneJS v4.22 整合（Stage A 套件安裝 `83b8c9a` + Stage B 初始化 `8cd61f3`）
- [x] **Stage C：第一張 DICOM 渲染**（commit `13cccd3`、2026-05-16）— UX 缺口已解決於 task #9 commit 7 `40d766d` (Fix-J)、見 §6.11
- [x] **Phase 2 task #9：4 業務元件 + AppContext + API client + env var 制度**（2026-05-16 → 2026-05-18、11 commits `fb656c6` → `fa0dd34`）— 完整 SPA E2E 驗收 ✅、Fix-J 順手解 Stage C UX 缺口
- [x] **Stub AI endpoint 接通 + `<AIPanel />`**（task #9 commit 6 `d66b6ab`）— mask overlay 渲染留 Phase 3 依賴真實 AI

**Phase 2 全部完成 — 後續進入 Phase 3（AI 整合）。**

### Phase 2.5：後端 audit findings 處理（task #9 §5.4 衍生，2026-05-18 工程師裁示先處理）
- [x] **§5.4 (a) 一次性 backfill script**（2026-05-18）— `scripts/backfill_series_uid.py` dry-run + `--apply`、安全機制（重讀 DICOM 確認 SeriesUID + 不自行新建 series）。Apply 結果：3 個 orphan instances (id=1/3/4) 全部補上 series_instance_uid `...593537`、orphan count=0、Series 表未動、API `/series/1/instances` 現在回 8 筆（從 5 筆）
- [x] **§5.4 (c) Instance ID gap 來源澄清**（2026-05-18）— 結論：**PostgreSQL SERIAL sequence 設計、不是 bug**。`instances_id_seq.last_value=10` + 缺 id=[2, 5]，是 transaction rollback 後 sequence 不 reset 的預期行為（避免 race condition）。推測來源：upload 同 SOP UID 重傳被 UNIQUE constraint 擋下 → IntegrityError → rollback。無需修 transaction handling。但發現連帶 issue → 見 §6.12

### Phase 3：AI 整合（PLAN §9、§12）
- [x] **`AIResult` model + Alembic migration `91725486ef55`**（task #10、2026-05-19）— schema scaffolding only；PLAN §9.3 完整實作；3 個 ORM-level test 涵蓋 CRUD + nullable + relationship
- [ ] `ai_service.py` + PyTorch 模型載入（pretrained / mock fallback 路徑見 PLAN §9.4）— ⏸ **工程師親自串接**（2026-05-18 裁示：AI 真實功能優先序低、演算法/模型由工程師接）
- [ ] `/ai/segment/{id}` 同步實作（覆蓋現有 stub）— ⏸ 同上
- [ ] `/ai/result/{id}` + `/ai/result/{id}/mask` 實作（覆蓋現有 stub）— ⏸ 同上
- [ ] 前端 mask overlay 渲染 — ⏸ 等真實 AI endpoint 接通後才派 dispatch

### Phase 4：收尾（PLAN §12、§13）
- [ ] Sample anonymized DICOM 測試資料準備
- [ ] End-to-end demo workflow 演練（5 分鐘內完成 PLAN §13 流程）

---

## 6. 已知缺口（中長期、未排程）

> 以下為「知道缺、但尚未排入近期計畫」的項目。納入 PLAN.md 後即升格為「下一步」。

### 6.1 AI 分割功能（業務）
- **缺什麼**：`/ai/segment/{id}` 與 `/ai/result/{id}` 目前是 stub，無實際分割邏輯、無結果儲存表、無任務佇列
- **什麼時候會痛**：當前端 / 客戶要求 AI 結果可用時，整條鏈都缺
- **相依**：分割模型、結果 schema 設計、任務佇列（Celery / RQ）的選型

### 6.2 Database Migration 框架（基礎設施）
> ✅ **已完成（2026-05-12）**。Alembic 已導入，baseline migration 涵蓋現有四表，upgrade/downgrade 雙向驗證通過。後續所有 schema 變更走 migration script（CLAUDE.md §12 強制）。本條保留以供歷史追溯。

### 6.3 Logging 與 Audit Trail（可觀測性 / 合規）
- **缺什麼**：關鍵操作（DB 寫入、DICOM 解析、檔案儲存）缺少統一 log 記錄；無審計軌跡
- **什麼時候會痛**：production debug、合規稽核、出包還原現場時
- **相依**：CLAUDE.md 第 14 節已定義 logging 規範，但目前程式碼尚未全面落實

### 6.4 身份驗證 / 授權（安全）
- **缺什麼**：所有端點皆無保護，任何人可上傳、查詢、下載
- **什麼時候會痛**：系統對外曝露、多用戶情境、患者資料隔離需求出現時
- **相依**：認證機制（JWT / OAuth / API Key）的選型；RBAC 設計

### 6.5 HIPAA 合規與患者隱私（合規）
- **缺什麼**：無患者資料脫敏、無存取記錄、無加密傳輸強制
- **什麼時候會痛**：實際上線承載真實患者資料、或進入合規審查時
- **相依**：與 6.3（Audit）、6.4（Auth）同步推進

### 6.6 多 Modality 支援（業務擴充）
- **缺什麼**：驗證層白名單僅允許 `US`，CT / MR / CR / DR 等其他模式被擋
- **什麼時候會痛**：業務需求擴展到非超音波影像時
- **相依**：白名單擴充（簡單）+ 各 Modality 是否需差異化驗證規則（待釐清）

### 6.7 API Rate Limiting（穩定性）
- **缺什麼**：無速率限制，惡意 / 失控 client 可拖垮服務
- **什麼時候會痛**：系統對外曝露、QPS 增長時
- **相依**：限制策略（per-IP / per-user）+ 後端（in-memory / Redis）選型

### 6.8 CORS 設定（前端整合）
> ✅ **已完成（2026-05-12）**。`main.py` 啟用 `CORSMiddleware`，dev 環境 allow `http://localhost:5173`（Vite default）。Production CORS 屬部署期決策、不在 MVP 範圍（PLAN §8.6）。本條保留以供歷史追溯。

### 6.9 環境區分（部署）
- **缺什麼**：dev / staging / production 設定無區分，hardcoded defaults
- **什麼時候會痛**：實際部署到多環境時
- **相依**：config.py 擴充 + .env profile 機制

### 6.10 Production Error Response（可用性）
- **缺什麼**：error response 在 production 可能洩漏內部細節（stack trace / SQL）
- **什麼時候會痛**：production 上線、安全審查時
- **相依**：CLAUDE.md 第 9 節已要求「Exception 訊息不可包含完整 SQL query 或 stack trace」，需落實

### 6.13 init_db (Base.metadata.create_all) 與 Alembic race condition（2026-05-19 task #10 收尾發現）
- **缺什麼**：`main.py:51-58 startup_event` 仍跑 `init_db()`（呼叫 `Base.metadata.create_all`），會在 backend dev server 重啟時搶先建出 model 對應的表、不更新 `alembic_version`、之後 `alembic upgrade head` 遇 `DuplicateTable` 失敗
- **觸發情境**：開發者修改 `models.py` 加新 class 後重啟 backend → 新表透過 init_db 自動建出來 → 接著想跑 alembic migration 套用對應的 CREATE TABLE → 失敗
- **本次 workaround**（2026-05-19）：DROP 該 empty 表 → 重跑 alembic upgrade head → alembic_version 正確升級
- **根本解**：拿掉 `main.py:startup_event` 的 `init_db()` 呼叫、讓 alembic 獨享 schema canonical 路徑；同時確認 `tests/conftest.py:35` `Base.metadata.create_all` 改寫成跑 alembic 程式化 upgrade（或保留 in-memory SQLite 走 create_all、僅 production 走 alembic — 視需求）
- **什麼時候會痛**：每次新增 model class（Phase 3 task #11 接 ai_service 若需要新表、未來任何 schema 變動）；production 部署時若有人「先 init_db 後 alembic」會 corrupt 流程
- **相依**：CLAUDE.md §5 禁止「改變 db.py session management 機制（除非明確被要求修復 bug）」邊緣 — 本項屬 bug fix 性質、需工程師裁示動 init_db 行為

### 6.14 Conflict resolution UI / replace endpoint（2026-05-19 §6.12 收尾留下）
- **缺什麼**：當 `/upload` 偵測到 SOP UID 命中但 bytes 不同（hash mismatch）時，目前回 409；但若用戶 / 管理者真的需要顯式覆蓋舊版（修補錯誤上傳、確認新版是正確版本），目前沒有 endpoint 可以做
- **MVP 階段不做的原因**：CLAUDE.md §13 「不靜默覆蓋」+ MVP 沒 auth (§6.4)、任何人能呼叫 replace endpoint 危險；replace 邏輯本身需要配套 audit log（誰、何時、原 hash、新 hash、舊 file archive 位置）
- **正確順序**：等 §6.4 認證 / 授權建立 admin 概念後再實作 replace endpoint
- **替代方案**：用戶遇到 409 → ① 接受現狀（舊版正確） ② DICOM 端重分配 SOPInstanceUID 後重傳（DICOM 標準做法、推薦） ③ 緊急情況工程師手動 SQL 操作（有人工 audit）

### 6.12 ~~Upload pipeline 缺 graceful duplicate detection~~（2026-05-18 §5.4 audit 連帶發現）
> ✅ **已解決於 2026-05-19**（commit pending）。`/upload` 加 SOPInstanceUID-based dedupe + SHA256 content hash 比對；三分支：① 同 SOP+同 bytes → 200 + `duplicate=true` + 既有 instance_id (idempotent) ② 同 SOP+不同 bytes → 409 + existing_instance_id/existing_hash/new_hash/suggested_actions ③ 新 SOP → 新建（既有行為）+ `duplicate=false`。Storage / DB 在 conflict 情境完全不動（無 orphan、無 sequence gap）。Conflict resolution UI 留 §6.14 等 auth 完成後實作。本條保留以供歷史追溯。

### 6.11 DicomViewer 影像未填滿 container（Stage C UX 缺口、2026-05-16）
> ✅ **已解決於 commit `40d766d` (Fix-J、task #9 commit 7、2026-05-18 工程師裁示)**。task #9 期間方向 J（CSS 層偵錯）由前端 Agent + codex 排查找到根因並修復：① outer div `aspectRatio` 設定衝突（commit 0 `fb656c6` 固化移除） ② Vite scaffold `#root max-width: 1126px` 改 `width:100% height:100%` ③ `html/body/#root` 100% chain + `.viewer/.viewport` wrapper 結構。user 驗收回報「ok 在中央區顯示」。Fix-1~Fix-4 詳細失敗歷史保留於 `frontend/PROGRESS.md` §4.4 供未來 Cornerstone 整合除錯參考。本條保留以供歷史追溯。

---

## 7. 目錄結構

```
MedPACS Intelligence Platform/
├── main.py                          # FastAPI 應用主入口（API layer）
├── config.py                        # Pydantic Settings 環境配置
├── db.py                            # SQLAlchemy 引擎與 session 管理
├── db_service.py                    # 資料庫 CRUD 服務（service layer）
├── models.py                        # SQLAlchemy ORM 模型（model layer）
├── storage.py                       # 檔案儲存服務介面
├── storage_backend.py               # 儲存後端實作（Local / S3 預留）
│
├── alembic.ini                      # Alembic 設定（credentials 由 env.py 注入）
├── alembic/                         # DB migration 目錄
│   ├── env.py                       # 載入 config.settings.DATABASE_URL
│   ├── script.py.mako               # Migration 模板
│   └── versions/                    # Migration scripts
│       ├── 20809e26d134_baseline_*.py        # Baseline: 四表 CREATE
│       ├── e25c80289a9c_add_series_*.py      # 2026-05-15: Series UNIQUE+NOT NULL + Instance FK
│       └── 91725486ef55_add_ai_results_*.py  # 2026-05-19: AIResult 表 (Phase 3 task #10)
│
├── validation/                      # DICOM 驗證模組
│   ├── __init__.py
│   ├── dicom_validator.py          # 驗證規則實作（必填欄位 + Modality 白名單）
│   ├── exceptions.py               # ValidationError 例外類別
│   ├── main_patch.py               # 驗證層整合修補檔
│   └── VALIDATION.md               # 驗證層設計說明
│
├── tests/                           # 測試套件（Backend）
│   ├── conftest.py                  # 共用 fixtures、工廠函式、TestClient
│   ├── test_dicom_service.py        # 整合測試（8 個）
│   ├── test_query_api.py            # API 端點測試（29 個）
│   ├── test_ai_result_model.py      # AIResult ORM 測試（3 個、Phase 3 task #10）
│   └── test_validators.py           # 驗證單元測試（9 個）
│
├── storage/                         # 本地 DICOM 檔案儲存（runtime 自動建立）
│   └── {patient_id}/{study_uid}/{filename}.dcm
│
├── frontend/                        # Frontend (React + Vite + TypeScript)
│   ├── CLAUDE.md                    # 前端 Agent 操作規範
│   ├── README.md                    # 前端啟動指南（按需查閱）
│   ├── PROGRESS.md                  # 前端工作進度（5 區塊）
│   ├── context/                     # 前端 state 檔（必讀小檔，對稱主 context/）
│   │   ├── HANDOFF.md               # 後端狀態鏡像（主 Agent 維護）
│   │   ├── DISPATCH.md              # 當前任務交付（主 Agent 覆寫式）
│   │   └── SESSION_HISTORY.md       # 前端 Agent 工作記憶（A/B 兩段）
│   ├── docs/                        # 前端詳細文件（按需查閱，對稱主 docs/）
│   │   ├── IMPLEMENTATION.md        # 前端架構詳述
│   │   └── archive/                 # 前端歸檔家（PROGRESS 超量切過來）
│   │       └── README.md
│   ├── package.json / package-lock.json
│   ├── vite.config.ts
│   ├── tsconfig.*.json
│   ├── eslint.config.js
│   ├── index.html
│   ├── public/
│   ├── src/
│   │   ├── main.tsx                 # 程式入口（含 initCornerstone）
│   │   ├── App.tsx
│   │   ├── App.css / index.css
│   │   ├── cornerstone/             # Cornerstone 整合（Stage B 已建）
│   │   │   └── setup.ts
│   │   ├── components/              # UI 元件（規劃中）
│   │   ├── context/                 # React Context（規劃中，src 子目錄；不要與 frontend/context/ 混淆）
│   │   ├── api/                     # Backend API client（規劃中）
│   │   └── assets/
│   └── node_modules/                # npm 套件（git ignored）
│
├── context/                         # 主 Agent context（小、必讀）
│   └── SESSION_HISTORY.md           # 主 Agent 工作記憶（A/B 兩段）
│
├── docs/                            # 詳細文件（按需查閱、非啟動必讀）
│   ├── PLAN.md                      # MVP 開發規劃
│   ├── IMPLEMENTATION.md            # 系統架構（backend 內部 + frontend 摘要）
│   ├── generated/                   # 🤖 自動生成（禁人工編輯）
│   │   ├── api_spec.md              # FastAPI routes（from main.py）
│   │   └── db_schema.md             # DB schema（from models.py + alembic）
│   └── archive/                     # 歸檔文件（低頻使用）
│       ├── QUICKSTART.md            # 5 分鐘雙端啟動
│       ├── STORAGE_BACKEND.md       # 儲存後端設計
│       └── COMMIT_GUIDE.md          # Commit 流程（已由系統 prompt 接手）
│
├── scripts/                         # 工具腳本
│   ├── gen_api_spec.py              # 產生 docs/generated/api_spec.md
│   ├── gen_db_schema.py             # 產生 docs/generated/db_schema.md
│   ├── backfill_series_uid.py       # 一次性 backfill — 補 pre-2026-05-15 orphan instances（2026-05-18）
│   └── hooks/
│       └── pre-commit               # git hook（偵測 source 變動 → 自動 regen）
│
├── pytest.ini                       # pytest 配置
├── requirements.txt                 # Python 依賴清單
├── .env.example                     # 環境變數範本
├── .env                             # 實際環境配置（git ignored）
│
├── README.md                        # 項目概覽與雙端啟動指引
├── CLAUDE.md                        # AI 操作規範
├── PROGRESS.md                      # 本檔（專案現況）
│
├── .git/                            # Git 版控
├── .venv/                           # Python 虛擬環境（git ignored）
├── .claude/                         # Claude Code 本地設置（git ignored）
│   └── settings.local.json
└── learning/                        # 個人學習筆記（git ignored）
```

---

## 8. 文件維護

| 項目 | 說明 |
|---|---|
| 文件版本 | v1.0 |
| 建立日期 | 2026-05-08 |
| 適用對象 | 工程師、AI coding agents、Project stakeholders |
| 更新觸發條件 | 完成功能、變更狀態、調整下一步、發現新缺口 |
| 更新方式 | 直接編輯本檔，commit message 標註 `docs(progress): ...` |
| 與 PLAN.md 關係 | PLAN.md 排程具體任務 → 本檔「下一步」引用之 → 完成後升格為「已完成」 |

> ⚠️ **本檔可由 AI agent 在工程師指示下更新**（與 CLAUDE.md 不同，CLAUDE.md 不可由 AI 自行修改）。
