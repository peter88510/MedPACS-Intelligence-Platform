# SESSION_HISTORY.md — 工作記憶 (Working Memory)

> **文件定位**：本檔為主 Agent 的 **session 級工作記憶**。
> 每次 session 開始時 AI 必須先讀本檔的 **A 段（系統現況快照）**；B 段為按需查閱（CLAUDE.md §10）。
>
> **與其他文件的差異**：
> - 不是長期規劃 → 見 [PLAN.md](../docs/PLAN.md)
> - 不是進度追蹤 → 見 [PROGRESS.md](../PROGRESS.md)
> - 不是行為規範 → 見 [CLAUDE.md](../CLAUDE.md)
>
> **更新規則（CLAUDE.md §10）**：
> - 工程師說「更新歷史」時，或每次 session 結束前工程師觸發
> - 只更新有變動的區塊，不重寫整檔
> - 不記錄對話流水帳，只記錄狀態與結論
>
> **結構說明（2026-05-14 起）**：
> - **A 段（系統現況快照）**：當前狀態、in-flight 任務、待決定事項 — 每次 session 必讀
> - **B 段（工作脈絡）**：里程碑歷史、上次 session 結尾狀態 — 按需查閱、需要回顧時才讀

---

## A. 系統現況快照（必讀，每次 session 啟動）

### 系統現況

- **定位**：AI-ready Ultrasound DICOM 平台 MVP（非完整 PACS 替代）
- **階段**：**Phase 2 進行中** — 前端骨架就位、Cornerstone Stage A 完成、Stage B 已 dispatch 待前端 Agent 接手。**AI 工作流優化 Phase 1-4 完成**（2026-05-14）
- **Backend**：FastAPI + PostgreSQL + SQLAlchemy + pydicom，9 個 API endpoints 中 7 個完整實作、2 個（`/ai/segment/{id}`、`/ai/result/{id}`）為 stub
- **CORS**：✅ dev allow `http://localhost:5173`（Vite default）
- **驗證層**：6 個必填欄位全部就位（PatientID / StudyInstanceUID / SeriesInstanceUID / SOPInstanceUID / Modality / PixelData）+ Modality 白名單（US）
- **Frontend**：✅ scaffold 完成（React 19 + Vite 8 + TS 6 + Cornerstone3D v4.22 已裝）；元件未實作；`frontend/context/DISPATCH.md` 裝載 Stage B 任務待執行
- **AI 推論**：尚未實作（Phase 3 任務）
- **測試**：36 個測試（單元 9 / 整合 6 / API 21），用 in-memory SQLite + StaticPool 隔離。前端尚無測試套件
- **儲存**：本地檔案系統（`storage/{patient}/{study}/{filename}.dcm`），已透過 `StorageBackend` 抽象預留 S3 接口
- **DB Migration 工具**：✅ Alembic 已導入（2026-05-12），baseline migration `20809e26d134` 涵蓋四表
- **AI 操作規範**：CLAUDE.md **v1.2**（2026-05-14、commit `688f098`）— v1.1 之上再加 R3 Doc Impact 檢測 / R4 Stale Warning / §15.6 PROGRESS 觸發式 archive；§8 風險說明表格化
- **文件結構（Hybrid）**：根目錄為跨專案文件、`docs/` 為後端深入文件（PLAN、IMPLEMENTATION）、`docs/generated/` 為 auto-gen 權威來源（api_spec.md / db_schema.md）、`docs/archive/` 為歷史備檔；frontend/ 鏡像同樣結構
- **前後端分工**：完整檔案機制 — `frontend/CLAUDE.md` v1.1（前端規範）、`frontend/context/HANDOFF.md`（後端狀態鏡像、主 Agent 維護）、`frontend/context/DISPATCH.md`（覆寫式任務交付）、`frontend/PROGRESS.md`、`frontend/context/SESSION_HISTORY.md`（前端 Agent 維護）
- **自動化機制**：`scripts/hooks/pre-commit`（git config core.hooksPath 已啟用）偵測 `main.py` / `models.py` / `alembic/versions/*.py` 變動 → 自動 regenerate `docs/generated/` 並 `git add`
- **個人學習筆記**：`learning/` 資料夾（gitignored）— 主 Agent 解釋技術後可存檔

### 進行中的任務

- 無 in-flight 程式碼修改（主 Agent 端）
- AI 工作流優化 Phase 1-4 全部完成 + 已 push（CLAUDE.md v1.2 啟用）
- **Stage B 已完成**（commit `8cd61f3`、`acd2ced`）。`frontend/context/DISPATCH.md` 仍裝載 Stage B 內容（status: active 但實際完工）、待主 Agent 派 Stage C 時覆寫
- 下一個主 Agent 任務：(a) 評估 PROGRESS 是否需立刻觸發第一次 archive（§15.6 規則）；(b) 依前端 Agent 回報之缺口 / 後端需求，評估是否補後端 endpoint（如 `/studies/{id}/series` 或真實 AI mask）；(c) 派 Stage C dispatch（DICOM 渲染）

### 待決定事項

| # | 議題 | 預設方向 / 選項 | 卡在哪 |
|---|---|---|---|
| 1 | AI 分割模型來源 | PLAN §9.4：① pretrained ultrasound checkpoint ② 最小 U-Net + 隨機 weight ③ Otsu mock | 工程師是否已有手邊的 ultrasound checkpoint 可用？沒有的話走 ③ |
| 2 | Sample DICOM 來源 | PLAN §14：① pydicom-data ② TCIA ③ 自製 synthetic | Phase 4 demo 之前要決定 |
| 3 | README env var 稽核 | 是否需要在 §15.2 新規範生效後做一次補登 | 待工程師確認是否有遺漏的 env var |
| 4 | 前端 UI/UX / 瀏覽器相容 / 效能 / 無障礙規範 | 列於 `frontend/CLAUDE.md` §11 待補清單 | 等前端真正開始寫元件、需要做這些決策時才補；現在補只是空談 |
| 5 | venv Python 版本 | 目前 3.8.8（Anaconda），系統有 3.12.2；用戶將其降為低優先 | 不阻擋；等真的踩到 3.8 限制再重建 |
| 6 | 後端 endpoint 補完計畫 | `/studies/{id}/series` 與 `/series/{id}/instances` 是前端高機率會需要的；真實 AI mask 也是 | 等前端 Stage C 開始整合時 confirmed 再排程 |

---

## B. 工作脈絡（按需查閱）

### 已完成里程碑

> 詳細清單與 API 狀態見 [PROGRESS.md](../PROGRESS.md)。本節只列關鍵里程碑。

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
- **M13 — AI 工作流優化 Phase 1（Hybrid Doc 重組）**（2026-05-14）：
  - 根目錄文件搬遷：`PLAN.md` → `docs/PLAN.md`、`IMPLEMENTATION.md` → `docs/IMPLEMENTATION.md`
  - `docs/archive/` 建立：`QUICKSTART.md`、`STORAGE_BACKEND.md`、`COMMIT_GUIDE.md`（不再活躍）
  - PROGRESS 採「PROGRESS 觸發式 archive」機制（>150 行或季末切到 `docs/archive/PROGRESS_YYYY_QN.md`）
  - SESSION_HISTORY A/B 段拆分（A 必讀、B 按需）
- **M14 — Phase 2（雙端結構對稱）**（2026-05-14）：
  - `frontend/` 鏡像主 Agent 結構：`frontend/context/`（HANDOFF、DISPATCH、SESSION_HISTORY）、`frontend/docs/`（IMPLEMENTATION、未來 archive）
  - 前端 `SESSION_HISTORY.md` 同步 A/B 拆分
- **M15 — Phase 3（API/Schema spec 自動化）**（2026-05-14、commits `f086072` + `e93e6cf`）：
  - `scripts/gen_api_spec.py`（FastAPI APIRoute 反射 → `docs/generated/api_spec.md`，9 endpoints）
  - `scripts/gen_db_schema.py`（SQLAlchemy `Base.metadata` + 最新 alembic revision → `docs/generated/db_schema.md`，4 tables）
  - `scripts/hooks/pre-commit`（bash、跨 Windows Git Bash）+ `git config core.hooksPath scripts/hooks`
  - `frontend/context/HANDOFF.md` §3/§4 由「duplicate spec」退化為「補充說明」（指向 generated 為權威來源）
- **M16 — Phase 4（CLAUDE.md v1.2）**（2026-05-14、commit `688f098`）：
  - 根 `CLAUDE.md`：§8 ⚠️ 風險說明表格化、§10 加 R3（Doc Impact 自動檢測）+ R4（Stale Warning >30 天）、§15.6 加 PROGRESS 觸發式 archive 規範
  - `frontend/CLAUDE.md`：§6.5 觸發式 Archive、§9.7 Stale Warning（對稱根 §10 R4），版本升 v1.1

### 上次 session 結尾狀態

- **日期**：2026-05-14（AI 工作流優化 Phase 1-4 全部完成 + 已 push）
- **本批 session 完成（單日 2026-05-14）**：
  1. **Phase 1（Hybrid Doc 重組）**：PLAN / IMPLEMENTATION 搬入 `docs/`、QUICKSTART / STORAGE_BACKEND / COMMIT_GUIDE 進 `docs/archive/`、SESSION_HISTORY A/B 拆分
  2. **Phase 2（雙端結構對稱）**：`frontend/context/`、`frontend/docs/` 建立，HANDOFF / DISPATCH / SESSION_HISTORY 全部搬進 `frontend/context/`
  3. **Phase 3（spec 自動化）**（commits `f086072` + `e93e6cf`）：`gen_api_spec.py`、`gen_db_schema.py`、pre-commit hook、`docs/generated/` 建立、HANDOFF §3/§4 退化為補充說明
  4. **Phase 4（CLAUDE.md v1.2）**（commit `688f098`）：§8 風險表格化、§10 加 R3 / R4、§15.6 PROGRESS 觸發式 archive；`frontend/CLAUDE.md` 同步升 v1.1
- **Commit 序列（最近，全部已 push）**：
  ```
  688f098 docs(claude): v1.2 — Doc Impact 檢測 / Stale Warning / PROGRESS 觸發式 archive + 表格化風險說明
  e93e6cf docs(generated): 補 db_schema.md 4 表完整 schema
  f086072 chore(docs): API spec / DB schema 自動產生機制（Phase 3）
  ```
- **重大認知變更**：
  - 「Doc Impact 檢測」由 prompt 規則 + pre-commit hook 雙層保障 — generator 自動同步 `docs/generated/`，主 Agent 規則覆蓋「補充說明」人工同步段
  - 「Stale Warning」開啟自我約束機制：讀重要文件前 git log -1 偵測 > 30 天就警告
  - 「PROGRESS 觸發式 archive」採 >150 行或季末兜底，避免時間驅動的 archive 動作在低活動期空跑
- **下個 session 起手建議**：
  1. **啟用新規則自我驗證**：下次起手讀任何 Tier 1 文件前跑 R4 stale check（≥30 天 warn）
  2. **PROGRESS.md 體積評估**：目前 root 與 frontend 兩個 PROGRESS 是否已逼近 150 行 → 若是、立即執行第一次觸發式 archive 到 `docs/archive/PROGRESS_2026_Q2.md`
  3. **開新 session 給前端 Agent 執行 Stage B**：起手語「依 `frontend/CLAUDE.md` §1 必讀清單啟動，然後依 `frontend/context/DISPATCH.md` 開始當前任務」
  4. 前端 Agent 完成 Stage B 後：讀 `frontend/PROGRESS.md` 看完成記錄與後端需求 → 主 Agent 評估後端補完 → 派 Stage C dispatch
