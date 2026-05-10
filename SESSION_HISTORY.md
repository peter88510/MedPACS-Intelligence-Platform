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
- **DB Migration 工具**：尚未導入（Alembic 已排程於 Phase 1 收尾）

### 進行中的任務

- 無 in-flight 程式碼修改
- 文件層 4 份未 commit 變更（見「上次 session 結尾狀態」）
- 下一個預計起手項目：**Alembic 導入 + baseline migration**（PLAN.md §12 Phase 1 task 7）

### 已完成里程碑

> 詳細清單與 API 狀態見 [PROGRESS.md](./PROGRESS.md)。本節只列關鍵里程碑。

- **M1 — DICOM 上傳完整 pipeline**：Parse → Validate → 本地儲存 → DB upsert（patient/study/series/instance）
- **M2 — 查詢 API 完整實作**：`/studies`、`/series/{id}`、`/instances/{id}`、`/instances/{id}/file`、`/instances/{id}/metadata`
- **M3 — 驗證層基礎**：必填欄位（PatientID / StudyInstanceUID / Modality）+ Modality 白名單（`US`）
- **M4 — 四層架構落地**：API → Service → Model → DB（CLAUDE.md §6）
- **M5 — 測試套件 + 隔離機制**：33 個測試、in-memory SQLite + monkeypatch
- **M6 — 文件套件就位**：README / IMPLEMENTATION / QUICKSTART / STORAGE_BACKEND / CLAUDE / PROGRESS / **PLAN**（本 session 新增）

### 待決定事項

| # | 議題 | 預設方向 / 選項 | 卡在哪 |
|---|---|---|---|
| 1 | AI 分割模型來源 | PLAN §9.4：① pretrained ultrasound checkpoint ② 最小 U-Net + 隨機 weight ③ Otsu mock | 工程師是否已有手邊的 ultrasound checkpoint 可用？沒有的話走 ③ |
| 2 | Sample DICOM 來源 | PLAN §14：① pydicom-data ② TCIA ③ 自製 synthetic | Phase 4 demo 之前要決定 |
| 3 | README env var 稽核 | 是否需要在 §15.2 新規範生效後做一次補登 | 待工程師確認是否有遺漏的 env var |
| 4 | CLAUDE.md 版本號升級 | 本 session 已修改 §10、§15.2，建議 v1.0 → v1.1 | 工程師決定要不要正式升版 |

### 上次 session 結尾狀態

- **日期**：2026-05-10
- **本 session 完成**：
  1. 建立 `PLAN.md`（含 Alembic 提前到 MVP、Frontend stack 定案 Vite + React + TS、AI inference contract、Non-goals 明列）
  2. 更新 `PROGRESS.md`：§5 接通 PLAN Phase 2/3 任務、§6.2 標「已排程」、§1 文件清單與 §7 目錄補上 PLAN.md
  3. 更新 `CLAUDE.md`：§15.2 補 infra 規範（docker-compose / volume / env / rollback / migration downgrade）、§10 補 session 歷史讀取規則
  4. 建立並 seed 本檔 `SESSION_HISTORY.md`
- **未 commit 檔案**：
  - `M  CLAUDE.md`
  - `M  PROGRESS.md`
  - `?? PLAN.md`
  - `?? SESSION_HISTORY.md`
- **下個 session 起手建議**：
  1. 先 commit 上述 4 份文件（建議拆成 2 個 commit：①「docs: 新增 PLAN.md 與 SESSION_HISTORY.md」②「docs(claude): 補 infra 規範與 session 歷史機制；docs(progress): 接通 PLAN」）
  2. 進入 Phase 1 收尾，從 **Alembic 導入 + baseline migration** 起手
