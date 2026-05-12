# SESSION_HISTORY.md — 工作記憶 (Working Memory)

> **文件定位**：本檔為 AI agent 的 **session 級工作記憶**。
> 每次 session 開始時 AI 必須先讀本檔（CLAUDE.md §10）。
>
> **與其他文件的差異**：
> - 不是長期規劃 → 見 [PLAN.md](./PLAN.md)
> - 不是進度追蹤 → 見 [PROGRESS.md](./PROGRESS.md)
> - 不是行為規範 → 見 [CLAUDE.md](./CLAUDE.md)
>
> **更新規則（CLAUDE.md §10）**：
> - 工程師說「更新歷史」時，或每次 session 結束前工程師觸發
> - 只更新有變動的區塊，不重寫整檔
> - 不記錄對話流水帳，只記錄狀態與結論

---

## 工作記憶

### 系統現況

- **定位**：AI-ready Ultrasound DICOM 平台 MVP（非完整 PACS 替代）
- **階段**：**Phase 1 全部完成**（PLAN.md §12），準備進入 Phase 2 Frontend Viewer
- **Backend**：FastAPI + PostgreSQL + SQLAlchemy + pydicom，9 個 API endpoints 中 7 個完整實作、2 個（`/ai/segment/{id}`、`/ai/result/{id}`）為 stub
- **CORS**：✅ dev allow `http://localhost:5173`（Vite default）
- **驗證層**：6 個必填欄位全部就位（PatientID / StudyInstanceUID / SeriesInstanceUID / SOPInstanceUID / Modality / PixelData）+ Modality 白名單（US）
- **Frontend**：尚未開始（Phase 2 任務）
- **AI 推論**：尚未實作（Phase 3 任務）
- **測試**：36 個測試（單元 9 / 整合 6 / API 21），用 in-memory SQLite + StaticPool 隔離
- **儲存**：本地檔案系統（`storage/{patient}/{study}/{filename}.dcm`），已透過 `StorageBackend` 抽象預留 S3 接口
- **DB Migration 工具**：✅ Alembic 已導入（2026-05-12），baseline migration 涵蓋四表

### 進行中的任務

- 無 in-flight 程式碼修改
- 本 session 變更尚未 commit（見「上次 session 結尾狀態」）
- 下一個預計起手項目：Phase 2 起手 — React + Vite + TypeScript 專案初始化 + CornerstoneJS 整合（PLAN §10）

### 已完成里程碑

> 詳細清單與 API 狀態見 [PROGRESS.md](./PROGRESS.md)。本節只列關鍵里程碑。

- **M1 — DICOM 上傳完整 pipeline**：Parse → Validate → 本地儲存 → DB upsert（patient/study/series/instance）
- **M2 — 查詢 API 完整實作**：`/studies`、`/series/{id}`、`/instances/{id}`、`/instances/{id}/file`、`/instances/{id}/metadata`
- **M3 — 驗證層基礎**：必填欄位（PatientID / StudyInstanceUID / Modality）+ Modality 白名單（`US`）
- **M4 — 四層架構落地**：API → Service → Model → DB（CLAUDE.md §6）
- **M5 — 測試套件 + 隔離機制**：33 個測試、in-memory SQLite + monkeypatch
- **M6 — 文件套件就位**：README / IMPLEMENTATION / QUICKSTART / STORAGE_BACKEND / CLAUDE / PROGRESS / PLAN
- **M7 — Alembic 導入 + baseline migration**（2026-05-12）：alembic.ini + env.py 接通 `config.settings`、baseline migration 涵蓋 patients/studies/series/instances 四表、upgrade/downgrade 雙向驗證通過、33 個測試無 regression
- **M8 — Phase 1 收尾完成**（2026-05-12）：CORS middleware（dev allow `http://localhost:5173`）+ 驗證層補齊（SeriesInstanceUID / SOPInstanceUID / PixelData 必填）+ test fixture 同步補齊。36 / 36 測試通過

### 待決定事項

| # | 議題 | 預設方向 / 選項 | 卡在哪 |
|---|---|---|---|
| 1 | AI 分割模型來源 | PLAN §9.4：① pretrained ultrasound checkpoint ② 最小 U-Net + 隨機 weight ③ Otsu mock | 工程師是否已有手邊的 ultrasound checkpoint 可用？沒有的話走 ③ |
| 2 | Sample DICOM 來源 | PLAN §14：① pydicom-data ② TCIA ③ 自製 synthetic | Phase 4 demo 之前要決定 |
| 3 | README env var 稽核 | 是否需要在 §15.2 新規範生效後做一次補登 | 待工程師確認是否有遺漏的 env var |
| 4 | CLAUDE.md 版本號升級 | 本 session 已修改 §10、§15.2，建議 v1.0 → v1.1 | 工程師決定要不要正式升版 |

### 上次 session 結尾狀態

- **日期**：2026-05-12（Alembic 部分已 commit + push，CORS / 驗證層補齊本次 session 完成尚未 commit）
- **本次 session 完成（Phase 1 收尾）**：
  1. **CORS middleware**：`main.py` 加入 `CORSMiddleware`，allow `http://localhost:5173`、`allow_credentials=False`、methods/headers 全開
  2. **驗證層補齊**：
     - `validation/dicom_validator.py`：`REQUIRED_FIELDS` 加入 `SeriesInstanceUID` / `SOPInstanceUID`；新增 `_check_pixel_data()` 用 `hasattr` 檢查 PixelData tag
     - `tests/conftest.py:make_mock_ds()`：加入 `series_uid` / `sop_uid` / `pixel_data` 預設值；`pixel_data=None` 透過 `del ds.PixelData` 模擬缺欄位（MagicMock 行為）
     - `tests/test_validators.py`：新增 3 個 reject 測試（series / sop / pixel）
     - `tests/test_dicom_service.py`：修正既有 2 個 integration fixture（`test_upload_with_valid_dicom` / `test_upload_stores_file_locally`），補上 SeriesInstanceUID / SOPInstanceUID + 最小 image metadata（Rows/Columns/BitsAllocated/... + PixelData）
  3. 文件同步：`validation/VALIDATION.md`（active rules 表 + 移除已實作的範例段落）、`PLAN.md §7.1`（標記已實作）、`PROGRESS.md`（§1 必填欄位 / §3 測試數 33→36 / §5 Phase 1 全部勾選）
  4. pytest：**36 / 36 通過**（原 33 + 新增 3）
- **未 commit 檔案**（git status 待你執行確認）：
  - `M  main.py`、`M  PLAN.md`、`M  PROGRESS.md`、`M  SESSION_HISTORY.md`
  - `M  validation/dicom_validator.py`、`M  validation/VALIDATION.md`
  - `M  tests/conftest.py`、`M  tests/test_dicom_service.py`、`M  tests/test_validators.py`
- **下個 session 起手建議**：
  1. 先 commit 本 session 變更（建議拆 3 個 commit：①「feat(api): add CORS middleware for Vite dev origin」②「feat(validation): require SeriesInstanceUID / SOPInstanceUID / PixelData」③「docs: sync VALIDATION/PLAN/PROGRESS/SESSION_HISTORY for Phase 1 closeout」）
  2. （視優先序）重建 venv 為 Python 3.12
  3. 進入 **Phase 2**：React + Vite + TypeScript 初始化 + CornerstoneJS 整合（PLAN §10）
