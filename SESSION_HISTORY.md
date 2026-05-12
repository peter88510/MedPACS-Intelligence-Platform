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
- **AI 操作規範**：CLAUDE.md **v1.1**（2026-05-12）— 加入 §10「任務完成前的最後檢查」與 §8「README.md 評估補充規範」

### 進行中的任務

- 無 in-flight 程式碼修改
- origin/master 已含 commit 1–5（含 `ada5828 docs(claude): v1.1`）；本次 SESSION_HISTORY 更新（commit 6）為唯一待 push
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
- **M9 — CLAUDE.md v1.1 + 文件同步反思**（2026-05-12）：因 CORS commit 漏更新 README / PROGRESS §6.8 / PLAN §8.6 觸發反思。R1（PROGRESS §5 ↔ §6 互斥檢查）寫入 §10「任務完成前的最後檢查」；R2（README 評估必寫進 §8 風險區塊）寫入 §8。版本號升至 v1.1

### 待決定事項

| # | 議題 | 預設方向 / 選項 | 卡在哪 |
|---|---|---|---|
| 1 | AI 分割模型來源 | PLAN §9.4：① pretrained ultrasound checkpoint ② 最小 U-Net + 隨機 weight ③ Otsu mock | 工程師是否已有手邊的 ultrasound checkpoint 可用？沒有的話走 ③ |
| 2 | Sample DICOM 來源 | PLAN §14：① pydicom-data ② TCIA ③ 自製 synthetic | Phase 4 demo 之前要決定 |
| 3 | README env var 稽核 | 是否需要在 §15.2 新規範生效後做一次補登 | 待工程師確認是否有遺漏的 env var |

### 上次 session 結尾狀態

- **日期**：2026-05-12（Phase 1 收尾全部完成 + CLAUDE.md 升至 v1.1）
- **本次 session 完成（Phase 1 收尾 + 反思）**：
  1. **CORS middleware**：`main.py` 加入 `CORSMiddleware`，allow `http://localhost:5173`、`allow_credentials=False`、methods/headers 全開
  2. **驗證層補齊**：
     - `validation/dicom_validator.py`：`REQUIRED_FIELDS` 加入 `SeriesInstanceUID` / `SOPInstanceUID`；新增 `_check_pixel_data()` 用 `hasattr` 檢查 PixelData tag
     - `tests/conftest.py:make_mock_ds()`：加入 `series_uid` / `sop_uid` / `pixel_data` 預設值；`pixel_data=None` 透過 `del ds.PixelData` 模擬缺欄位（MagicMock 行為）
     - `tests/test_validators.py`：新增 3 個 reject 測試（series / sop / pixel）
     - `tests/test_dicom_service.py`：修正既有 2 個 integration fixture，補上 Series/SOP UID + 最小 image metadata
  3. 文件同步：`validation/VALIDATION.md`、`PLAN.md §7.1`、`PROGRESS.md`、`SESSION_HISTORY.md`
  4. **CORS 文件補強**（commit 4）：PROGRESS §6.8 矛盾修正、PLAN §8.6 加 ✅、README 新增 CORS (Dev) 章節
  5. **CLAUDE.md 升至 v1.1**（commit 5 / `ada5828`）：§10 新增「任務完成前的最後檢查」、§8 補 README 評估規範
  6. pytest：36 / 36 通過
- **Commit 序列**（origin/master 已含 1–5；6 為本次 SESSION_HISTORY 更新）：
  1. `feat(api): 加入 CORSMiddleware 允許 Vite dev origin`
  2. `feat(validation): 補齊 SeriesInstanceUID / SOPInstanceUID / PixelData 必填檢查`
  3. `docs: 同步 VALIDATION / PLAN / PROGRESS / SESSION_HISTORY 反映 Phase 1 收尾`
  4. `docs(cors): 補齊 CORS middleware 三處遺漏文件`
  5. `docs(claude): v1.1 加入文件同步檢查規範`
  6. `docs(history): 同步 Phase 1 收尾 + CLAUDE v1.1 狀態`  ← 本次, unpushed
- **下個 session 起手建議**：
  1. `git push` 把 commit 6 送上 origin
  2. （視優先序）重建 venv 為 Python 3.12
  3. 進入 **Phase 2**：React + Vite + TypeScript 初始化 + CornerstoneJS 整合（PLAN §10）
