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
- **階段**：**Phase 2 進行中** — 前端骨架就位（Vite + React 19 + TS 6）、CornerstoneJS 套件已安裝（Stage A 完成）。Stage B（init 設定）已 dispatch，待前端 Agent 接手
- **Backend**：FastAPI + PostgreSQL + SQLAlchemy + pydicom，9 個 API endpoints 中 7 個完整實作、2 個（`/ai/segment/{id}`、`/ai/result/{id}`）為 stub
- **CORS**：✅ dev allow `http://localhost:5173`（Vite default）
- **驗證層**：6 個必填欄位全部就位（PatientID / StudyInstanceUID / SeriesInstanceUID / SOPInstanceUID / Modality / PixelData）+ Modality 白名單（US）
- **Frontend**：✅ scaffold 完成（React 19 + Vite 8 + TS 6 + Cornerstone3D v4.22 已裝）；元件未實作；DISPATCH.md 裝載 Stage B 任務待執行
- **AI 推論**：尚未實作（Phase 3 任務）
- **測試**：36 個測試（單元 9 / 整合 6 / API 21），用 in-memory SQLite + StaticPool 隔離。前端尚無測試套件
- **儲存**：本地檔案系統（`storage/{patient}/{study}/{filename}.dcm`），已透過 `StorageBackend` 抽象預留 S3 接口
- **DB Migration 工具**：✅ Alembic 已導入（2026-05-12），baseline migration 涵蓋四表
- **AI 操作規範**：CLAUDE.md **v1.1**（2026-05-12）— 加入 §10「任務完成前的最後檢查」與 §8「README.md 評估補充規範」；2026-05-13 加入 §15.5「前後端分工機制」
- **前後端分工**：建立完整檔案機制（2026-05-13 / 14）— `frontend/CLAUDE.md`（前端 Agent 規範）、`frontend/HANDOFF.md`（後端狀態鏡像，主 Agent 維護）、`frontend/DISPATCH.md`（當前任務交付，覆寫式）、`frontend/PROGRESS.md`（前端進度）、`frontend/SESSION_HISTORY.md`（規劃中，前端 Agent 第一版自寫）
- **文件結構**：採 Hybrid — 根目錄文件為跨專案；frontend/ 內為前端開發者深入文件
- **個人學習筆記**：`learning/` 資料夾（gitignored）— 主 Agent 解釋技術後可存檔

### 進行中的任務

- 無 in-flight 程式碼修改（主 Agent 端）
- **Stage B 已派發給前端 Agent**：`frontend/DISPATCH.md` 裝載 CornerstoneJS init 設定任務（task_id: `phase-2-task-8-stage-b`），等待前端 Agent 新 session 起手執行
- 下一個主 Agent 任務（Stage B 完成後）：依前端 Agent 回報之缺口 / 後端需求，評估是否補後端 endpoint（如 `/studies/{id}/series` 或真實 AI mask）；或直接派 Stage C dispatch（DICOM 渲染）

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
- **M10 — Phase 2 起手：前端骨架 + Cornerstone 套件**（2026-05-13）：
  - `npm create vite@latest frontend -- --template react-ts` 產出 React 19 + TS 6 + Vite 8 骨架（commit `2d055de`）
  - Cornerstone3D v4.22 + dicom-image-loader + tools + dicom-parser 安裝（commit `83b8c9a`、Vite pre-bundle 驗證通過、smoke test 撤回後乾淨）
  - 取代 Vite 預設 README 為新手向中文版本
  - 已知：6 個 moderate vulnerabilities 來自 Cornerstone transitive deps，MVP 階段接受
- **M11 — 雙端文件 Hybrid 架構重組**（2026-05-13、commit `bd42ec9`）：
  - 新增 `frontend/IMPLEMENTATION.md`（元件樹、Context、API client、Cornerstone Stage A/B/C 計畫，~470 行）
  - 根目錄 `README.md` 從「Backend-only API reference」拓寬為項目概覽
  - `IMPLEMENTATION.md` / `QUICKSTART.md` / `PLAN.md §10` / `PROGRESS.md §7` 全部同步
  - 從用戶反饋「對前端規劃模糊」具體化為元件 × API 對應表
- **M12 — 前後端分工機制建立**（2026-05-13、commits `097cef4` + `a5058b7`）：
  - 根 `CLAUDE.md` §15.5「前後端分工機制」+ TOC 入口
  - `frontend/CLAUDE.md`（前端 Agent 規範、12 章節）
  - `frontend/HANDOFF.md`（後端狀態鏡像、主 Agent 維護、放在 frontend/ 內讓前端 Agent 範圍乾淨）
  - `frontend/DISPATCH.md`（當前任務交付、覆寫式、第一版裝 Stage B）
  - `frontend/PROGRESS.md`（5 區塊：已完成/進行中/待辦/已知缺口/後端需求清單）
  - `frontend/SESSION_HISTORY.md`（規劃中，前端 Agent 第一次 dispatch 收尾自寫）
  - 任務生命週期：DISPATCH 覆寫 → 前端 Agent 萃取摘要進 PROGRESS 進行中 → 完成移到已完成（含 commit hash）

### 待決定事項

| # | 議題 | 預設方向 / 選項 | 卡在哪 |
|---|---|---|---|
| 1 | AI 分割模型來源 | PLAN §9.4：① pretrained ultrasound checkpoint ② 最小 U-Net + 隨機 weight ③ Otsu mock | 工程師是否已有手邊的 ultrasound checkpoint 可用？沒有的話走 ③ |
| 2 | Sample DICOM 來源 | PLAN §14：① pydicom-data ② TCIA ③ 自製 synthetic | Phase 4 demo 之前要決定 |
| 3 | README env var 稽核 | 是否需要在 §15.2 新規範生效後做一次補登 | 待工程師確認是否有遺漏的 env var |
| 4 | 前端 UI/UX / 瀏覽器相容 / 效能 / 無障礙規範 | 列於 `frontend/CLAUDE.md` §11 待補清單 | 等前端真正開始寫元件、需要做這些決策時才補；現在補只是空談 |
| 5 | venv Python 版本 | 目前 3.8.8（Anaconda），系統有 3.12.2；用戶將其降為低優先 | 不阻擋；等真的踩到 3.8 限制再重建 |
| 6 | 後端 endpoint 補完計畫 | `/studies/{id}/series` 與 `/series/{id}/instances` 是前端高機率會需要的；真實 AI mask 也是 | 等前端 Stage C 開始整合時 confirmed 再排程 |

### 上次 session 結尾狀態

- **日期**：2026-05-14（Phase 2 起手 + 前後端分工機制建立完成）
- **本批 session 完成（跨 2026-05-13 與 2026-05-14）**：
  1. **Phase 2 task #7**（commit `2d055de`）：Vite + React 19 + TS 6 專案骨架，dev server 啟動 ~440ms 正常回應，取代預設 README 為新手向中文版
  2. **Phase 2 task #8 Stage A**（commit `83b8c9a`）：Cornerstone3D v4.22 + dicom-image-loader + tools + dicom-parser 安裝，Vite pre-bundle 驗證通過、smoke test 撤回乾淨
  3. **雙端文件 Hybrid 重組**（commit `bd42ec9`）：新增 `frontend/IMPLEMENTATION.md`、改寫根 README / QUICKSTART / IMPLEMENTATION、PLAN §10 補元件 × API 表、PROGRESS §7 補 frontend/、順手修 3 處 stale
  4. **learning/ 個人筆記目錄**（commit `e285703`）：`.gitignore` 加 `learning/`，本機保存學習筆記
  5. **前後端分工機制 v1**（commit `097cef4`）：根 `CLAUDE.md` §15.5 + TOC、`frontend/CLAUDE.md`（12 章節）、`frontend/HANDOFF.md`（後端狀態鏡像、放進 frontend/）、`frontend/PROGRESS.md`（5 區塊）
  6. **DISPATCH + SESSION_HISTORY 機制**（commit `a5058b7`）：`frontend/DISPATCH.md`（覆寫式任務交付、第一版裝 Stage B）、`frontend/CLAUDE.md` §8/§9 新增、任務生命週期改寫
- **Commit 序列**（全部已 push）：
  ```
  a5058b7 chore: 補 DISPATCH.md（覆寫式任務交付）與 SESSION_HISTORY 機制
  097cef4 chore: 建立前後端分工機制 — HANDOFF 進 frontend/、規範任務生命週期
  bd42ec9 docs: 重構文件結構以反映 backend + frontend 雙端架構
  e285703 chore(gitignore): 排除 learning/ 個人學習筆記目錄
  83b8c9a chore(frontend): 安裝 Cornerstone3D 套件（Phase 2 task #8）
  2d055de feat(frontend): 建立 React + Vite + TypeScript 專案骨架（Phase 2 task #7）
  ```
  本次 SESSION_HISTORY 更新（commit 7）為唯一待 push
- **重大認知變更**：
  - Frontend 從「規劃模糊」到「規劃明確」（8 個元件、5 欄位 Context、7 個 API endpoint、3 階段整合）
  - 引入「主 Agent / 前端 Agent」分工角色觀；主 Agent 不動 frontend/ 內程式碼，僅維護 HANDOFF + DISPATCH
  - dispatch 從 ephemeral prompt 改為檔案化（DISPATCH.md 覆寫式）
- **下個 session 起手建議**：
  1. `git push` 本次 SESSION_HISTORY 更新
  2. **開新 session 給前端 Agent 執行 Stage B**：起手語只需「依 `frontend/CLAUDE.md` §1 必讀清單啟動，然後依 `frontend/DISPATCH.md` 開始當前任務」
  3. 前端 Agent 完成 Stage B 後：
     - 讀 `frontend/PROGRESS.md` 看完成記錄與新發現的後端需求
     - 若有後端需求 → 主 Agent 處理、更新 `frontend/HANDOFF.md`
     - 派 Stage C dispatch（DICOM 實際渲染）— 整檔覆寫 `frontend/DISPATCH.md`
