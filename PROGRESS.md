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
- [x] 自動 DB 初始化（`init_db()`，已被 Alembic 取代為 canonical 路徑） — **2026-05-19 §6.13 根治**：startup_event 不再自動呼叫 `init_db()`、避免 race condition；`init_db` function 保留供 emergency reset 手動 call
- [x] 驗證層模組化（`validation/`）
- [x] **Alembic 導入 + baseline migration**（涵蓋 patients / studies / series / instances 四表，upgrade/downgrade 雙向已驗證）
- [x] **AIResult model + Alembic migration `91725486ef55`**（Phase 3 task #10、2026-05-19）— PLAN §9.3 schema scaffolding；不接 PyTorch（工程師親自串接演算法/模型）；upgrade/downgrade round-trip 驗證通過

### 測試與品質
- [x] 84 個測試案例（單元 / 整合 / API / ORM 多層）
- [x] 共用 fixtures（`tests/conftest.py`）
- [x] pytest 配置（`pytest.ini`）
- [x] 測試隔離機制（記憶體 SQLite + monkeypatch）

### AI 整合（Phase 3 prep）
- [x] **AI source vendored 於 `./AI/`**（2026-06-06、snapshot @ `6139799`、from github.com/peter88510/diaphragm_excursion）— diaphragm M-mode excursion 量測 pipeline（DICOM → motion curve → peak/trough → cm）；Python 3.8、PaddleSeg + numpy + scipy + pywt 等；4 層架構 (Input/Algorithm/Visualization/Profiling)；含 ARCHITECTURE/CLAUDE/PROGRESS/README + algorithm/config/input/visualization/tools/experiments/font/docs；paddleseglibs/(27MB) + model weights gitignore；`requirements-ai.txt` 13 deps；root README 加 §Step 7 setup 章節
- [x] **AIResult schema 對齊 + Measurement Type resolver 架構**（2026-06-09、設計見 `.work/ai_result_design.md`）— `ai_results` +4 欄 (`measurement_type` server_default='excursion' / `result_json` JSONB(SQLite variant JSON) / `primary_value` / `primary_unit`)、`instances` +2 欄 (`device_manufacturer` / `device_model`)；Alembic migration `7f3c9a2b1d04`（全 additive、upgrade/downgrade 雙向）；`services/measurement_type.py`（MeasurementType enum + Resolver Protocol + MachineModelResolver[mapping 可注入] + 空 MACHINE_MODEL_MAP + ImageContentResolver stub）；upload flow 抽 Manufacturer(0008,0070)/ModelName(0008,1090) 存 Instance
- [x] **AI engine 整合層 + `/ai/segment`·`/ai/result` 真實實作**（2026-06-10、Phase 3 #2/#3）— 可替換式 `services/ai_engine/`（抽象 `DiaphragmEngine` ABC + 平台中立 `EngineResult`/`Measurement` + paddle 的 `DiaphragmExcursionEngine` wrapper + `get_engine()` factory 唯一替換點 + serialize → design §4 envelope）。`#14` 採同 process import（lazy import `AI.main.run`、缺 paddle → 503、66-test 不受影響）；LEGACY mode、viz 關閉。`/ai/segment/{id}` 真實流程：resolver 解析（C62→excursion / L154→thickness）→ unknown 422 / thickness 501 / excursion·sniff 跑引擎 → 寫 ai_results；`/ai/result/{id}` 回最新結果（未跑→404）。`MACHINE_MODEL_MAP` 填 C62/L154（key 改 model-only，工程師 2026-06-10 裁示）。82 tests 全綠（含 fake-engine 注入、不碰 paddle）。**真實推論端到端待工程師裝 paddle + weights 驗證**；mask PNG endpoint + 前端 overlay 屬下游

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
| POST | `/upload` | 上傳並處理 DICOM 檔案 | ✅ 完整 | response 含 `instance_id`（2026-05-14 加）+ `duplicate` 欄位（2026-05-19 加，dedup 結果指示）；409 表 SOP UID 衝突；2026-06-09 起額外抽 Manufacturer/ModelName 存 Instance（response 不變） |
| GET | `/health` | 健康檢查 | ✅ 完整 | — |
| GET | `/studies` | 列出所有研究 | ✅ 完整 | — |
| GET | `/studies/{id}/series` | 列出該研究的所有系列 | ✅ 完整 | 2026-05-15 加；舊 study 可能回 `[]` |
| GET | `/series/{id}` | 取得指定系列 | ✅ 完整 | — |
| GET | `/series/{id}/instances` | 列出該系列的所有實例 | ✅ 完整 | 2026-05-15 加；2026-05-15 前的 instances `series_instance_uid` 為 NULL、不會列出 |
| GET | `/instances/{id}` | 取得指定實例 | ✅ 完整 | — |
| GET | `/instances/{id}/file` | 下載原始 DICOM 檔案 | ✅ 完整 | 透過 FileResponse |
| GET | `/instances/{id}/metadata` | 取得實例 metadata | ✅ 完整 | — |
| POST | `/ai/segment/{id}` | 觸發 AI 量測 | ✅ 完整 | 2026-06-10 真實實作（取代 stub）；resolver→422(unknown)/501(thickness)/200(excursion·sniff)；engine 缺 paddle→503、推論失敗→500（留 error 結果）；回 `{instance_id, ai_result_id, status, measurement_type, primary_value, primary_unit, measurement_count}`。**端到端真實推論待 paddle+weights 驗證** |
| GET | `/ai/result/{id}` | 取得 AI 量測結果 | ✅ 完整 | 2026-06-10 真實實作（取代 stub）；回最新一筆 ai_results（含 `measurement_type`/`result`(envelope)/`primary_value`/`primary_unit`/`mask_url`=null）；尚未跑過→404 |

**完整度**：11/11 完整實作（AI 兩端為整合層完整、端到端真實推論待 paddle 環境驗證）。

---

## 3. 測試覆蓋簡況

### 總覽
- **總測試數**：84 個
- **執行方式**：`pytest tests/ -v`
- **隔離機制**：記憶體 SQLite + monkeypatch 臨時 storage，每個測試獨立

### 三層分布

| 層級 | 檔案 | 測試數 | 風格 |
|---|---|---|---|
| 整合測試 | `tests/test_dicom_service.py` | 13 | 真實 SQLite 記憶體 DB + 臨時 storage（含 2026-05-15 series upsert / upload-creates-series 兩項 + 2026-05-19 duplicate detection 三項 + 2026-06-09 device tag 抽取兩項：有 tag / 無 tag null） |
| API 測試 | `tests/test_query_api.py` | 31 | TestClient + mock `db_service`（含 /studies/{id}/series 與 /series/{id}/instances 各 4；2026-06-10 AI 兩端真實實作：segment 422/501/200/503/404、result 命中/未跑 404/instance 404，引擎走 DI fake 不碰 paddle） |
| ORM 測試 | `tests/test_ai_result_model.py` | 6 | 純 SQLAlchemy model 層（task #10：CRUD + nullable + relationship；2026-06-09：measurement_type default + result_json round-trip + 新欄 nullable） |
| 單元測試 | `tests/test_validators.py` | 9 | 純邏輯，無 DB / HTTP |
| 單元測試 | `tests/test_measurement_type.py` | 13 | MeasurementType resolver（model-only key、known/unknown/missing、whitespace 正規化、manufacturer 缺值仍命中、production map C62→excursion/L154→thickness、enum str、ImageContentResolver stub） |
| 單元測試 | `tests/test_ai_engine.py` | 12 | AI engine 抽象層（serialize envelope / primary value-unit / engine guard 不載 paddle / get_engine singleton；2026-06-12 加 warmup base no-op / 子類 override 兩項） |

### 已覆蓋路徑
- ✅ DICOM 上傳完整流程（解析 / 儲存 / DB 寫入）
- ✅ Patient / Study upsert 行為
- ✅ Instance 建立行為
- ✅ 所有查詢端點（成功、404、空集合）
- ✅ AI 端點真實流程（resolver 分支 422/501、引擎成功寫入、503 不可用；fake engine 注入）
- ✅ AI engine 抽象層（envelope 序列化、guard、factory）
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
- [x] **AI source vendoring (task #11 prep、2026-06-06)** — peter88510/diaphragm_excursion @ `6139799` (2026-06-05) snapshot vendored 進 `./AI/`；paddleseglibs/ + model weights gitignore；`requirements-ai.txt` (13 deps) 拆出；README 加 setup 章節
- [x] **Schema 對齊 + Measurement Type resolver 架構**（2026-06-09、設計 `.work/ai_result_design.md`）— 裁示方案：統一 header + JSON payload（`ai_results` +`measurement_type`/`result_json`(JSONB)/`primary_value`/`primary_unit`；新增量測類型零 migration）。`instances` +`device_manufacturer`/`device_model`（上傳時抽、懶解析）。`services/measurement_type.py` plugin 架構（MVP MachineModelResolver、未來可換 ImageContentResolver）。Alembic `7f3c9a2b1d04` additive。66 tests 全綠。**endpoint 仍 stub**
- [x] **AI engine wrapper（`services/ai_engine/`）+ `/ai/segment`·`/ai/result` 真實實作**（2026-06-10）— 可替換式 `DiaphragmEngine` ABC + paddle `DiaphragmExcursionEngine`（#14 同 process import、lazy、缺 paddle→503）+ serialize → design §4 envelope + `get_engine()` factory；resolver 接通（C62→excursion / L154→thickness、unknown 422 / thickness 501）；ai_results 寫入 + 查詢。82 tests 全綠（fake-engine 注入）。commit `e934025`/`22101af`/`f7f16de`
- [x] **端到端真實推論驗證 + run_config 共用調參**（2026-06-11）— 工程師裝 paddle+weights，`POST /ai/segment/12` 跑完 150-frame model → **200 OK + ai_results 寫入**。途中修：① requirements-ai 缺 paddleseg 相依(pyyaml/visualdl/filelock/requests) + cp950 encoding ② 邊界 numpy→native 正規化(result_json JSON-serializable) ③ engine `_build_bundle` 接 `run_config.build_bundle()`（Option A：tuning 100% 上游 run_config、API 強制 LEGACY/viz-off）。整合 Option A 已驗證
- [x] **AI 整合介面瘦身（facade re-vendor、Option 1）**（2026-06-11）— Phase 0 契約✅(`docs/ai_inference_contract.md`、commit `772faed`) / Phase 1 上游 `inference.py` facade✅ / Phase 2 re-vendor✅(@`5340456`、8 檔、commit `8f15e18`) / Phase 3 engine 簡化✅(~250→~150 行、commit `bca26ab`)。engine 改呼叫 `inference.analyze`：去 importlib hack + `_build_bundle` reach-in + numpy 正規化；接 warm segmenter(lazy 載一次重用)。**剩 Phase 2b trim**(viz/tools/experiments/font + 砍 visualdl，延後、需 GPU env 實測) + ~~startup warmup~~(✅ 2026-06-12 完成、見下)
- [x] **GPU 環境收斂**（2026-06-11）— `.venv`(3.8/CPU paddle) per-frame 慢 → 改用 clone 自 CLI `diaphragmalgo_env` 的 `medpacs_gpu`(Python 3.10.18 + paddlepaddle-gpu 3.2.0/cu118 + 後端 web 依賴)；GPU 提速已驗證。日常啟動：`conda activate medpacs_gpu` → `uvicorn main:app --reload`
- [x] **AI engine startup warmup（opt-in `AI_WARMUP_ON_STARTUP`）**（2026-06-12、commit `418f29d` + review fixes）— FastAPI startup 預載 paddle segmenter 消第一個 `/ai/segment` 冷啟；`DiaphragmEngine` ABC 加預設 no-op `warmup()`、子類 override 走既有 lazy 路徑。env-gated（預設 false、測試/純後端啟動零延遲）+ exception-safe（缺 paddle 降級不擋啟動）。Settings 收編 `AI_WARMUP_ON_STARTUP: bool`（修寫入 `.env` 時 pydantic extra_forbidden 崩潰）。+2 test、84 全綠。設計筆記 `learning/asgi-lifespan-and-engine-locks.md`（gitignored）
- [ ] `/ai/result/{id}/mask` — mask PNG endpoint（engine 預留 `mask_path`；與 facade `save_mask_dir` 合一設計，見契約 §4.3）
- [ ] **Realtime 串流 demo endpoint**（候選）— REALTIME mode 逐 frame 推 excursion + video artifact；正解活在 run-loop state（run() 不回傳）→ 需另設 streaming endpoint，工程師 territory
- [ ] 前端 mask overlay / 量測結果渲染 — ⏸ 數值層可先接（後端已就緒）、mask overlay 等 mask endpoint

### Phase 4：收尾（PLAN §12、§13）
- [ ] Sample anonymized DICOM 測試資料準備
- [ ] End-to-end demo workflow 演練（5 分鐘內完成 PLAN §13 流程）

---

## 6. 已知缺口（中長期、未排程）

> 以下為「知道缺、但尚未排入近期計畫」的項目。納入 PLAN.md 後即升格為「下一步」。

### 6.1 AI 量測功能（業務）
> ✅ **整合層完成 + 端到端已驗證（2026-06-11）**：`/ai/segment`·`/ai/result` 真實實作、ai_results 寫入/查詢、可替換式 engine（design §4 envelope）；工程師 dev 裝 paddle+weights、`POST /ai/segment` 跑出真實 excursion → 200 OK。**剩餘缺口**：① AI 整合介面瘦身（facade re-vendor、見 §5 + `docs/ai_inference_contract.md`） ② thickness 演算法本體未存在（L154 目前 501 forward-design） ③ mask PNG endpoint + 前端 overlay 渲染 ④ realtime 串流 demo endpoint（候選）。任務佇列（Celery / RQ）MVP 階段不需（同步 LEGACY 已足）。本條保留追蹤剩餘缺口。

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

### 6.13 ~~init_db (Base.metadata.create_all) 與 Alembic race condition~~（2026-05-19 task #10 收尾發現）
> ✅ **已解決於 2026-05-19**（commit pending、方案 A）。`main.py:startup_event` 移除 `init_db()` 呼叫、改 print「Schema managed by Alembic」訊息；alembic 獨享 schema canonical 路徑。`db.init_db` function 保留供 emergency reset 手動 call。README.md `Integration Notes` 同步更新行為描述。dev workflow 變動：新 clone / fresh DB 必須先跑 `alembic upgrade head` 才能啟 backend（既有 README Step 4 已要求此順序、本次只是真正落實）。`conftest.py:35` `Base.metadata.create_all` 不動（test 走獨立 in-memory SQLite engine、與 production DB 分離、52 test 全綠）。本條保留以供歷史追溯。

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
├── main.py                          # FastAPI 應用主入口（API layer、entrypoint）
├── core/                            # 設定層
│   ├── __init__.py
│   └── config.py                    # Pydantic Settings 環境配置
├── db/                              # DB 層（session / engine）
│   ├── __init__.py                  # re-export（from db import get_db... 照舊）
│   └── session.py                   # SQLAlchemy 引擎與 session 管理
├── models/                          # Model 層（SQLAlchemy ORM）
│   ├── __init__.py                  # re-export（from models import ... 照舊）
│   └── orm.py                       # ORM 模型定義
├── services/                        # Service 層（business logic、不 import FastAPI）
│   ├── __init__.py
│   ├── db_service.py                # 資料庫 CRUD 服務
│   ├── storage.py                   # 檔案儲存服務介面
│   ├── storage_backend.py           # 儲存後端實作（Local / S3 預留）
│   ├── measurement_type.py          # MeasurementType enum + Resolver plugin（2026-06-09；key model-only 2026-06-10）
│   └── ai_engine/                   # AI 推論引擎抽象層（可替換式、2026-06-10）
│       ├── __init__.py              # get_engine() factory（唯一替換點）+ re-export
│       ├── base.py                  # DiaphragmEngine ABC + EngineResult/Measurement + Errors
│       ├── diaphragm_excursion_engine.py  # paddle wrapper（lazy import AI.main.run）
│       └── serialize.py             # EngineResult → result_json envelope（design §4）
│
├── alembic.ini                      # Alembic 設定（credentials 由 env.py 注入）
├── alembic/                         # DB migration 目錄
│   ├── env.py                       # 載入 core.config.settings.DATABASE_URL
│   ├── script.py.mako               # Migration 模板
│   └── versions/                    # Migration scripts
│       ├── 20809e26d134_baseline_*.py        # Baseline: 四表 CREATE
│       ├── e25c80289a9c_add_series_*.py      # 2026-05-15: Series UNIQUE+NOT NULL + Instance FK
│       ├── 91725486ef55_add_ai_results_*.py  # 2026-05-19: AIResult 表 (Phase 3 task #10)
│       └── 7f3c9a2b1d04_add_measurement_*.py # 2026-06-09: instances +2 device 欄 / ai_results +4 量測欄
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
│   ├── test_ai_result_model.py      # AIResult ORM 測試（6 個、task #10 + 2026-06-09 量測欄）
│   ├── test_measurement_type.py     # MeasurementType resolver 單元測試（13 個、2026-06-10 model-only key）
│   ├── test_ai_engine.py            # AI engine 抽象層測試（10 個、2026-06-10、不載 paddle）
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
│   ├── ai_inference_contract.md     # AI inference facade 契約（上游 inference.py 施工圖，2026-06-11）
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
├── AI/                              # Phase 3 AI inference (vendored 2026-06-06、snapshot @ 6139799)
│   ├── ARCHITECTURE.md / CLAUDE.md / PROGRESS.md / README.md   # AI sub-repo 自有文件
│   ├── main.py                     # Orchestration (per-frame loop)
│   ├── algorithm/                  # diaphragm_detection / excursion / motion_curve / multiframe / roi_band / segmentation / signal_processing
│   ├── config/                     # dataclass cfg per-layer
│   ├── input/                      # DCM/PNG reader + FrameSequence
│   ├── visualization/              # debug + final overlay + REALTIME video
│   ├── tools/                      # timing_report.py
│   ├── experiments/                # 驗證 script
│   ├── docs/                       # AI sub-repo docs (INDEX/api_reference/pipeline/modules/notes/STYLE)
│   ├── font/                       # Altinn-DIN Bold.otf (viz 字型)
│   ├── run_config.example.py       # per-machine cfg template
│   └── paddleseglibs/              # [gitignored, 27MB] vendored PaddleSeg; clone from AI repo
│
├── requirements-ai.txt              # AI inference deps (paddlepaddle / pydicom / numpy / scipy / pywt 等 13 個)
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
