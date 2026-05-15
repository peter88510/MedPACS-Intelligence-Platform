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

- 無 in-flight 程式碼修改（主 Agent 端，本批已 push 完）
- **DISPATCH 改派為 Stage C 修正版**（`a7e973e`）— 純 viewer 已過關但影像尺寸不完整；新 dispatch 要前端 Agent 補 `viewport.resetCamera()` + 容器 aspect-ratio + 一併 commit Stage C 完整版
- **Backend Series 結構補完已 push**（`9967f71`）— upload pipeline 加 series upsert / Instance 加 series_instance_uid FK / 2 新 endpoints (`/studies/{id}/series` + `/series/{id}/instances`) / migration `e25c80289a9c` / 46 tests 全綠 / docs 全同步
- **主 Agent 進入第二輪待命**，等：① 工程師跑 `alembic upgrade head` ② 前端 Agent 完成 Stage C 修正 dispatch
- 下一個主 Agent 任務（前端完工後）：(a) 審查前端 Stage C 完整版 commit、(b) 同步根 PROGRESS §5「下一步」標 Stage C 完成、(c) 派 Phase 2 task #9 dispatch（API client + AppContext + 4 業務元件 + `VITE_API_BASE_URL` env var 制度）

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

- **日期**：2026-05-14（同日多 batch；Phase 1-4 重組完成後接續 Stage C dispatch + backend instance_id 補正）
- **本批 session 完成（單日 2026-05-14、Stage C dispatch batch）**：
  1. **CLAUDE.md v1.2 規則首次實戰驗證**：
     - R4 Stale Check 全 9 份 Tier 1 文件均 = 2026-05-14（同日新增 / 修訂），無一觸發 ≥30 天 warn
     - PROGRESS Archive 評估：root 已完成段 ~45 行 / frontend ~31 行，均遠未達 150 行門檻，本次不 archive
  2. **派發 Stage C dispatch 到前端 Agent**（commit `cbca650`）：純 viewer 起手、CSS Modules、API URL hardcode、StrictMode 雙 mount 注意事項齊備
  3. **同步前端 Stage A/B 完成狀態進根 PROGRESS.md**：§1 新增 Frontend 段、§5 Phase 2 勾選 #7 + #8 Stage A/B
  4. **README.md Project Structure stale tree 修正**（commit `93f274c`）：補 Phase 1+2 reorg 後新增的 `context/`、`docs/`、`frontend/context/`、`frontend/docs/`、`docs/generated/`、`scripts/`，移除已遷檔的根層引用（PLAN / IMPLEMENTATION / SESSION_HISTORY）
  5. **新 feature：POST /upload response 加 `instance_id`**（commit `40fd1e9`）：non-breaking 欄位新增，解除前端 / 工程師「拿到 instance DB id 必須繞 psql」窘境。改動 main.py + 1 test 加斷言 + README + HANDOFF §3/§7 + DISPATCH 驗證步驟；36/36 pytest 全綠；pre-commit hook 自動 regen `docs/generated/api_spec.md`
- **Commit 序列（本批，全部已 push）**：
  ```
  9967f71 feat(api): Series 結構補完 — upload upsert + 2 endpoints + Instance FK
  a7e973e docs(dispatch): 覆寫為 Stage C 收尾 — 影像尺寸自適應 + 一併 commit
  6bd4bd8 docs(session): 收尾 — Stage C 已 dispatch、主 Agent 進入待命
  40fd1e9 feat(api): POST /upload response 加 instance_id 欄位（non-breaking）
  93f274c docs(readme): 同步 Project Structure 至 Phase 1+2 reorg 後狀態
  cbca650 docs: 同步前端 Stage A/B 完成狀態 + 派發 Stage C dispatch
  6fdbe91 docs(session): 加入下次 session 啟動強制動作區塊（R4 + PROGRESS archive 評估）
  ```
- **2026-05-15 補充批次（Stage C 結果審查 + Series 補完）**：
  - 審查前端 Stage C：純 viewer 達成（瀏覽器以 instance_id=1 渲染 Peter_Quiet_1.dcm 成功）但影像尺寸被切。前端 Agent 列三個可能因素於 §4.4，等主 Agent 拍板處理時機
  - 工程師拍板：尺寸缺口立刻修 + 一併 commit Stage C；backend 走完整解
  - 派 Stage C 尺寸修正 dispatch（`a7e973e`）— scope 嚴格限縮 viewport.resetCamera() + aspect-ratio
  - 主 Agent 自行做 backend Series 補完（`9967f71`）— 發現 schema 比預期糟（upload 跳過 series upsert + Instance 沒 series FK，導致 `/series/{id}/instances` 完全無法實作）；走 alembic migration 完整解、46 tests 全綠
  - **遺留**：工程師需跑 `alembic upgrade head` 在實際 dev DB 上、否則 backend 重啟會找不到新 column（test 用 in-memory sqlite + create_all 不受影響）
- **重大認知變更**：
  - v1.2 規則確實首戰即捉到漏網：README.md Project Structure 是 Phase 1 reorg 漏改的 stale doc，靠 R3 概念與工程師事件回報才補上 → 證實「Doc Impact 檢測」對結構性 reorg 仍需主 Agent 視角而非單靠 pre-commit hook
  - `/upload` response 缺 `instance_id` 是 API 設計小坑 — frontend/PROGRESS §5 早 flag、但直到工程師實戰才被觸發補上；提醒：派 dispatch 前要 dry-run 驗證步驟可行性
  - Claude Code session 之間 DISPATCH cache：前端 Agent session 啟動後讀過 DISPATCH 就快取於 context，主 Agent 中途覆寫 DISPATCH 對該 session 不可見，需起新 session 才能讀到。**未來規則建議**：派新 dispatch 後一律請工程師起新前端 session（不要嘗試在舊 session 內推進）
- **下個 session 起手建議（前端完工後審查階段）**：
  1. **R4 Stale Check** 對 9 份 Tier 1 文件重做一次（規則常駐）
  2. **讀 `frontend/PROGRESS.md`** 看 Stage C 完成記錄、新後端需求清單、新缺口
  3. **同步根 `PROGRESS.md`**：§5 Stage C 改為已完成（加 commit hash）、Phase 2 task #9 升為下一步
  4. **評估後端補完**：依前端回報的後端需求（最可能：`/studies/{id}/series` + `/series/{id}/instances`）決定是否派 backend task
  5. **派 Phase 2 task #9 dispatch**：API client + AppContext + 4 業務元件 + `VITE_API_BASE_URL` env var 制度
  6. **修 `frontend/PROGRESS.md` lines 5, 64 的 `./IMPLEMENTATION.md` stale link**（→ `./docs/IMPLEMENTATION.md`）— 屬前端 Agent territory，但若前端 Agent 沒順手修，下次 session 可標 §9.5 結構性修正例外動一下並在 commit message 註明
