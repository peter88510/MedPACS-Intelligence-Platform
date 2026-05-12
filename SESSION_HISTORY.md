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
- **階段**：Phase 1 收尾中（PLAN.md §12）
- **Backend**：FastAPI + PostgreSQL + SQLAlchemy + pydicom，9 個 API endpoints 中 7 個完整實作、2 個（`/ai/segment/{id}`、`/ai/result/{id}`）為 stub
- **Frontend**：尚未開始（Phase 2 任務）
- **AI 推論**：尚未實作（Phase 3 任務）
- **測試**：33 個測試（單元 6 / 整合 6 / API 21），用 in-memory SQLite + monkeypatch 隔離
- **儲存**：本地檔案系統（`storage/{patient}/{study}/{filename}.dcm`），已透過 `StorageBackend` 抽象預留 S3 接口
- **DB Migration 工具**：✅ Alembic 已導入（2026-05-12），baseline migration 涵蓋四表

### 進行中的任務

- 無 in-flight 程式碼修改
- 本 session 變更尚未 commit（見「上次 session 結尾狀態」）
- 下一個預計起手項目：Phase 1 剩餘兩項擇一 — ① 驗證層補齊（SeriesInstanceUID / SOPInstanceUID / PixelData）② CORS middleware（dev allow `http://localhost:5173`）

### 已完成里程碑

> 詳細清單與 API 狀態見 [PROGRESS.md](./PROGRESS.md)。本節只列關鍵里程碑。

- **M1 — DICOM 上傳完整 pipeline**：Parse → Validate → 本地儲存 → DB upsert（patient/study/series/instance）
- **M2 — 查詢 API 完整實作**：`/studies`、`/series/{id}`、`/instances/{id}`、`/instances/{id}/file`、`/instances/{id}/metadata`
- **M3 — 驗證層基礎**：必填欄位（PatientID / StudyInstanceUID / Modality）+ Modality 白名單（`US`）
- **M4 — 四層架構落地**：API → Service → Model → DB（CLAUDE.md §6）
- **M5 — 測試套件 + 隔離機制**：33 個測試、in-memory SQLite + monkeypatch
- **M6 — 文件套件就位**：README / IMPLEMENTATION / QUICKSTART / STORAGE_BACKEND / CLAUDE / PROGRESS / PLAN
- **M7 — Alembic 導入 + baseline migration**（2026-05-12）：alembic.ini + env.py 接通 `config.settings`、baseline migration 涵蓋 patients/studies/series/instances 四表、upgrade/downgrade 雙向驗證通過、33 個測試無 regression

### 待決定事項

| # | 議題 | 預設方向 / 選項 | 卡在哪 |
|---|---|---|---|
| 1 | AI 分割模型來源 | PLAN §9.4：① pretrained ultrasound checkpoint ② 最小 U-Net + 隨機 weight ③ Otsu mock | 工程師是否已有手邊的 ultrasound checkpoint 可用？沒有的話走 ③ |
| 2 | Sample DICOM 來源 | PLAN §14：① pydicom-data ② TCIA ③ 自製 synthetic | Phase 4 demo 之前要決定 |
| 3 | README env var 稽核 | 是否需要在 §15.2 新規範生效後做一次補登 | 待工程師確認是否有遺漏的 env var |
| 4 | CLAUDE.md 版本號升級 | 本 session 已修改 §10、§15.2，建議 v1.0 → v1.1 | 工程師決定要不要正式升版 |

### 上次 session 結尾狀態

- **日期**：2026-05-12
- **本 session 完成**：
  1. `requirements.txt` 加入 `alembic==1.13.1` 並安裝
  2. `alembic init alembic` 產生骨架；改寫 `alembic.ini`（清空 `sqlalchemy.url`）與 `alembic/env.py`（從 `config.settings.DATABASE_URL` 注入、`target_metadata = Base.metadata`）
  3. 對空 DB 執行 `alembic revision --autogenerate -m "baseline: patients studies series instances"`，產出 baseline migration（revision `20809e26d134`），人工檢視所有 4 表 / index / unique / FK 對應正確
  4. 雙向驗證：`alembic upgrade head` → `downgrade base` → `upgrade head`，schema 正確重建
  5. 跑 pytest：33 / 33 通過，無 regression
  6. 更新 `README.md`（新增 Step 4 Alembic / Database Migration 章節 / Troubleshooting）、`PROGRESS.md`（§1 / §5 / §6.2 / §7）、`SESSION_HISTORY.md`
  7. 修正 `tests/conftest.py`：從 `sqlite:///./test.db`（file-backed）改為 `sqlite:///:memory:` + `StaticPool`。刪除 `test.db` 檔案。33 / 33 測試通過、執行時間 10.22s → 2.36s（~4× 加速）
  8. `QUICKSTART.md` 目錄結構移除 `test.db` 條目
- **Python 版本盤點結果（2026-05-12）**：
  - 系統有 **Python 3.12.2**（`py -3.12`，工程師確認此為其編譯環境）
  - 本 repo `.venv` 是用 Anaconda 3.8.8 建立的 → 與工程師意圖不符
  - 結論：venv 需要用 3.12 重建（獨立任務，未在本 session 執行）
- **未 commit 檔案**（git status 待你執行確認）：
  - `M  requirements.txt`、`M  README.md`、`M  PROGRESS.md`、`M  QUICKSTART.md`、`M  SESSION_HISTORY.md`、`M  tests/conftest.py`
  - `D  test.db`
  - `?? alembic.ini`、`?? alembic/`
- **下個 session 起手建議**：
  1. 先 commit 本 session 變更（建議拆 3 個 commit：①「feat(db): introduce Alembic + baseline migration」②「test(conftest): switch to true in-memory SQLite via StaticPool」③「docs: sync README/PROGRESS/QUICKSTART/SESSION_HISTORY」）
  2. 重建 venv 為 Python 3.12（`py -3.12 -m venv .venv` → 重裝 `requirements.txt`）
  3. 進入 Phase 1 剩餘兩項：驗證層補齊 + CORS middleware（順序由工程師決定）
