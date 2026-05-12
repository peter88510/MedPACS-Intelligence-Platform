# PLAN.md — MVP 開發規劃

> **文件定位**：本檔記錄 **長期規劃** — Scope / Architecture / API / Validation / Roadmap / Non-goals。
>
> **責任邊界（避免與其他文件重複）**：
> - 「已完成什麼 / 進度狀態」 → [PROGRESS.md](./PROGRESS.md)
> - 「AI 行為規範 / Coding 約束」 → [CLAUDE.md](./CLAUDE.md)
> - 「快速啟動 / API 操作範例」 → [QUICKSTART.md](./QUICKSTART.md)
> - 「系統架構詳細實作」 → [IMPLEMENTATION.md](./IMPLEMENTATION.md)
>
> **更新觸發條件**：MVP scope 變動 / 新模組規劃 / API 設計變更 / Non-goal 重新評估。
> **更新方式**：PR + 工程師 review。AI agent 可協助草擬，不可自行 commit。

---

## 目錄

1. [專案目標](#1-專案目標)
2. [MVP Scope](#2-mvp-scope)
3. [Non-Goals（明確不做）](#3-non-goals明確不做)
4. [系統架構](#4-系統架構)
5. [Tech Stack](#5-tech-stack)
6. [Ingestion Architecture](#6-ingestion-architecture)
7. [Validation Strategy](#7-validation-strategy)
8. [API Design](#8-api-design)
9. [AI Inference Contract](#9-ai-inference-contract)
10. [Frontend 規劃](#10-frontend-規劃)
11. [Storage Layout](#11-storage-layout)
12. [Development Roadmap](#12-development-roadmap)
13. [Demo Workflow（驗收標準）](#13-demo-workflow驗收標準)
14. [Sample Data 準備](#14-sample-data-準備)
15. [Future Expansion](#15-future-expansion)
16. [文件維護](#16-文件維護)

---

## 1. 專案目標

打造一個 **AI-ready Ultrasound DICOM 平台原型**。
目標 **不是** 取代商業 PACS，而是建立可擴充的最小骨架，支援：

1. DICOM 上傳、儲存、metadata 解析
2. DICOM Web Viewer 顯示
3. AI 分割推論（Ultrasound）
4. 分割結果疊加渲染

未來可往 DICOMweb / C-STORE / multi-model AI / VLM 擴展，但 **MVP 不實作**（見 §3、§15）。

---

## 2. MVP Scope

### 2.1 In-scope（兩週內必完成）

**Backend**
- DICOM 上傳 API（POST `/upload`）
- DICOM metadata 解析、本地檔案儲存、PostgreSQL 持久化
- 必填欄位 + UID + Modality 驗證
- Ultrasound modality 白名單（`US`）
- 查詢 API：`/studies`、`/series/{id}`、`/instances/{id}`、`/instances/{id}/file`、`/instances/{id}/metadata`
- AI 分割 API：`POST /ai/segment/{id}`、`GET /ai/result/{id}`、`GET /ai/result/{id}/mask`
- AI 結果儲存（DB record + 本地 PNG mask）

**Frontend**
- React + CornerstoneJS DICOM viewer
- Metadata panel
- "Run AI" 觸發按鈕
- 分割結果疊加顯示

**Cross-cutting**
- Dev 環境 CORS 設定
- Sample anonymized DICOM 測試資料準備
- End-to-end 手動 demo 流程（§13）

### 2.2 進度狀態

進度追蹤統一於 [PROGRESS.md](./PROGRESS.md)。本檔不重複列舉「已完成 / 進行中」。

---

## 3. Non-Goals（明確不做）

> 以下項目即使技術上可行，**也不在 MVP 範圍**。任何要求新增請走 PR + 規劃 review。

| 類別 | 不做的項目 | 原因 |
|---|---|---|
| Security | 認證 / 授權 / RBAC | 屬於 production 課題，MVP 假設 trusted env |
| Compliance | HIPAA / 患者資料脫敏 / Audit trail | 同上，非原型驗證重點 |
| DICOM 標準 | DICOMweb（STOW/WADO/QIDO）、C-STORE | 需專屬 networking layer |
| Async | Celery / RQ / Redis 任務佇列 | MVP AI 同步推論即可（§9） |
| Infrastructure | MinIO / S3 / Docker / CI/CD | 已預留 StorageBackend 抽象，無需現在實作 |
| AI Platform | Multi-model registry / model versioning UI / A/B | 只有單一模型 |
| Annotation | 標註工具 / VLM / 多模態 workflow | 超出 MVP 範圍 |
| Workflow | M-mode / Doppler / B-mode 跨上傳依賴規則 | 需狀態機，違反兩週時程（§7.4） |
| Production Hardening | Rate limiting / production-safe error response | 部署期再談 |

---

## 4. 系統架構

```
┌──────────────────────────────────────────┐
│  Frontend (React + CornerstoneJS)        │
│  ─ Viewer / Metadata Panel / AI Trigger  │
└──────────────┬───────────────────────────┘
               │ HTTP/JSON + DICOM/PNG binary
               ▼
┌──────────────────────────────────────────┐
│  FastAPI Backend                         │
│  ┌──────────────────────────────────┐    │
│  │ API Layer (main.py)              │    │
│  ├──────────────────────────────────┤    │
│  │ Service Layer                    │    │
│  │  ─ db_service.py                 │    │
│  │  ─ storage.py / storage_backend  │    │
│  │  ─ ai_service.py  (新增)         │    │
│  ├──────────────────────────────────┤    │
│  │ Validation Layer (validation/)   │    │
│  ├──────────────────────────────────┤    │
│  │ Model Layer (models.py)          │    │
│  ├──────────────────────────────────┤    │
│  │ DB Layer (db.py)                 │    │
│  └──────────────────────────────────┘    │
└──────────┬─────────────────┬─────────────┘
           ▼                 ▼
   ┌─────────────┐   ┌──────────────────┐
   │ PostgreSQL  │   │  Local Storage   │
   │  patients   │   │  /storage/       │
   │  studies    │   │   {patient}/     │
   │  series     │   │     {study}/     │
   │  instances  │   │       *.dcm      │
   │  ai_results │   │       ai/*.png   │
   └─────────────┘   └──────────────────┘
```

**分層規範以 [CLAUDE.md §6](./CLAUDE.md) 為準，不可破壞跨層責任**。

---

## 5. Tech Stack

### Backend
- Python 3.11+
- FastAPI、pydicom、SQLAlchemy 2.0、Pydantic v2 Settings
- PostgreSQL（test 用 in-memory SQLite）
- Alembic（DB schema migration — CLAUDE.md §12 強制要求）
- PyTorch（AI 推論）
- Pillow（mask PNG 編碼）

### Frontend
- React + TypeScript
- Vite
- CornerstoneJS：`@cornerstonejs/core` + `@cornerstonejs/dicom-image-loader` + `@cornerstonejs/tools`（v3.x）
- 無強制 UI framework，可選 Tailwind 或純 CSS

### Future-only（MVP 不導入，見 §15）
MinIO / S3、Celery / Redis、pynetdicom、Docker、CI/CD。

---

## 6. Ingestion Architecture

目前 ingestion 流程整合於 `main.py` + `storage.py` + `db_service.py` + `validation/`。

未來模組化方向（**MVP 不重構**）：

```
ingestion/
 ├─ dicom_parser.py     # 統一 pydicom 解析入口
 ├─ validator.py        # = validation/dicom_validator.py
 └─ storage.py          # = storage.py
```

**MVP 決策**：暫不抽象成 `ingestion/`。CLAUDE.md §3 最小修改原則 + §6 架構保護 — 在「第二個輸入路徑」（DICOMweb 或 C-STORE）真實出現前不做這層抽象。

---

## 7. Validation Strategy

### 7.1 必填欄位

上傳 DICOM 必須包含以下 tag，缺一即拒絕（HTTP 400）：

| Tag | 用途 |
|---|---|
| `PatientID` | Patient upsert key |
| `StudyInstanceUID` | Study upsert key |
| `SeriesInstanceUID` | Series 識別 |
| `SOPInstanceUID` | Instance 唯一性 |
| `Modality` | Modality whitelist 檢查 |
| `PixelData` | 確認影像可顯示 |

> ✅ 全部 6 個必填欄位已實作（2026-05-12）。PatientID / StudyInstanceUID / SeriesInstanceUID / SOPInstanceUID / Modality 走 `REQUIRED_FIELDS`，PixelData 走 `_check_pixel_data()`（hasattr 檢查）。

### 7.2 UID 驗證

- UID 格式：符合 DICOM UID 規範（max 64 chars、dot-separated digits）
- Duplicate prevention：DB unique constraint 已就位
- 違反 uniqueness → HTTP 409，**不可靜默覆蓋**（CLAUDE.md §13）

### 7.3 Modality 驗證

MVP 僅允許 `US`。其他 modality 回傳 HTTP 400 並標示 `unsupported_modality`。

### 7.4 Ultrasound Workflow Rules（MVP 簡化決策）

> **延後到 MVP 後**。原規劃中 "M-mode requires B-mode / Doppler cannot exist independently" 等跨檔案 workflow 規則需要：
> 1. 跨上傳的 series 組合持久化
> 2. 完整性 invalidation 規則（部分上傳 / 重傳如何處理？）
> 3. 狀態機設計
>
> 這超出兩週 MVP 時程，且違反 CLAUDE.md §3 最小修改原則。
>
> **MVP 內僅做**：每筆上傳獨立驗證 modality 與必填欄位。Series-level 完整性 → 未來擴充。

### 7.5 安全性驗證

- File magic bytes 檢查（DICM preamble）
- File size 上限（建議 200MB，可配置）
- Filename sanitization（防 path traversal） — 已由 storage layer 處理

---

## 8. API Design

### 8.1 系統
| 方法 | 路徑 | 用途 |
|---|---|---|
| GET | `/health` | Liveness / version |

### 8.2 Upload
| 方法 | 路徑 | Body | Response |
|---|---|---|---|
| POST | `/upload` | multipart `file` | `{filename, patient_id, study_instance_uid, modality, message}` |

### 8.3 Query
| 方法 | 路徑 | Response |
|---|---|---|
| GET | `/studies` | `{studies: [...]}` |
| GET | `/series/{id}` | series record |
| GET | `/instances/{id}` | instance record |

### 8.4 Viewer-facing
| 方法 | 路徑 | Response |
|---|---|---|
| GET | `/instances/{id}/file` | binary DICOM（`application/dicom`） |
| GET | `/instances/{id}/metadata` | flat metadata dict |

### 8.5 AI
| 方法 | 路徑 | Response |
|---|---|---|
| POST | `/ai/segment/{id}` | `{instance_id, ai_result_id, status}` |
| GET | `/ai/result/{id}` | `{instance_id, status, mask_url, confidence, model_name}` |
| GET | `/ai/result/{id}/mask` | binary PNG |

> Mask 採 **PNG 二進位** + 獨立 endpoint：避免 base64 膨脹 JSON，前端可直接 `<img>` 載入或當 texture overlay。

### 8.6 CORS

✅ **已實作（2026-05-12）** — `main.py` 啟用 `CORSMiddleware`：
- 允許 origin：`http://localhost:5173`（Vite default）
- `allow_credentials=False`（目前無 cookie auth 需求）
- `allow_methods=["*"]`、`allow_headers=["*"]`
- Production CORS 屬部署期決策，不在 MVP 範圍。

---

## 9. AI Inference Contract

### 9.1 設計原則

| 原則 | 決策 |
|---|---|
| 同步 vs 非同步 | **同步**。`POST /ai/segment/{id}` 直接執行推論並回傳結果 ID。MVP 不引入 Celery。 |
| 模型管理 | **單模型**。MVP 沒有 model registry。 |
| 失敗處理 | HTTP 5xx + 寫入 `ai_results.status='failed'` + `error_message`。不重試、不 fallback。 |

### 9.2 Mask Wire Format

- 格式：**PNG，single-channel grayscale**（0 = background, 255 = foreground）
- 尺寸：與原 DICOM frame 同 width × height
- 儲存路徑：`storage/{patient_id}/{study_uid}/ai/{instance_id}_{model_name}_mask.png`

### 9.3 DB Schema 新增

```python
class AIResult(Base):
    __tablename__ = "ai_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    instance_id: Mapped[int] = mapped_column(ForeignKey("instances.id"), index=True)
    model_name: Mapped[str] = mapped_column(String(64))
    model_version: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16))   # queued / running / completed / failed
    mask_path: Mapped[Optional[str]] = mapped_column(String(512))
    confidence: Mapped[Optional[float]]
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
```

> **Schema 變更走 Alembic migration**（CLAUDE.md §12）。
> 流程：`alembic revision --autogenerate -m "add ai_results table"` → 人工檢查產出的 script → commit → `alembic upgrade head`。
> baseline migration（涵蓋現有 `patients` / `studies` / `series` / `instances` 四表）需在 Phase 1 收尾時建立。

### 9.4 模型選擇

**MVP 路徑（依優先順序）**：
1. **首選**：既有 ultrasound segmentation pretrained checkpoint（如 nnU-Net 範例 / TorchIO model zoo）
2. **次選**：最小 U-Net + 隨機 weight 作為 placeholder（仍呼叫 PyTorch pipeline）
3. **降級**：Otsu thresholding 產生視覺合理的 mask，明確標註 `model_name="mock_threshold"`

**MVP 不做**：模型訓練、benchmark、metrics 評估。

---

## 10. Frontend 規劃

### 10.1 專案結構（建議）

```
frontend/
├── src/
│   ├── api/                    # FastAPI client（fetch wrapper）
│   ├── components/
│   │   ├── DicomViewer.tsx     # CornerstoneJS canvas
│   │   ├── MetadataPanel.tsx   # /instances/{id}/metadata
│   │   ├── StudyList.tsx       # /studies
│   │   └── AIPanel.tsx         # Run AI + mask overlay
│   ├── hooks/
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── vite.config.ts
```

### 10.2 CornerstoneJS 整合要點

- 套件：`@cornerstonejs/core`、`@cornerstonejs/dicom-image-loader`、`@cornerstonejs/tools`（v3.x）
- 載入 scheme：`wadouri:` 指向 `/instances/{id}/file`
- Mask overlay：取 `/ai/result/{id}/mask` PNG → 半透明 image layer 疊加

### 10.3 UX 範圍

- 上傳 → 跳到該 study viewer
- Viewer 旁顯示 metadata
- "Run AI" 按鈕 → loading state → 顯示 mask overlay
- 失敗 → 簡單 error toast（不做 retry UI）

---

## 11. Storage Layout

```
storage/
└── {patient_id}/
    └── {study_uid}/
        ├── {sop_instance_uid}.dcm                    # 原始 DICOM
        └── ai/
            └── {instance_id}_{model_name}_mask.png   # AI mask
```

> DICOM 部分為 **CLAUDE.md §13 保護對象，不可變更**。
> `ai/` 子目錄為新增，不影響既有結構。

---

## 12. Development Roadmap

> **進度追蹤** → [PROGRESS.md](./PROGRESS.md)。本區塊只描述「應做什麼」與「成功標準」。

### Phase 1：Backend 基礎（Day 1–7）

| # | 任務 | 成功標準 |
|---|---|---|
| 1 | FastAPI + `/upload` + pydicom 解析 | 上傳回傳 metadata |
| 2 | PostgreSQL schema + 本地儲存 | 資料持久化 |
| 3 | 必填欄位 + UID + Modality 驗證（含 PixelData / SOPInstanceUID / SeriesInstanceUID） | 不合法檔案被拒絕 |
| 4 | 查詢 API（studies / series / instances） | 前端可取資料 |
| 5 | Viewer-facing endpoints（file / metadata） | 前端可下載 DICOM 與讀取 metadata |
| 6 | CORS middleware（dev 環境） | 前端跨域呼叫不被擋 |
| 7 | Alembic 導入 + baseline migration | `alembic upgrade head` 在乾淨 DB 重建出現有四表；後續 schema 變更全走 migration |

### Phase 2：Frontend Viewer（Day 8–10）

| # | 任務 | 成功標準 |
|---|---|---|
| 7 | React + Vite + CornerstoneJS 初始化 | 專案可啟動，hello world 渲染 |
| 8 | DICOM viewer + metadata panel | 影像正確渲染、metadata 顯示 |
| 9 | Stub AI endpoint 接通 | 「Run AI」按下後收到 stub 回應 |

### Phase 3：AI 整合（Day 11–13）

| # | 任務 | 成功標準 |
|---|---|---|
| 10 | `AIResult` model + Alembic migration | migration script commit、`alembic upgrade head` 成功、index 就位 |
| 11 | `ai_service.py` + PyTorch 模型載入（pretrained 或 mock） | 推論可產出 mask PNG |
| 12 | `/ai/segment/{id}` 同步實作 | API 回傳 mask URL |
| 13 | 前端 mask overlay 渲染 | Viewer 顯示半透明 mask |

### Phase 4：收尾（Day 14）

| # | 任務 | 成功標準 |
|---|---|---|
| 14 | End-to-end demo 流程演練（含 sample DICOM） | §13 demo 可在 5 分鐘內完成 |
| 15 | Refactor / cleanup | 限縮在 MVP scope（CLAUDE.md §3 最小修改） |

### Risk / Buffer

- **CornerstoneJS 整合風險**：v3 API 與舊版差異大 → 預留 1 天 buffer
- **PyTorch 模型整合風險**：若卡住 > 半天 → fallback 到 §9.4 第 3 路徑（mock_threshold）
- **CLAUDE.md §10**：不確定就停，列假設請工程師確認

---

## 13. Demo Workflow（驗收標準）

成功 MVP demo 應在 **5 分鐘內**完成下列流程：

1. 啟動 backend：`uvicorn main:app --reload`
2. 啟動 frontend：`npm run dev`
3. 透過 Web UI 上傳一個 anonymized ultrasound DICOM
4. Viewer 自動顯示影像 + metadata panel
5. 點 "Run AI" → 等待數秒 → 看到分割 overlay
6. 重新整理頁面 → AI 結果仍可從 `/ai/result/{id}` 取回

---

## 14. Sample Data 準備

- **來源建議**（依優先順序）：
  1. [pydicom-data](https://github.com/pydicom/pydicom-data) ultrasound 樣本
  2. TCIA 公開 ultrasound dataset（須確認 license）
  3. 自製 synthetic DICOM（pydicom 寫 test fixture generator）
- **禁止**：使用任何真實患者資料（CLAUDE.md §11）
- **儲存位置**：`test_dicom_files/`（已存在）

---

## 15. Future Expansion

> 以下項目 **明確不在 MVP 範圍**。列出僅供 roadmap 預想，**非承諾**。

### DICOM 標準
- DICOMweb（STOW-RS / WADO-RS / QIDO-RS）
- C-STORE SCP（pynetdicom）

### AI Platform
- Multi-model registry + 版本管理
- 任務佇列（Celery / RQ）
- Model A/B testing
- 結果管理 UI
- Plugin system

### Infrastructure
- MinIO / S3 物件儲存（已預留 StorageBackend 接口）
- Docker / Compose 部署
- CI/CD pipeline

### Advanced Features
- 認證 / RBAC（PROGRESS §6.4）
- HIPAA 合規 / Audit trail（PROGRESS §6.5）
- Annotation tools
- VLM / multimodal workflow
- Ultrasound workflow engine（M-mode / Doppler 跨上傳依賴）

---

## 16. 文件維護

| 項目 | 說明 |
|---|---|
| 文件版本 | v1.0 |
| 建立日期 | 2026-05-10 |
| 適用對象 | 工程師、AI coding agents、Project stakeholders |
| 更新觸發條件 | MVP scope 變動 / 新模組規劃 / API 設計變更 / Non-goal 重新評估 |
| 更新方式 | PR + 工程師 review。AI agent 可協助草擬，不可自行 commit |
| 與 PROGRESS.md 關係 | PLAN 排程 → PROGRESS 追蹤狀態。本檔不記錄完成度 |
| 與 CLAUDE.md 關係 | PLAN 不可違反 CLAUDE.md。衝突時以 CLAUDE.md 為準 |

> ⚠️ 本檔規劃方向不可由 AI agent 單方面變更。Scope / Non-goal 異動需經工程師明確指示。
