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

### 系統現況（2026-05-18）

- **定位**：AI-ready Ultrasound DICOM 平台 MVP（非完整 PACS 替代）
- **階段**：**Phase 2 + Phase 2.5 + Phase 3 task #10 + §6.12 dedup 完成** — 前端 SPA E2E ✅ + Stage C UX 已解決 + §5.4 backfill 已 apply + AIResult schema + `/upload` duplicate detection (idempotent 200 + 409 conflict)、52 tests 全綠。**下一步主軸**：「AI 真實功能優先序壓低、系統架構優先」 — 剩餘候選：① init_db/alembic race condition 根治 (§6.13) ② Conflict resolution UI / replace endpoint (§6.14、§6.12 收尾留下、需先等 §6.4 auth) ③ Sample DICOM 多 study/series (PLAN §14) ④ Logging/audit (§6.3) ⑤ Production 部署準備
- **Backend**：FastAPI + PostgreSQL + SQLAlchemy + pydicom，11 個 API endpoints 中 9 個完整實作（含 2026-05-15 新增 `/studies/{id}/series` + `/series/{id}/instances`）、2 個（`/ai/segment/{id}`、`/ai/result/{id}`）為 stub；DB schema 5 tables（含 2026-05-19 新增 `ai_results`、待工程師接演算法時寫入）；`/upload` 2026-05-19 加 duplicate detection (idempotent 200 / 409 conflict / new SOP 新建)
- **CORS**：✅ dev allow `http://localhost:5173`（Vite default）
- **驗證層**：6 個必填欄位全部就位（PatientID / StudyInstanceUID / SeriesInstanceUID / SOPInstanceUID / Modality / PixelData）+ Modality 白名單（US）
- **Frontend**：✅ **完整 SPA E2E 可用** — React 19 + Vite 8 + TS 6 + Cornerstone3D v4.22 + AppContext (5 fields + cascade) + Layout/TopBar/StudyList/MetadataPanel/AIPanel/DicomViewer 全業務元件 + API client + `VITE_API_BASE_URL` env var 制度。Stage C UX 缺口已解決
- **AI 推論**：尚未實作（Phase 3 任務）
- **測試**：52 個測試（單元 9 / 整合 11 / API 29 / ORM 3；2026-05-19 加 3 個 dedup integration test），用 in-memory SQLite + StaticPool 隔離。前端尚無測試套件
- **儲存**：本地檔案系統（`storage/{patient}/{study}/{filename}.dcm`），已透過 `StorageBackend` 抽象預留 S3 接口
- **DB Migration 工具**：✅ Alembic 已導入（2026-05-12），baseline `20809e26d134` + Series migration `e25c80289a9c` (2026-05-15) + AIResult migration `91725486ef55` (2026-05-19) 共 3 個 migration、五表完整；目前 alembic_version = `91725486ef55`
- **DB 資料狀態（2026-05-18 backfill 後）**：1 study + 1 series + 8 instances 全部 link 到 series 1 (uid `...593537`)；orphan count=0。Instance ID gap [2, 5] 已澄清為 PostgreSQL SERIAL sequence 在 IntegrityError rollback 後不 reset 的正常設計（不是 bug）。連帶發現 upload pipeline 缺 graceful duplicate detection → 新 known issue PROGRESS §6.12
- **AI 操作規範**：CLAUDE.md **v1.2**（2026-05-14、commit `688f098`）— v1.1 之上再加 R3 Doc Impact 檢測 / R4 Stale Warning / §15.6 PROGRESS 觸發式 archive；§8 風險說明表格化
- **文件結構（Hybrid）**：根目錄為跨專案文件、`docs/` 為後端深入文件（PLAN、IMPLEMENTATION）、`docs/generated/` 為 auto-gen 權威來源（api_spec.md / db_schema.md）、`docs/archive/` 為歷史備檔；frontend/ 鏡像同樣結構
- **前後端分工**：完整檔案機制 — `frontend/CLAUDE.md` v1.1（前端規範）、`frontend/context/HANDOFF.md`（後端狀態鏡像、主 Agent 維護）、`frontend/context/DISPATCH.md`（覆寫式任務交付）、`frontend/PROGRESS.md`、`frontend/context/SESSION_HISTORY.md`（前端 Agent 維護）
- **自動化機制**：`scripts/hooks/pre-commit`（git config core.hooksPath 已啟用）偵測 `main.py` / `models.py` / `alembic/versions/*.py` 變動 → 自動 regenerate `docs/generated/` 並 `git add`
- **個人學習筆記**：`learning/` 資料夾（gitignored）— 主 Agent 解釋技術後可存檔

### 進行中的任務

- 無 in-flight 程式碼修改（主 Agent 端）
- **前端**：task #9 已完成；目前無 active 前端 dispatch（`frontend/context/DISPATCH.md` status: completed）。下個前端 dispatch 等系統架構 / Phase 3 backend scaffolding 推進後才派（前端 AIPanel mask overlay 真實渲染等工程師接好真實 AI endpoint 後才動）
- **主 Agent 下一步**：§6.12 dedup 已完成（2026-05-19）。剩餘候選（待工程師決定下個項目）：① init_db/alembic race condition 根治 (§6.13) ② Conflict resolution UI / replace endpoint (§6.14、§6.12 收尾留下、需先等 §6.4 auth) ③ Sample DICOM 多 study/series (PLAN §14) ④ Logging/audit (§6.3) ⑤ Production 部署準備
- **R4 stale check 規則調整**（2026-05-16，工程師授權）：主 Agent 改為 per-Read inline、active phase 不再做 blanket per-session 全掃；不動 CLAUDE.md 文字（仍符合 §10 R4 letter）

### 待決定事項

| # | 議題 | 預設方向 / 選項 | 卡在哪 |
|---|---|---|---|
| 1 | AI 分割模型來源 | PLAN §9.4：① pretrained ultrasound checkpoint ② 最小 U-Net + 隨機 weight ③ Otsu mock | 工程師是否已有手邊的 ultrasound checkpoint 可用？沒有的話走 ③；Phase 3 backend 開工時需先決定 |
| 2 | Sample DICOM 來源 | PLAN §14：① pydicom-data ② TCIA ③ 自製 synthetic | Phase 4 demo 之前要決定；可順帶用於驗證 §5.4 backfill |
| 3 | README env var 稽核 | 是否需要在 §15.2 新規範生效後做一次補登 | 待工程師確認是否有遺漏的 env var |
| 4 | 前端 UI/UX / 瀏覽器相容 / 效能 / 無障礙規範 | 列於 `frontend/CLAUDE.md` §11 待補清單 | task #9 SPA 已驗收，現有風格是「深色主題 + Cornerstone 黑底」；Phase 4 demo 前若有正式 UX 規格再補 |
| 5 | venv Python 版本 | 目前 3.8.8（Anaconda），系統有 3.12.2；用戶將其降為低優先 | 不阻擋；等真的踩到 3.8 限制再重建 |
| 6 | 後端 endpoint 補完計畫 | ✅ Series 兩 endpoints 已於 2026-05-15 補完 (`9967f71`)；剩 AI mask 真實 PNG（Phase 3 範圍） | 已解決 series 部分 |
| 7 | ~~§5.4 backfill 走 (a) script 還是 (b) Alembic data migration~~ | ✅ 已決：(a) 一次性 script (2026-05-18) | — |
| 8 | ~~§5.4 (c) instance ID gap 處理深度~~ | ✅ 已決：PostgreSQL SERIAL 設計、不是 bug、不修 transaction handling；連帶 issue「upload 缺 duplicate detection」記 §6.12 | — |
| 9 | AI 真實功能何時接 | 工程師裁示「優先序低、系統架構完工後再接、由工程師親自串接」（2026-05-18） | 不再阻擋；Phase 3 backend scaffolding 仍可做但不接 PyTorch |
| 10 | 系統架構優先項目排序 | task #10 + §6.12 dedup 已完成；剩餘候選：① init_db/alembic race condition 根治 (§6.13) ② Conflict resolution UI / replace endpoint (§6.14、§6.12 收尾留下、需 §6.4 auth) ③ Sample DICOM ④ Logging/audit (§6.3) ⑤ Production 準備 | 待工程師裁示下一步 |
| 11 | init_db/alembic race condition 根治時機 (§6.13) | 拿掉 main.py:startup_event 的 init_db() — 屬 bug fix 性質、但動 db 啟動行為需慎重；同時 conftest.py:35 Base.metadata.create_all 走法可能需配套 | 等工程師裁示 |
| 12 | §6.14 Conflict resolution UI / replace endpoint 何時實作 | §6.12 dedup 完成留下；需要 admin 概念 → 必須先做 §6.4 auth；MVP 階段不在 scope | 等 §6.4 auth 階段一起做 |

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

---

### 2026-05-19 session 結尾狀態（§6.12 Upload duplicate detection 完工）

- **本次主 Agent 工作**：
  - **§6.12 dedup 完工**：`main.py /upload` 加 SOP UID + SHA256 hash 三分支邏輯
    - 同 SOP + 同 bytes → 200 + `duplicate=true` + 既有 instance_id (idempotent)
    - 同 SOP + 不同 bytes → 409 + existing_instance_id/existing_hash/new_hash/suggested_actions (keep_existing / save_as_new / manual_overwrite)
    - 同 SOP + storage 上原檔不存在 → 409 + `existing_file_missing=true` (邊角、提示手動清理)
    - 新 SOP → 既有行為 + `duplicate=false`
    - **Storage / DB 在 conflict 情境完全不動**（無 orphan 檔、無 sequence gap）
  - **遵循 CLAUDE.md §13**「UID uniqueness 違反時必須回傳明確錯誤，不可靜默覆蓋」 — 工程師裁示走方案 A（只做偵測 + 409 詳盡訊息、不實作 replace）
  - **加 helper**：`db_service.get_instance_by_sop_uid(db, sop_uid)`
  - **加 3 個 integration test** (`tests/test_dicom_service.py`)：idempotent 重傳 / 409 conflict / existing_file_missing 邊角
  - **既有 test 影響**：grep 確認 0 既有 case 涵蓋 duplicate SOP → 不需修改既有 test
  - **§6.14 新 known issue**：「Conflict resolution UI / replace endpoint」 — 等 §6.4 auth 完成後實作（待決定 #12）
  - **文件同步**：
    - `PROGRESS.md` §1 加 duplicate detection 核心業務條 + §2 API 表 /upload 加 duplicate 欄位 + 409 註記 + §3 測試三層分布更新 (52 total、整合 11) + §6.12 標已解決 + §6.14 新增
    - `frontend/context/HANDOFF.md` §3.1 加 duplicate 欄位說明 + §3.2 加 409 conflict 格式 + §7 加 2026-05-19 兩條 (task #10 + dedup)
    - `context/SESSION_HISTORY.md` A 段系統現況 / 進行中 / 待決定 (#10 / #12) + B 段本記錄
- **新增 / 修改檔案**：
  - 修改：`main.py`（imports + dedup 三分支邏輯 + duplicate=false 加進新建 response）、`db_service.py`（get_instance_by_sop_uid helper）、`tests/test_dicom_service.py`（3 新 test + helper `_build_minimal_dicom`）
  - 自動 regen：`docs/generated/api_spec.md`（pre-commit hook 因 main.py 變動觸發；只 line number shift、無新 endpoint）
  - 文件同步：PROGRESS、SESSION_HISTORY、HANDOFF
- **R3 Doc Impact**：API route 行為變動 + main.py 變動 → pre-commit hook 自動 regen api_spec.md；HANDOFF §3.1/§3.2 補充說明已更新（response 欄位 + 409 格式）；無 DB schema 變動、無 env var 變動
- **R1 跨節一致性**：§6.12 標已解決 ↔ §1 / §3 加 dedup feature — 一致 ✓
- **下次 session 主 Agent 起手**：問工程師決定下一步（待決定 #10 剩餘候選：§6.13 init_db 根治 / PLAN §14 sample DICOM / §6.3 logging / production 準備；§6.14 / §6.4 屬中後期）
- **commit 狀態**：6 個檔變動待 commit；commit message 草稿 `feat(api): §6.12 upload duplicate detection — SOP UID + SHA256 hash + idempotent 200 / 409 conflict`

---

### 2026-05-19 session 早段（Phase 3 task #10 完工 — AIResult schema scaffolding） — commit `b6a55da`

- **本次主 Agent 工作**：
  - **task #10 完工**：依 PLAN §9.3 加 `AIResult` model（classical SQLAlchemy 1.x style 與既有 models.py 一致）+ Alembic migration `91725486ef55_add_ai_results_table.py`（upgrade: CREATE TABLE + pkey index + instance_id index + FK；downgrade: drop in reverse order）
  - **意外發現 + 處理**：alembic upgrade 遇 `DuplicateTable` — 根因為 `main.py:startup_event` 的 `init_db()` (Base.metadata.create_all) 副作用搶先建表、但不更新 `alembic_version`。Workaround：drop empty 表 + 重跑 alembic upgrade（user 授權）。根治列為 §6.13 known issue
  - **完整驗證**：alembic current → 91725486ef55 (head) ✓；upgrade/downgrade round-trip ✓；pre-commit hook generator regen `docs/generated/db_schema.md`（4→5 tables、ai_results 欄位 / FK / index 全對）✓
  - **新增 test**：`tests/test_ai_result_model.py` 3 個 ORM-level test — (1) 全欄位 CRUD + created_at default (2) nullable 欄位接受 None (3) `Instance.ai_results` back-relationship 雙向。pytest 49 全綠（46→49）
  - **文件同步**：
    - `PROGRESS.md` §1 加 AIResult model 條 + §3 測試三層分布加 ORM 測試列 (49 total) + §5 Phase 3 task #10 [x] + §6.13 新 known issue (init_db race) + §7 結構加 migration file + test file
    - `context/SESSION_HISTORY.md` A 段系統現況 / 進行中 / 待決定 (#10/#11) + B 段本記錄
  - **未動 HANDOFF.md §7**：本次 schema 新增對前端目前無影響（前端用 AI endpoint stub、不直接 query ai_results）；待 Phase 3 task #11/#12 工程師接演算法、AI endpoint 真實實作時再更新
- **新增檔案**：`alembic/versions/91725486ef55_add_ai_results_table.py`、`tests/test_ai_result_model.py`
- **修改檔案**：`models.py`（imports + AIResult class + Instance.ai_results relationship）、`docs/generated/db_schema.md`（generator 自動）、PROGRESS、SESSION_HISTORY
- **R3 Doc Impact**：DB schema 變動 → pre-commit hook 自動 regen `docs/generated/db_schema.md`；API route 未變、env var 未變
- **R4 Stale**：本 session 已 inline check 過、9 份 Tier 1 文件全在 30 天內
- **下次 session 主 Agent 起手**：問工程師決定下一步（待決定 #10：剩餘候選 §6.12 upload duplicate / §6.13 init_db 根治 / PLAN §14 sample DICOM / §6.3 logging / production 準備）
- **commit 狀態**：5 個檔變動 + 2 個新增待 commit；commit message 草稿 `feat(db): Phase 3 task #10 — AIResult model + Alembic migration 91725486ef55`

---

### 2026-05-18 session 結尾狀態（§5.4 backend backfill 完工 + 工程師更新 AI 優先序） — commit `671450a`

- **本次主 Agent 工作**：
  - **§5.4 (a) backfill apply**：寫 `scripts/backfill_series_uid.py`（dry-run + `--apply`、重讀 DICOM 確認 SeriesUID + 不自行新建 series 安全機制）；dry-run 確認 3 個 orphan (id=1/3/4) 都對應現有 series 1 → `--apply` 寫入 → orphan count=0 + API `/series/1/instances` 5→8 筆。Schema 與 Series 表未動
  - **§5.4 (c) ID gap 澄清**：結論為 PostgreSQL SERIAL sequence 設計（IntegrityError rollback 不 reset、預期行為）；推測 gap 來源為 upload 重傳同 SOP UID 被 UNIQUE constraint 擋；無需修 transaction handling。連帶發現 upload pipeline 回 500 + 裸 SQL error 不友善 → 新 known issue §6.12
  - **工程師裁示更新（重要）**：AI 真實功能優先序壓低、系統架構優先、演算法與推論模型由工程師親自串接（主 Agent 不選型）→ 已存 project memory `project_ai_inference_priority.md`
  - **文件同步**：
    - `PROGRESS.md` §5 Phase 2.5 兩項 [x] 完成 + §6.12 加新 known issue + §7 加 backfill script 到 scripts/
    - `frontend/PROGRESS.md` §5.4 標已解決於 `scripts/backfill_series_uid.py --apply`
    - `frontend/context/HANDOFF.md` §7 加 2026-05-18 backfill apply 紀錄
    - `context/SESSION_HISTORY.md` A 段系統現況 / 進行中 / 待決定 (#7-#10) + B 段本記錄
- **新增檔案**：`scripts/backfill_series_uid.py`（179 行、安全 dry-run + --apply + post-apply 驗證）
- **R3 Doc Impact**：純 script + docs、無動 main.py / models.py / alembic — 不 trigger pre-commit hook、不 regen `docs/generated/`
- **下次 session 主 Agent 起手**：問工程師決定下一步（待決定 #10 — Phase 3 scaffolding vs upload duplicate detection vs logging vs sample DICOM）。AI 真實推論不在主 Agent scope（工程師親自接）
- **commit 狀態**：本批 5 個檔變動待 commit；commit message 草稿 `feat: scripts/backfill_series_uid.py — §5.4 orphan instances 修舊資料`

---

### 2026-05-18 session 早段（task #9 審查 + 下一步裁示 + 文件同步）— commit `1969808`

- **本 session 主 Agent 工作**：純文件審查與同步、未動程式碼
  - 讀 frontend PROGRESS / DISPATCH / HANDOFF / CLAUDE.md + 根 PROGRESS + 雙端 SESSION_HISTORY 確認 task #9 完工狀態（11 commits `fb656c6` → `fa0dd34` 已 push、E2E 驗收 ✅）
  - 問工程師下一步主軸 → 工程師裁示「§5.4 後端 backfill 先處理」
  - 問工程師 Stage C UX 缺口處理 → 工程師裁示「標已解決於 commit `40d766d` (Fix-J)」
  - 同步 4 份文件：
    - `frontend/PROGRESS.md` §4.4 — 主段標已解決於 `40d766d`、整體狀況彙整段結案
    - `PROGRESS.md` §6.11 標已解決 + §1 加 task #9 完工項 + §5 task #9 改 [x] + 加 Phase 2.5 §5.4 backfill 兩條
    - `frontend/context/DISPATCH.md` — frontmatter `status: active` → `completed`、加 completed_commits 清單、加「⏸️ 本任務已完成」說明段
    - `context/SESSION_HISTORY.md` A 段（系統現況 / 進行中 / 待決定）+ B 段（本記錄）
- **跨 territory 動 frontend/PROGRESS §4.4**：屬 §15.5 例外（主 Agent 緊急同步 user 驗收結果），commit message 會明示
- **未動 `frontend/context/SESSION_HISTORY.md`**：屬前端 Agent territory；下次前端 Agent session 啟動會自行同步「Stage C UX 已標解決」與「DISPATCH status: completed」
- **R3 Doc Impact 檢測**：本批僅文件同步、無 API route / DB schema / env var 變動、無需 regen `docs/generated/`
- **下次 session 主 Agent 起手**：直接進入 §5.4 後端 backfill 工作
  1. 先讀 `models.py` (`Instance` / `Series` model) + 看現有 upload pipeline (`db_service.py:create_instance` 等) 確認 schema 與邏輯
  2. SQL 查實際 orphan 狀態（連 PostgreSQL）：`SELECT id, sop_instance_uid, study_instance_uid, series_instance_uid, file_path FROM instances WHERE series_instance_uid IS NULL ORDER BY id;`
  3. 問工程師走 (a) 一次性 script 還是 (b) Alembic data migration（待決定事項 #7）
  4. 寫 `scripts/backfill_series_uid.py`（或 alembic migration）
  5. (c) 確認 instance ID gap (2/5/11+) 來源：`SELECT MAX(id), COUNT(*) FROM instances;` + 看 upload pipeline transaction handling
  6. 完工後同步根 PROGRESS §5 + §1 + frontend/context/HANDOFF.md §7 重大變更段、push commits
- **commit 狀態**：4 份文件變動待 commit；commit message 草稿 `docs: task #9 收尾 — Stage C UX 標已解決 + 下一步 §5.4 backend backfill`
