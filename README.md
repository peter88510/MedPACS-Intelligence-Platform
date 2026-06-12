---
docspec: "2.0"
type: PROJECT_OVERVIEW
title: "MedPACS Intelligence Platform v2.0"
version: "2.2.0"
status: "update"
---

# MedPACS Intelligence Platform

針對超音波 DICOM 工作流的雙層式系統：

- **後端（Backend）** — FastAPI + PostgreSQL + SQLAlchemy + pydicom。負責 DICOM 上傳、解析、驗證、持久化，以及 AI 測量端點（橫膈膜偏移 diaphragm excursion、paddle；真正的推論需要 AI runtime——見 Step 7）。
- **前端（Frontend）** — React 19 + Vite + TypeScript + CornerstoneJS。單頁式 DICOM 檢視器，含 metadata 面板與 AI overlay。

> MVP 範圍與 roadmap 見 [`docs/PLAN.md`](./docs/PLAN.md)，目前進度見 [`PROGRESS.md`](./PROGRESS.md)。

## 功能（Features）

### 後端
- DICOM 檔案上傳與解析
- 6 欄位 DICOM 驗證（PatientID / StudyInstanceUID / SeriesInstanceUID / SOPInstanceUID / Modality / PixelData）
- Modality 白名單（僅限 `US`）
- 本地檔案儲存（依 `PatientID` → `StudyInstanceUID` 階層化）
- PostgreSQL 持久化，搭配 Alembic migrations
- AI 測量端點（`/ai/segment`、`/ai/result`）——可抽換的 engine layer，包裝 vendored 的 `./AI` 橫膈膜 pipeline；端到端推論需要 AI runtime（Step 7）
- CORS middleware，對應 `http://localhost:5173` 開發來源

### 前端（Phase 2，進行中）
- React + Vite + TypeScript 骨架（Cornerstone3D 相依套件已安裝）
- 規劃中：4 個元件（StudyList / DicomViewer / MetadataPanel / AIPanel）
- 規劃中：CornerstoneJS DICOM 渲染，含 AI mask overlay

## 專案結構（Project Structure）

> 2026-05-14 重組（Phase 1 + 2 文件重組）：root 層深度文件移入 `docs/`；跨 session 工作記憶移入 `context/`；前端鏡像相同的 `context/` + `docs/` 結構。權威的完整目錄樹見 [`PROGRESS.md`](./PROGRESS.md) §7。

```text
MedPACS Intelligence Platform/
├── main.py                          # API layer 入口（uvicorn main:app）
├── core/                            # config（settings）
├── db/                              # session / engine
├── models/                          # SQLAlchemy ORM
├── services/                        # db_service / storage / storage_backend / measurement_type
├── requirements.txt / pytest.ini / alembic.ini
├── alembic/                          # DB migration scripts（env.py + versions/）
├── storage/                          # 實體 DICOM 儲存（runtime 自動建立）
├── validation/                       # DICOM 驗證規則
├── tests/                            # 後端 pytest 測試套件（36 個測試）
├── test_dicom_files/                 # 範例 DICOM fixtures
│
├── frontend/                         # Phase 2 前端（React + Vite + TS + Cornerstone3D）
│   ├── CLAUDE.md / README.md / PROGRESS.md
│   ├── context/                      # 小型必讀狀態檔
│   │   ├── HANDOFF.md                # 後端狀態鏡像（主 Agent 維護）
│   │   ├── DISPATCH.md               # 當前任務（每次派任務時覆寫）
│   │   └── SESSION_HISTORY.md        # 前端 Agent 工作記憶
│   ├── docs/                         # 詳細文件（按需查閱）
│   │   ├── IMPLEMENTATION.md         # 前端架構
│   │   └── archive/                  # 前端側 archive
│   ├── package.json / vite.config.ts / tsconfig.*.json
│   └── src/                          # main.tsx / App.tsx / cornerstone/setup.ts / components/
│
├── context/                          # 主 Agent 小型必讀狀態
│   └── SESSION_HISTORY.md            # AI session 工作記憶（A/B 段）
│
├── docs/                             # 詳細文件（按需查閱）
│   ├── PLAN.md                       # MVP 範圍 + roadmap + non-goals
│   ├── IMPLEMENTATION.md             # 系統架構（後端內部 + 前端概覽）
│   ├── generated/                    # 🤖 自動生成（請勿手動編輯）
│   │   ├── api_spec.md               # FastAPI 路由（由 main.py 生成）
│   │   └── db_schema.md              # DB schema（由 models/ + alembic 生成）
│   └── archive/                      # 低流量封存文件
│       ├── QUICKSTART.md             # 5 分鐘 API 導覽
│       ├── STORAGE_BACKEND.md        # Storage backend 設計
│       └── COMMIT_GUIDE.md           # Commit 流程（已被 system prompt 取代）
│
├── scripts/                          # 工具
│   ├── gen_api_spec.py               # → docs/generated/api_spec.md
│   ├── gen_db_schema.py              # → docs/generated/db_schema.md
│   └── hooks/pre-commit              # git hook：source 變動 → 自動 regen
│
├── .env.example                      # 環境變數範本（DATABASE_URL / UPLOAD_STORAGE_PATH）
├── .env                              # 實際環境設定（git ignored）
├── README.md                         # 本檔（專案概覽）
├── PROGRESS.md                       # 目前專案狀態
├── CLAUDE.md                         # AI 操作合約
└── .venv/                            # Python virtualenv（git ignored）
```

## 安裝設定（Setup）

### Step 1：安裝相依套件

_Linux/macOS：_

```bash
pip install -r requirements.txt
```

_Windows：_

```powershell
pip install -r requirements.txt
```

### Step 2：設定環境

_Linux/macOS：_

```bash
cp .env.example .env

# 編輯 .env
nano .env
# 或
vim .env
```

_Windows（PowerShell）：_

```powershell
# 若 .env.example 不存在則建立
@"
# PostgreSQL Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/meddicom_db

# Server Configuration
UPLOAD_STORAGE_PATH=./storage
"@ | Set-Content -Path ".env.example" -Encoding UTF8

# 複製為 .env
Copy-Item .env.example .env

# 用實際憑證編輯 .env
notepad .env
```

_Windows（CMD）：_

```cmd
REM 建立 .env.example
echo # PostgreSQL Configuration > .env.example
echo DATABASE_URL=postgresql://postgres:password@localhost:5432/meddicom_db >> .env.example
echo # Server Configuration >> .env.example
echo UPLOAD_STORAGE_PATH=./storage >> .env.example

REM 複製為 .env
copy .env.example .env

REM 編輯 .env
notepad .env
```

#### 設定憑證

編輯 `.env`，填入你實際的 PostgreSQL 密碼：

```text
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/meddicom_db
UPLOAD_STORAGE_PATH=./storage
```

### Step 3：建立 PostgreSQL 資料庫

_Linux/macOS：_

```bash
createdb -U postgres -h localhost meddicom_db
```

_Windows：_

```cmd
createdb -U postgres -h 127.0.0.1 meddicom_db
```

#### 確認資料庫已建立

_Linux/macOS：_

```bash
psql -U postgres -h 127.0.0.1 -c "\l"
```

_Windows：_

```powershell
psql -U postgres -h 127.0.0.1 -c "\l"
```

預期輸出：清單中應出現 `meddicom_db`。

#### 替代方案：透過 psql 建立資料庫

在任何平台連線到 PostgreSQL：

_Linux/macOS：_

```bash
psql -U postgres -h 127.0.0.1
```

_Windows：_

```powershell
psql -U postgres -h 127.0.0.1
```

接著執行：

```sql
CREATE DATABASE meddicom_db;
```

### Step 4：初始化 Schema（Alembic）

資料庫建立完成後（Step 3），套用 migrations 以建構 schema。

**全新資料庫（尚無任何資料表）：**

```powershell
alembic upgrade head
```

**已存在且已含 schema 的資料庫（例如 pre-Alembic 時期）：**

將 DB 標記為已在 head——**不會**執行 CREATE TABLE：

```powershell
alembic stamp head
```

> ⚠️ 當要遷移的是早於 Alembic、且已含那四張資料表的 DB 時，請選 `stamp head`（而非 `upgrade head`）。對已有資料的 DB 跑 `upgrade head` 會因「relation already exists」而失敗。

驗證 migration 狀態：

```powershell
alembic current
```

### Step 5：執行應用程式

_Linux/macOS：_

```bash
uvicorn main:app --reload
```

_Windows：_

```powershell
uvicorn main:app --reload
```

伺服器執行於 `http://localhost:8000`。

### Step 6：啟動前端（選用，Phase 2）

若你只需要後端 API，可略過此步。在**新的終端機**（保持後端執行中）：

```powershell
cd frontend
npm install        # 首次，或拉到新相依套件後
npm run dev
```

開啟於 `http://localhost:5173`。後端的 CORS middleware 已允許此來源。

> 前端開發者指南：[`frontend/README.md`](./frontend/README.md)
> 前端架構：[`frontend/docs/IMPLEMENTATION.md`](./frontend/docs/IMPLEMENTATION.md)

### Step 7：選用——AI 推論設定（Phase 3 準備）

AI 橫膈膜偏移推論 pipeline 以 vendored 形式置於 [`AI/`](./AI/)（僅含原始碼；
重量級相依與 model weights 已從 git 排除）。除非你打算執行真正的 AI 推論
（Phase 3 後端整合；見 PROGRESS §5 Phase 3），否則可略過本節。

**1. 拉取重量級產物**（被本 repo 的 `.gitignore` 排除）：

```powershell
# paddleseglibs/ — vendored PaddleSeg，含 Patch 2A-2C 修改（約 27 MB）
git clone --depth 1 https://github.com/peter88510/diaphragm_excursion.git temp-ai
Copy-Item -Recurse temp-ai/paddleseglibs ./AI/
Remove-Item -Recurse -Force temp-ai

# Model weights（5 × 323 MB）— 從實驗室儲存取得並放置於：
#     AI/paddleseglibs/output/model/<model_name>/best_model/model.pdparams
```

**2. 安裝 AI Python 相依**（與 MedPACS 後端分開）：

```powershell
pip install -r requirements-ai.txt
```

> ⚠️ `paddlepaddle` 可能需要依你的 CUDA / CPU 環境釘選對應版本。
> 視需要編輯 `requirements-ai.txt`。

**3. Smoke test** 獨立的 AI pipeline：

```powershell
cd AI
python main.py  # 先編輯 main.py 底部的 `image_path`
```

預期：`[done] N frames, ..., excursion_runs=M` log 行，且 `excursion_cm` 值
落在 1-7 cm 範圍（典型橫膈膜範圍）。完整 Quick Start 見
[`AI/README.md`](./AI/README.md) §3。

> 後端整合已完成（2026-06-10）：`/ai/segment/{id}` 透過可抽換的
> `services/ai_engine` layer 呼叫 `AI.main.run`。一旦此 AI runtime 安裝完成，
> `/ai/segment` 即執行真正推論；否則回傳 503。見 PROGRESS §5 Phase 3。

## 前端概覽（Frontend Overview）

前端是位於 `frontend/` 下的單頁應用程式（SPA）：

- **技術棧**：React 19 + TypeScript 6 + Vite 8 + CornerstoneJS 4.22（Cornerstone3D 家族）
- **狀態管理**：React Context（5 個欄位）——無 Redux/Zustand
- **元件**：4 個業務元件（`StudyList` / `DicomViewer` / `MetadataPanel` / `AIPanel`）+ 4 個結構性元件 = 共 8 個
- **樣式**：CSS Modules，無 UI framework
- **後端耦合**：MVP 期間 hard-coded `API_BASE = 'http://localhost:8000'`（env var 之後再做）

元件設計、Context 結構、API client 結構，以及 CornerstoneJS 整合計畫見
[`frontend/docs/IMPLEMENTATION.md`](./frontend/docs/IMPLEMENTATION.md)。

## API 端點（API Endpoints）

### POST /upload

上傳並處理一個 DICOM 檔案。

**Request：**

```text
Content-Type: multipart/form-data
Body: file (binary DICOM)
```

**Response（200 OK）：**

```json
{
  "instance_id": 1,
  "filename": "patient_001.dcm",
  "patient_id": "P12345",
  "study_instance_uid": "1.2.3.4.5.6.7",
  "modality": "CT",
  "message": "DICOM file uploaded and processed successfully"
}
```

| 欄位 | 型別 | 備註 |
|---|---|---|
| `instance_id` | integer | 新建立 instance 的 DB primary key。可用它透過 `GET /instances/{id}` / `/instances/{id}/file` / `/instances/{id}/metadata` 往下查。2026-05-14 新增。 |
| `filename` | string | 由上傳回傳 |
| `patient_id` | string | DICOM `PatientID` tag 值（非 DB primary key） |
| `study_instance_uid` | string | DICOM `StudyInstanceUID` tag 值 |
| `modality` | string | DICOM `Modality` tag 值 |

### GET /health

健康檢查端點。

**Response（200 OK）：**

```json
{
  "status": "ok",
  "version": "2.0"
}
```

### GET /studies

回傳資料庫中所有 studies，依最近 ingest 排序。

**Response（200 OK）：**

```json
{
  "studies": [
    { "id": 1, "study_instance_uid": "1.2.840.10008..." }
  ]
}
```

### GET /series/{id}

依資料庫 ID 回傳單一 series 記錄。

| 參數 | 型別 | 說明 |
|---|---|---|
| `id` | integer | series 的資料庫 primary key |

**Response（200 OK）：** Series 物件。

**Response（404 Not Found）：**

```json
{ "detail": "Series with id 99 not found" }
```

### GET /studies/{id}/series

回傳指定 study 的所有 series（2026-05-15 新增）。

| 參數 | 型別 | 說明 |
|---|---|---|
| `id` | integer | study 的資料庫 primary key |

**Response（200 OK）：**

```json
{ "series": [ { "id": 10, "series_instance_uid": "1.2.3.4", "study_instance_uid": "1.2.3" } ] }
```

當 study 尚無 series 記錄時，回傳空的 `series: []` 是合法的（例如 2026-05-15 之前的舊上傳，當時上傳 pipeline 尚未寫入 series 表）。

**Response（404 Not Found）：** 當 study 本身不存在時回傳。

### GET /series/{id}/instances

回傳指定 series 的所有 instances（2026-05-15 新增）。

| 參數 | 型別 | 說明 |
|---|---|---|
| `id` | integer | series 的資料庫 primary key |

**Response（200 OK）：**

```json
{ "instances": [ { "id": 100, "sop_instance_uid": "1.2.3.4.5", "series_instance_uid": "1.2.3.4" } ] }
```

當 series 存在、但其子 instances 是在 2026-05-15 schema 升級前上傳時，回傳空的 `instances: []` 是合法的（它們的 `series_instance_uid` 欄位為 NULL，無法配對）。

**Response（404 Not Found）：** 當 series 本身不存在時回傳。

### GET /instances/{id}

依資料庫 ID 回傳單一 instance 記錄。

| 參數 | 型別 | 說明 |
|---|---|---|
| `id` | integer | instance 的資料庫 primary key |

**Response（200 OK）：** Instance 物件。

**Response（404 Not Found）：**

```json
{ "detail": "Instance with id 99 not found" }
```

### GET /instances/{id}/file

串流指定 instance 的原始 DICOM 檔案。

| 參數 | 型別 | 說明 |
|---|---|---|
| `id` | integer | instance 的資料庫 primary key |

**Response（200 OK）：** `application/dicom` 檔案串流。

**Response（404 Not Found）：** 當 instance 不存在、或磁碟上找不到該檔案時回傳。

### GET /instances/{id}/metadata

回傳指定 instance 的所有 metadata 欄位。

| 參數 | 型別 | 說明 |
|---|---|---|
| `id` | integer | instance 的資料庫 primary key |

**Response（200 OK）：**

```json
{ "id": 1, "sop_instance_uid": "1.2.840...", "series_id": 10 }
```

**Response（404 Not Found）：**

```json
{ "detail": "Instance with id 99 not found" }
```

## AI 端點（AI Endpoints）

> 自 2026-06-10 起為真正的整合層（取代先前的 stubs）。**端到端推論**需要
> AI runtime（paddle + model weights，見
> [Step 7](#step-7選用ai-推論設定phase-3-準備)）；若未安裝，
> `/ai/segment` 回傳 **503**。測量類型由 DICOM device model
> （`ManufacturerModelName`）解析：`C62` → excursion，`L154` → thickness。

### POST /ai/segment/{id}

對該 instance 執行橫膈膜測量（同步，LEGACY 模式），並寫入一筆 `ai_results`。

| 參數 | 型別 | 說明 |
|---|---|---|
| `id` | integer | instance 的資料庫 primary key |

**Response（200 OK）：**

```json
{ "instance_id": 1, "ai_result_id": 42, "status": "completed",
  "measurement_type": "excursion", "primary_value": 2.31, "primary_unit": "cm",
  "measurement_count": 1 }
```

| Status | 時機 |
|---|---|
| 422 | Device model 不在 machine-model map 中（無法解析類型——拒絕猜測） |
| 501 | Thickness 測量（前瞻設計；演算法尚未實作） |
| 503 | AI runtime 相依未安裝（安裝 `requirements-ai.txt` + Step 7） |
| 500 | 已嘗試推論但失敗（會記錄一筆 `error` row） |
| 404 | Instance 不存在 |

### GET /ai/result/{id}

回傳該 instance 最新的 AI 結果。

| 參數 | 型別 | 說明 |
|---|---|---|
| `id` | integer | instance 的資料庫 primary key |

**Response（200 OK）：**

```json
{ "instance_id": 1, "ai_result_id": 42, "status": "completed",
  "measurement_type": "excursion", "model_name": "diaphragm_excursion",
  "model_version": "6139799", "primary_value": 2.31, "primary_unit": "cm",
  "confidence": null, "mask_url": null,
  "result": { "schema_version": 1, "measurements": [ ... ], "primary": { ... } },
  "error_message": null, "created_at": "..." }
```

> `mask_url` 目前為 `null`——mask PNG 端點是下游任務。

**Response（404 Not Found）：** instance 不存在，或尚無 AI 結果（請先執行 `POST /ai/segment/{id}`）。

```json
{ "detail": "Instance with id 99 not found" }
```

## 資料庫 Schema（Database Schema）

### patients

| 欄位 | 型別 | 約束 |
|---|---|---|
| `id` | Integer | Primary key |
| `patient_id` | String | Unique；在 studies 中作為 FK 被引用 |
| `created_at` | DateTime | insert 時自動設定 |

### studies

| 欄位 | 型別 | 約束 |
|---|---|---|
| `id` | Integer | Primary key |
| `study_instance_uid` | String | Unique；在 instances 中作為 FK 被引用 |
| `patient_id` | String | FK → `patients.patient_id` |
| `modality` | String | Nullable |
| `created_at` | DateTime | insert 時自動設定 |

### series

| 欄位 | 型別 | 約束 |
|---|---|---|
| `id` | Integer | Primary key |
| `series_instance_uid` | String | **Unique, NOT NULL**（自 2026-05-15 migration `e25c80289a9c` 起） |
| `study_instance_uid` | String | FK → `studies.study_instance_uid` |
| `created_at` | DateTime | insert 時自動設定 |

### instances

| 欄位 | 型別 | 約束 |
|---|---|---|
| `id` | Integer | Primary key |
| `sop_instance_uid` | String | Nullable；unique |
| `file_path` | String | 已儲存檔案的相對路徑 |
| `study_instance_uid` | String | FK → `studies.study_instance_uid` |
| `series_instance_uid` | String | Nullable；FK → `series.series_instance_uid`（2026-05-15 新增；舊 rows 為 NULL） |
| `created_at` | DateTime | insert 時自動設定 |

## 儲存結構（Storage Structure）

檔案以階層化目錄結構儲存於本地：

```text
storage/
└── {patient_id}/
    └── {study_instance_uid}/
        └── {filename}.dcm
```

已知 metadata 的範例：

```text
storage/
└── P12345/
    └── 1.2.3.4.5.6.7/
        └── patient_001.dcm
```

缺少 PatientID 或 StudyInstanceUID 的範例：

```text
storage/
└── unknown_patient/
    └── unknown_study/
        └── file.dcm
```

## 測試（Testing）

執行核心測試套件：

_Linux/macOS：_

```bash
pytest test_dicom_service.py -v
```

_Windows：_

```powershell
pytest test_dicom_service.py -v
```

測試涵蓋：

- Health 端點
- DICOM 上傳與解析
- 本地檔案儲存
- 資料庫操作（upsert patient、upsert study、create instance）

## 資料庫 Migration（Alembic）

Schema 變更透過 Alembic 管理。**依 CLAUDE.md §12，任何 schema 變更都必須走 migration script**——直接呼叫 `Base.metadata.create_all()` 僅保留給測試使用。

### 常用指令

```powershell
# 套用所有 pending migrations
alembic upgrade head

# 回退一個 migration
alembic downgrade -1

# 回退到空 schema
alembic downgrade base

# 顯示目前 revision
alembic current

# 顯示 migration 歷史
alembic history

# 編輯 models/orm.py 後生成新的 migration
alembic revision --autogenerate -m "describe change"
```

### 撰寫新的 migration

1. 編輯 `models/orm.py`（新增 column / table）
2. 執行 `alembic revision --autogenerate -m "<short description>"`
3. **打開 `alembic/versions/` 中生成的 script 並 review**——autogenerate 並不完美（它會漏掉 CHECK constraints、ENUM 變更、server defaults 等）
4. 在 scratch DB 上驗證 `upgrade()` 與 `downgrade()` 皆可運作
5. Commit 該 script

### 註記

- `alembic.ini` **不**含憑證；`alembic/env.py` 從 `core.config.settings`（由 `.env` 載入）注入 `DATABASE_URL`。
- 測試使用 in-memory SQLite + `Base.metadata.create_all()`（見 `tests/conftest.py`）——它們為了速度與隔離而繞過 Alembic。

## CORS（開發用）

`main.py` 為開發啟用 `CORSMiddleware`，讓前端（Phase 2——React + Vite，預設 port `5173`）可從瀏覽器呼叫本 API。

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

開發時若要允許其他來源（例如 `http://localhost:3000`），將它附加到 `allow_origins`。**Production CORS 屬部署決策，刻意排除在 MVP 範圍外**（PLAN §8.6）。

## 整合註記（Integration Notes）

- **API Contract**：`/upload` response 與 v1.0 完全相同。Client 端無需變更。
- **內部變更**：檔案儲存與資料庫持久化對 API 使用者透明。
- **資料庫初始化**：Schema 由 Alembic 建構（`alembic upgrade head`——全新 DB 首次啟動 `uvicorn main:app` 前必須執行）。`db/session.py` 中的舊 `init_db()` 保留為可呼叫的緊急重置用，但**已不再於啟動時被呼叫**（自 2026-05-19 起，PROGRESS §6.13 root-cause 修正，避免 `Base.metadata.create_all` 與 alembic 競態而導致下次 `alembic upgrade head` 出現 DuplicateTable）。
- **CORS**：開發來源為 `http://localhost:5173`。要新增更多請見上方 **CORS（開發用）** 段。
- **儲存目錄**：`./storage` 目錄若不存在會自動建立。

## 疑難排解（Troubleshooting）

### Database Connection Refused

- 確認 PostgreSQL 正在執行。
- 確認 `.env` 中的 `DATABASE_URL` 正確。
- 確認資料庫存在：`createdb meddicom_db`。

### No Such Table

執行 Alembic 以建構 schema：

```powershell
alembic upgrade head
```

若 migrations 卡住或失去同步，見上方 **資料庫 Migration（Alembic）** 段。

### Permission Denied on ./storage

- 確認專案目錄具有寫入權限。
- 確認 `.env` 中的 `UPLOAD_STORAGE_PATH` 設定正確。

_Linux/macOS：_

```bash
chmod 755 .
```

## 版本歷史（Version History）

| 版本 | 狀態 | 備註 |
|---|---|---|
| v2.0 | Current | 新增 PostgreSQL 持久化與本地檔案儲存 |
| v1.0 | Superseded | 初版 DICOM 解析與上傳 |
