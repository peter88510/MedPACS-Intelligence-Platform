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
- [x] DICOM magic bytes 驗證
- [x] DICOM 必填欄位驗證（PatientID / StudyInstanceUID / SeriesInstanceUID / SOPInstanceUID / Modality / PixelData）
- [x] Modality 白名單驗證（目前僅允許 `US`）
- [x] Patient upsert（依 patient_id 唯一性）
- [x] Study upsert（依 study_instance_uid 唯一性）
- [x] Series 建立（依 series_instance_uid）
- [x] Instance 建立（依 sop_instance_uid 唯一性）
- [x] DICOM 檔案本地儲存（路徑：`{storage}/{patient_id}/{study_uid}/{filename}.dcm`）

### 查詢能力
- [x] 列出所有研究（GET /studies）
- [x] 取得指定系列（GET /series/{id}）
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
- [x] 自動 DB 初始化（`init_db()`，已被 Alembic 取代為 canonical 路徑，保留向後相容）
- [x] 驗證層模組化（`validation/`）
- [x] **Alembic 導入 + baseline migration**（涵蓋 patients / studies / series / instances 四表，upgrade/downgrade 雙向已驗證）

### 測試與品質
- [x] 33 個測試案例（單元 / 整合 / API 三層）
- [x] 共用 fixtures（`tests/conftest.py`）
- [x] pytest 配置（`pytest.ini`）
- [x] 測試隔離機制（記憶體 SQLite + monkeypatch）

### Frontend（Phase 2 進行中）
- [x] React 19 + Vite 8 + TypeScript 6 專案骨架（2026-05-13、commit `2d055de`）
- [x] Cornerstone3D v4.22 套件安裝（`@cornerstonejs/core` + `dicom-image-loader` + `tools` + `dicom-parser`）（Stage A、2026-05-13、commit `83b8c9a`）
- [x] CornerstoneJS 初始化設定（`src/cornerstone/setup.ts` idempotent `initCornerstone()` + `main.tsx` async bootstrap）（Stage B、2026-05-14、commit `8cd61f3`）

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
| POST | `/upload` | 上傳並處理 DICOM 檔案 | ✅ 完整 | — |
| GET | `/health` | 健康檢查 | ✅ 完整 | — |
| GET | `/studies` | 列出所有研究 | ✅ 完整 | — |
| GET | `/series/{id}` | 取得指定系列 | ✅ 完整 | — |
| GET | `/instances/{id}` | 取得指定實例 | ✅ 完整 | — |
| GET | `/instances/{id}/file` | 下載原始 DICOM 檔案 | ✅ 完整 | 透過 FileResponse |
| GET | `/instances/{id}/metadata` | 取得實例 metadata | ✅ 完整 | — |
| POST | `/ai/segment/{id}` | 觸發 AI 分割 | ⚠️ **Stub** | 僅回傳 `{"status": "queued"}`，無實作 |
| GET | `/ai/result/{id}` | 取得 AI 分割結果 | ⚠️ **Stub** | 僅回傳 mock 結果 |

**完整度**：7/9 完整實作，2/9 為 stub。

---

## 3. 測試覆蓋簡況

### 總覽
- **總測試數**：36 個
- **執行方式**：`pytest tests/ -v`
- **隔離機制**：記憶體 SQLite + monkeypatch 臨時 storage，每個測試獨立

### 三層分布

| 層級 | 檔案 | 測試數 | 風格 |
|---|---|---|---|
| 整合測試 | `tests/test_dicom_service.py` | 6 | 真實 SQLite 記憶體 DB + 臨時 storage |
| API 測試 | `tests/test_query_api.py` | 21 | TestClient + mock `db_service` |
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
- [ ] **Stage C：第一張 DICOM 渲染**（純 viewer、hardcoded instance ID、wadouri scheme）— **2026-05-14 dispatching 中**
- [ ] `<MetadataPanel />` / `<StudyList />` / `<AIPanel />` 元件 + API client + AppContext（Phase 2 task #9，Stage C 完成後派發）
- [ ] Stub AI endpoint 接通 + `<AIPanel />` mask overlay（依賴 Phase 3 真實 AI）

### Phase 3：AI 整合（PLAN §9、§12）
- [ ] `AIResult` model + Alembic migration
- [ ] `ai_service.py` + PyTorch 模型載入（pretrained / mock fallback 路徑見 PLAN §9.4）
- [ ] `/ai/segment/{id}` 同步實作（覆蓋現有 stub）
- [ ] `/ai/result/{id}` + `/ai/result/{id}/mask` 實作（覆蓋現有 stub）
- [ ] 前端 mask overlay 渲染

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
│       └── 20809e26d134_baseline_*.py  # Baseline: 四表 CREATE
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
│   ├── test_dicom_service.py        # 整合測試（6 個）
│   ├── test_query_api.py            # API 端點測試（21 個）
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
