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

### 系統現況（2026-06-11）

- **定位**：AI-ready Ultrasound DICOM 平台 MVP（非完整 PACS 替代）
- **階段**：**Phase 3 AI 整合 — 端到端打通 + facade 瘦身 + GPU 提速完成** — AI engine 整合層 ✅(2026-06-10、`e934025`) + 端到端驗證 ✅(2026-06-11) + **facade re-vendor @`5340456` ✅(`8f15e18`) + engine 簡化接 facade ✅(`bca26ab`、~250→~150 行) + GPU 環境 `medpacs_gpu` ✅**；84 tests 全綠。**startup warmup 已完成（2026-06-12、`418f29d` + review fixes）**。**剩**：Phase 2b trim(viz/tools/experiments/font + 砍 visualdl、需 GPU env 實測、保留) → 其後 mask PNG endpoint + 前端接數值。工程師親接 AI 演算法、主 Agent 接整合層
- **Backend**：FastAPI + PostgreSQL + SQLAlchemy + pydicom，**11 個 API endpoints 全完整**（AI 兩端 2026-06-10 真實實作、端到端 2026-06-11 驗證）；分層：main.py=API root / `core/` 設定 / `db/` session / `models/` ORM / `services/`(db_service+storage+storage_backend+measurement_type+**ai_engine/**) / `validation/`；DB schema 5 tables，`ai_results` +4 量測欄、`instances` +2 device 欄；`/upload` 抽 Manufacturer/ModelName + dedup
- **CORS**：✅ dev allow `http://localhost:5173`（Vite default）
- **驗證層**：6 個必填欄位全部就位（PatientID / StudyInstanceUID / SeriesInstanceUID / SOPInstanceUID / Modality / PixelData）+ Modality 白名單（US）
- **Frontend**：✅ **完整 SPA E2E 可用** — React 19 + Vite 8 + TS 6 + Cornerstone3D v4.22 + AppContext (5 fields + cascade) + Layout/TopBar/StudyList/MetadataPanel/AIPanel/DicomViewer 全業務元件 + API client + `VITE_API_BASE_URL` env var 制度。Stage C UX 缺口已解決
- **AI 推論**：核心演算法 vendored `./AI/` **@ `5340456`**（含上游 `inference.py` facade + `algorithm/single_frame.py`）；MedPACS 整合層 engine 改呼叫 `inference.analyze`（去 importlib hack/reach-in/numpy 正規化、接 warm segmenter）。tuning 100% 上游 `run_config`。resolver C62→excursion/L154→thickness、design §4 envelope
- **執行環境**：**改用 conda `medpacs_gpu`**（clone 自 CLI `diaphragmalgo_env`、Python 3.10.18 + paddlepaddle-gpu 3.2.0/cu118 + 後端 web 依賴）— GPU 提速已驗證。舊 `.venv`(3.8/CPU paddle) 退役。啟動：`conda activate medpacs_gpu` → `uvicorn main:app --reload`；pytest 需 `PYTHONUTF8=1`（pytest.ini 中文、cp950 locale）
- **測試**：84 個測試（單元 9 validators + 13 measurement_type + 12 ai_engine / 整合 13 / API 31 / ORM 6），in-memory SQLite + StaticPool 隔離；AI engine 走 DI fake、不碰 paddle。前端尚無測試套件
- **儲存**：本地檔案系統（`storage/{patient}/{study}/{filename}.dcm`），已透過 `StorageBackend` 抽象預留 S3 接口
- **DB Migration 工具**：✅ Alembic，baseline `20809e26d134` + Series `e25c80289a9c` + AIResult `91725486ef55` + measurement fields `7f3c9a2b1d04` (2026-06-09、instances +2 / ai_results +4) 共 4 個 migration；工程師已 `alembic upgrade head`、alembic_version = `7f3c9a2b1d04`
- **DB 資料狀態（2026-05-18 backfill 後）**：1 study + 1 series + 8 instances 全部 link 到 series 1 (uid `...593537`)；orphan count=0。Instance ID gap [2, 5] 已澄清為 PostgreSQL SERIAL sequence 在 IntegrityError rollback 後不 reset 的正常設計（不是 bug）。連帶發現 upload pipeline 缺 graceful duplicate detection → 新 known issue PROGRESS §6.12
- **AI 操作規範**：CLAUDE.md **v1.3**（2026-06-09、commit `dc0584c`、工程師授權）— v1.2 之上 §6 分層落點更新 + §15.4 改為目錄結構規範(core/db/models/services)；v1.2 含 R3/R4/§15.6/§8 表格化
- **文件結構（Hybrid）**：根目錄為跨專案文件、`docs/` 為後端深入文件（PLAN、IMPLEMENTATION）、`docs/generated/` 為 auto-gen 權威來源（api_spec.md / db_schema.md）、`docs/archive/` 為歷史備檔；frontend/ 鏡像同樣結構
- **前後端分工**：完整檔案機制 — `frontend/CLAUDE.md` v1.1（前端規範）、`frontend/context/HANDOFF.md`（後端狀態鏡像、主 Agent 維護）、`frontend/context/DISPATCH.md`（覆寫式任務交付）、`frontend/PROGRESS.md`、`frontend/context/SESSION_HISTORY.md`（前端 Agent 維護）
- **自動化機制**：`scripts/hooks/pre-commit`（git config core.hooksPath 已啟用）偵測 `main.py` / `models/*.py` / `alembic/versions/*.py` 變動 → 自動 regenerate `docs/generated/` 並 `git add`
- **個人學習筆記**：`learning/` 資料夾（gitignored）— 主 Agent 解釋技術後可存檔

### 進行中的任務

- 無 in-flight 程式碼修改；facade/engine/GPU 三批已進 master（`8a0a367` 等）。本 session：warmup 已 commit `418f29d`；review fixes（4 檔）+ PROGRESS/SESSION_HISTORY 同步待 commit + push 收尾
- **前端**：task #9 已完成；無 active 前端 dispatch。**現可派**：AIPanel 接真實 `/ai/segment`·`/ai/result`（數值層、後端已就緒）；mask overlay 等 mask PNG endpoint
- **主 Agent 下一步（Phase 3 收尾）**：① mask PNG endpoint `/ai/result/{id}/mask`（engine 已預留 `mask_path` + facade `save_mask_dir`、契約 §4.3） ② 派前端 AIPanel 接真實量測數值（後端已就緒） ③ Phase 2b trim（砍 AI/ viz/tools/experiments/font + 測 visualdl 可否移除、需 GPU env 實測）
- **R4 stale check 規則調整**（2026-05-16，工程師授權）：主 Agent 改為 per-Read inline、active phase 不再做 blanket per-session 全掃；不動 CLAUDE.md 文字（仍符合 §10 R4 letter）

### 待決定事項

| # | 議題 | 預設方向 / 選項 | 卡在哪 |
|---|---|---|---|
| 1 | AI 分割模型來源 | PLAN §9.4：① pretrained ultrasound checkpoint ② 最小 U-Net + 隨機 weight ③ Otsu mock | 工程師是否已有手邊的 ultrasound checkpoint 可用？沒有的話走 ③；Phase 3 backend 開工時需先決定 |
| 2 | Sample DICOM 來源 | PLAN §14：① pydicom-data ② TCIA ③ 自製 synthetic | Phase 4 demo 之前要決定；可順帶用於驗證 §5.4 backfill |
| 3 | README env var 稽核 | 是否需要在 §15.2 新規範生效後做一次補登 | 待工程師確認是否有遺漏的 env var |
| 4 | 前端 UI/UX / 瀏覽器相容 / 效能 / 無障礙規範 | 列於 `frontend/CLAUDE.md` §11 待補清單 | task #9 SPA 已驗收，現有風格是「深色主題 + Cornerstone 黑底」；Phase 4 demo 前若有正式 UX 規格再補 |
| 5 | ~~venv Python 版本~~ | ✅ 已決 (2026-06-11)：踩到 3.8 限制（GPU paddle 3.2.0 無 cp38 wheel）→ 改用 conda `medpacs_gpu`(Python 3.10.18 + GPU paddle)。舊 .venv 退役 | — |
| 6 | 後端 endpoint 補完計畫 | ✅ Series 兩 endpoints 已於 2026-05-15 補完 (`9967f71`)；剩 AI mask 真實 PNG（Phase 3 範圍） | 已解決 series 部分 |
| 7 | ~~§5.4 backfill 走 (a) script 還是 (b) Alembic data migration~~ | ✅ 已決：(a) 一次性 script (2026-05-18) | — |
| 8 | ~~§5.4 (c) instance ID gap 處理深度~~ | ✅ 已決：PostgreSQL SERIAL 設計、不是 bug、不修 transaction handling；連帶 issue「upload 缺 duplicate detection」記 §6.12 | — |
| 9 | AI 真實功能何時接 | 工程師裁示「優先序低、系統架構完工後再接、由工程師親自串接」（2026-05-18） | 不再阻擋；Phase 3 backend scaffolding 仍可做但不接 PyTorch |
| 10 | 系統架構優先項目排序 | 工程師回歸 + AI vendoring 完成、進入 Phase 3 整合主線；其他候選 (§6.3 logging / Production / §6.14 Conflict UI / PLAN §14 跳過) 暫降權 | 整合完成後再回看 |
| 13 | ~~Phase 3 Schema 對齊：AIResult excursion_cm 怎麼存~~ | ✅ 已決 (2026-06-09)：統一 header + JSON payload — `ai_results` +`measurement_type`/`result_json`(JSONB)/`primary_value`/`primary_unit`；新增量測類型零 migration。設計 `.work/ai_result_design.md` | — |
| 14 | ~~ai_service.py 執行模型~~ | ✅ 已決 + 已實作 + 已驗證 (2026-06-10/11)：(a) 同 process import（lazy、缺 paddle→503）。run_config 共用調參走 Option A | — |
| 15 | ~~AI 整合介面瘦身策略~~ | ✅ 已決 + 已落地 (2026-06-11)：Option 1 上游 facade `inference.py` + re-vendor @`5340456` + engine 簡化。剩 Phase 2b trim + startup warmup（保留） | — |
| 11 | ~~init_db/alembic race condition 根治時機 (§6.13)~~ | ✅ 已決 (2026-05-19)：方案 A、拿掉 startup_event 的 init_db() 呼叫、conftest 不動 | — |
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

### 2026-06-12 session 結尾狀態（Phase 3：AI engine startup warmup）

- **本 session 工作（兩段）**：
  1. **startup warmup（opt-in）實作**（commit `418f29d`、工程師 /commit）：
     - `services/ai_engine/base.py`：`DiaphragmEngine` ABC 加 concrete 預設 no-op `warmup()`（非 abstractmethod → fake/未來 engine 不需實作、測試零破壞）
     - `diaphragm_excursion_engine.py`：override `warmup()` = `_load_inference()` + `_get_warm_segmenter(EXCURSION)`，重用既有 lazy 路徑、不複製
     - `main.py:startup_event`：env-gated（`AI_WARMUP_ON_STARTUP`）+ exception-safe（`EngineUnavailableError`/任何 Exception → 降級訊息、不擋啟動）
     - 文件：`.env.example` + README Step 7 + `frontend/context/HANDOFF.md §2`；+2 test
  2. **code review（code-reviewer subagent）+ 修正**（review fixes 待 commit）：
     - 結果 0 CRITICAL / 0 HIGH / 3 MEDIUM / 4 LOW、APPROVE WITH SUGGESTIONS、紅線零命中
     - 採納修正：① `import time` 移頂層 ② `warmup()` docstring 補 `_run_lock` 並發假設 ③ HANDOFF §2 env var row ④ **Settings 收編 `AI_WARMUP_ON_STARTUP: bool`**
     - 保留不改：print vs logger（與既有 startup 一致）、`on_event` deprecation（既有技術債）
- **踩雷（重要）**：把 `AI_WARMUP_ON_STARTUP` 寫進 `.env` 後，舊版（os.getenv + Settings `extra=forbid`）→ pydantic-settings 對 dotenv 未宣告 key 直接 **forbid → 後端整個起不來**（不是 review 建議、是真 bug）。收編進 Settings 後根除；main.py 改讀 `settings.AI_WARMUP_ON_STARTUP`（型別化 bool、去字串解析）
- **設計筆記**：`learning/asgi-lifespan-and-engine-locks.md`（gitignored）— ASGI lifespan 序列性 + 雙鎖（`_init_lock` vs `_run_lock`）+ warmup 為何不需 `_run_lock`
- **commit 狀態**：warmup `418f29d` 已進 master；本批 review fixes（`main.py`/`core/config.py`/`diaphragm_excursion_engine.py`/`frontend/context/HANDOFF.md`）+ docs（PROGRESS/SESSION_HISTORY）待 commit + push
- **下次 session 起手**：Phase 3 收尾 — ① mask PNG endpoint `/ai/result/{id}/mask` ② 派前端 AIPanel 接數值 ③ Phase 2b trim（需 GPU env 實測）

---

### 2026-06-11 session 結尾狀態（續：facade re-vendor + engine 簡化 + GPU 環境收斂）

- **接續同日**：契約交付上游後，上游 agent 完成 facade（commits `8f15e18`/`bca26ab`/`972ae4e`、本機 commit）：
  1. **re-vendor @`5340456`**（`8f15e18`）：clone 上游 diff（自基準 `6139799`，僅 8 檔變動）→ file-level copy 進 `./AI/`（保留 gitignored paddleseglibs/weights/run_config.py）。新增 `inference.py`(facade) + `algorithm/single_frame.py`(抽核心)；`main.py` 改薄包；`paddleseg_segmenter.py` +`configure_output`(warm)。facade 回全 native 型別
  2. **engine 簡化**（`bca26ab`）：`DiaphragmExcursionEngine` 改呼叫 `inference.analyze`，~250→~150 行；去 importlib hack/`_build_bundle` reach-in/numpy 正規化；接 warm segmenter（lazy `prepare_segmenter()` 載一次重用）。82 tests 綠
  3. **requirements-ai GPU 調整**（`972ae4e`）：移除 CPU paddle 行、改 GPU 分裝指引 + Python 3.10 註記
- **GPU 環境收斂（重大）**：診斷出 per-frame 慢主因 = `.venv` paddle 是 **CPU-only build**（`compiled_with_cuda=False`）。CLI 原系統 = Python 3.10.18 + paddle-gpu 3.2.0/cu118。GPU paddle 3.2.0 無 cp38 wheel → 不能只換 paddle、.venv(3.8) 不可用。**解法**：`conda create --clone diaphragmalgo_env`(CLI 的 GPU env) → `medpacs_gpu` + 裝後端 web 依賴(requirements.txt)。GPU 提速經 `/ai/segment/12` 驗證。解掉待決定 #5
- **踩雷補充**：① clone repo 在 Windows 撞 git "dubious ownership" → `safe.directory` 例外 ② GPU paddle 不在一般 PyPI、要走 paddle 官方 index(cu118)；cu118 能在本機 CUDA 12.0 driver 上跑（向下相容）
- **保留未做**：startup warmup（消第一次 cold start、~10 行）、Phase 2b trim（砍 viz/tools/experiments/font + 測 visualdl 等能否移除、需 GPU env 實測）
- **下次起手**：① 決定 startup warmup ② Phase 2b trim ③ mask PNG endpoint(`/ai/result/{id}/mask`，engine 已預留 mask_path + facade `save_mask_dir`) ④ 前端 AIPanel 接真實量測數值

---

### 2026-06-11 session 結尾狀態（Phase 3 AI 整合端到端打通 + facade 契約定案）

- **本 session 三段工作**：
  1. **AI engine 整合層 + endpoint 真實實作**（commit `e934025`/`22101af`/`f7f16de`、工程師 /commit）：
     - `services/ai_engine/`：抽象 `DiaphragmEngine` ABC + 平台中立 `EngineResult`/`Measurement` + paddle `DiaphragmExcursionEngine`（#14 同 process import；sys.path 插 AI/ + importlib 避 `main` 撞名；lazy、缺 paddle→`EngineUnavailableError`→503）+ serialize→design §4 envelope + `get_engine()` factory（DI 注入、測試換 fake）
     - `main.py`：`/ai/segment` 真實流程（resolver→unknown 422 / thickness 501 / excursion·sniff 跑引擎 / EngineUnavailable 503 / 失敗留 error 列後 500）→ 寫 ai_results；`/ai/result` 回最新結果（未跑→404）
     - `MACHINE_MODEL_MAP` 填 C62→excursion / L154→thickness（**key 改 model-only**，工程師裁示）；db_service `create_ai_result` + `get_latest_ai_result_by_instance`；82 tests 全綠
  2. **端到端真實推論驗證**（工程師裝 paddle+weights、`POST /ai/segment/12` 跑完 150-frame model → 200 OK + ai_results 寫入）。途中三修：
     - `requirements-ai.txt`：cp950 locale 下 pip 撞 UTF-8 破折號/§ → 改純 ASCII；補 paddleseg 漏列相依 `pyyaml`/`visualdl`/`filelock`/`requests`（module-level import）
     - **numpy→native 正規化**：AI 回 np.int64/np.float64，`result_json`(JSONB) 走 json.dumps 不認 → engine 邊界 `_opt_int/_opt_float/_opt_point` 轉 native
     - **run_config 共用調參（Option A）**：engine `_build_bundle` 以 `run_config.build_bundle()` 為基底 + 強制 API-safe（LEGACY/viz-off/save_predictions-off）。工程師修好 run_config.py bug 後驗證通過
  3. **AI 整合介面瘦身決策（待決定 #15、Option 1）**：上游 `diaphragm_excursion` repo 加 `inference.py` facade + re-vendor；tuning 100% 上游 run_config。寫契約施工圖 `docs/ai_inference_contract.md`（git-track、已 /commit）交付上游 agent
- **踩雷摘要（避免重蹈）**：
  - **環境**：`.venv`(3.8.8) vs base anaconda 並存；裝套件 / 跑 server 要同一 python；`--reload` 不會因 pip 裝新套件而生效 → **裝套件後 server 必重啟**
  - **cp950 encoding**：pip 讀 requirements / pytest 讀 ini，Windows locale 用 Big5 解 UTF-8 中文會炸；對策 ASCII 化或 `PYTHONUTF8=1`
  - **整合 vendored 非 package**：AI/ 用 sys.path 絕對 import + `main` 撞名 → importlib hack（facade 落地後可消除）
- **下次 session 起手（Phase 3 facade）**：等上游交付 `inference.py` → re-vendor（trim viz/tools/experiments/font、相依實測能否砍 visualdl 等）→ engine 簡化（~250→十幾行）。詳 `docs/ai_inference_contract.md` §5/§6
- **commit 狀態**：4 個本地 commit 未 push（`f7f16de`/`22101af`/`e934025` + facade 契約）

---

### 2026-06-09 session 結尾狀態（AIResult schema/resolver + 後端分層整頓 + CLAUDE.md v1.3）

- **本次兩個任務（皆已 commit + push、工程師親自 /commit）**：
  1. **AIResult schema 對齊 + Measurement Type resolver**（commit `0961366`；generated docs `48d4662`；設計 `.work/ai_result_design.md`）：
     - `models/orm.py`：`Instance` +`device_manufacturer`/`device_model`；`AIResult` +`measurement_type`(server_default excursion)/`result_json`(JSONB↔SQLite JSON variant)/`primary_value`/`primary_unit`
     - `services/measurement_type.py`：`MeasurementType` enum + Resolver Protocol + `MachineModelResolver`(mapping 可注入、空 `MACHINE_MODEL_MAP`) + `ImageContentResolver` stub
     - Alembic `7f3c9a2b1d04`(additive)；upload 抽 device tag；+14 tests
     - **endpoint 仍 stub**（真實實作屬下游 task）；待決定 #13 已決、#14 仍開
  2. **後端模組分層整頓 relocate-only**（commit `dc0584c`）：config→`core/`、db→`db/session.py`、models→`models/orm.py`、db_service/storage/storage_backend→`services/`；`db/`+`models/` 用 `__init__` re-export → `from db/models import` 照舊；`main.py` 留 root(`uvicorn main:app` 不變)；git mv 保歷史；CLAUDE.md §6+§15.4+v1.3(工程師授權)；README/PROGRESS/IMPLEMENTATION/PLAN/HANDOFF 同步；66 tests 綠
- **工程師已 `alembic upgrade head`** → dev DB alembic_version = `7f3c9a2b1d04`（含新欄）
- **背景工作模式踩雷紀錄**：本 session 為 background job、harness 強制 worktree 隔離；worktree 無 `.venv`/`.env`、pre-commit hook 因 dubious-ownership 不觸發 → 需手動 regen / PATH 指 venv / cherry-pick -n 交 staged。**結論：互動式日常工作直接用前景 `claude`、勿用 worktree**（工程師已知悉）
- **殘留**：gitignored 空資料夾 `.claude/worktrees/reorg-layers/`、`.claude/worktrees/session-history/`（無害、可手動清）
- **下次 session 起手**：Phase 3 整合主線 — 待決定 #14(ai_service 執行模型) 起手前確認；先請工程師提供 `MACHINE_MODEL_MAP` 機型表

---

### 2026-06-06 session 結尾狀態（工程師回歸 + AI source vendoring 完工）

- **背景**：工程師空檔約 18 天、期間在另一專案完成 AI diaphragm excursion 核心演算法整合（peter88510/diaphragm_excursion repo），回 MedPACS 後表示「對專案陌生」、問下一步發展
- **本次主 Agent 工作**：
  - **Audit `./AI/`**：發現工程師預先 commit 的是 docs (11 個 .md untracked)、source code 在獨立 GitHub repo
  - **Design decisions (工程師裁示)**：
    - 整合架構：**Vendored 進 MedPACS repo**（不走 submodule / subprocess）
    - Vendored 範圍：source only、paddleseglibs/(27MB) + model weights gitignore
    - Python deps：拆 **requirements-ai.txt**
  - **執行 Vendoring (10 步)**：
    1. backup 既有 `./AI/` 到 `.work/AI-backup-before-vendoring/`
    2. `git clone --depth 1 https://github.com/peter88510/diaphragm_excursion` → `.work/`（48MB total / 21MB w/o paddleseglibs / 最新 commit `6139799` 2026-06-05）
    3. `cp -r .work/diaphragm_excursion ./AI/` + `rm -rf AI/.git`
    4. 既有 11 個 .md vs AI repo 對比：行數 0 差、md5 全異（LF/CRLF 差異、內容語意同）→ 安全覆蓋
    5. 更新 root `.gitignore` 加 `AI/` 排除段（paddleseglibs / *.pdparams / output / run_config.py / .idea 等）+ `.work/` 排除
    6. 建 root `requirements-ai.txt`（13 deps：paddlepaddle / pydicom / numpy / scipy / scikit-image / opencv-python / Pillow / PyWavelets / bresenham / matplotlib / natsort / imageio / imageio-ffmpeg）
    7. 更新 root `README.md` 加 §Step 7 「Optional: AI inference setup」章節（clone paddleseglibs / 取 model weights / pip install / smoke test）
    8. 更新 root `PROGRESS.md` §1 加 AI 整合段 + §5 Phase 3 task #11 [x] + Phase 3 schema 對齊待裁示 + §7 結構加 `AI/`
    9. 更新 `context/SESSION_HISTORY.md` A/B 段（系統現況 + 進行中 + 待決定 #13/#14 + 本記錄）
    10. cleanup `.work/`（即將）
- **Imports 抓出的外部 deps**（grep AI source）：pydicom / numpy / scipy.{ndimage, optimize, signal} / skimage.morphology / cv2 / PIL.{Image, ImageDraw, ImageFont} / pywt / bresenham / matplotlib.{Figure, FigureCanvasAgg} / natsort / imageio / paddlepaddle（vendored paddleseg 透過 paddleseglibs/）
- **3 個 design mismatch** 待 Phase 3 整合任務裁示（已記為待決定 #13 + #14；schema 對齊 / 執行模型 / 多 frame DICOM 單位處理）
- **新增檔案**：`AI/` (~150-250 files / ~21 MB)、`requirements-ai.txt`
- **修改檔案**：`.gitignore`、`README.md`、`PROGRESS.md`、`context/SESSION_HISTORY.md`
- **R3 Doc Impact**：本次 vendor 不動 main.py / models.py / alembic、pre-commit hook 不 trigger generators；HANDOFF 不需更新（前端目前不直接接觸 ai_results / AI source）
- **R1 跨節一致性**：PROGRESS §5 Phase 3 task #11 [x] ↔ §1 AI 整合段「Vendored 於 `./AI/`」— 一致 ✓
- **下次 session 主 Agent 起手**：依工程師指示「後續還是需要規劃整合 API」、進入 Phase 3 整合 task：① Schema 對齊裁示 (待決定 #13) ② ai_service.py wrapper 設計 ③ `/ai/segment/{id}` 真實實作 ④ `/ai/result/{id}/mask` viz PNG ⑤ 前端 AIPanel
- **commit 狀態**：vendor 改動 + 4 個文件同步待 commit；commit message 草稿 `feat: vendor AI/diaphragm_excursion source (snapshot @ 6139799)`

---

### 2026-05-19 session 結尾狀態（§6.13 init_db/alembic race condition 根治） — commit `0750dbc`

- **本次主 Agent 工作**：
  - **§6.13 根治**：`main.py:startup_event` 移除 `init_db()` 呼叫、改 print 「Schema managed by Alembic」訊息（方案 A、工程師授權）
  - **`db.init_db` function 保留**：供 emergency reset 手動 call、向後相容
  - **dev workflow 變動**：新 clone / fresh DB 啟動前須先跑 `alembic upgrade head`（既有 README Step 4 已要求此順序、本次只是真正落實）
  - **README.md `Integration Notes` 更新**：行為描述同步反映「no longer invoked at startup」+ 指向 PROGRESS §6.13
  - **conftest.py 不動**：test 走獨立 in-memory SQLite engine + `Base.metadata.create_all`、與 production DB 分離；不受影響
  - **52 test 全綠** — 確認 startup init_db() 移除對 test 無 regression
  - **文件同步**：
    - `PROGRESS.md` §1 init_db 行為註記改為「§6.13 根治」+ §6.13 標已解決
    - `README.md` Integration Notes 一行更新
    - `context/SESSION_HISTORY.md` A 段系統現況 / 進行中 / 待決定 (#10 / #11 已決) + B 段本記錄
- **修改檔案**：`main.py` (startup_event body)、`README.md` (Integration Notes 一行)、`PROGRESS.md`、`context/SESSION_HISTORY.md`
- **R3 Doc Impact**：main.py startup_event body 變動 → pre-commit hook 會 regen api_spec.md（startup_event 不在 API route 範圍、generator 預期不改 visible 內容、僅可能 line shift）
- **R1 跨節一致性**：§6.13 標已解決 ↔ §1 init_db 註記「§6.13 根治」— 一致 ✓
- **README 評估**：✅ 已更新（dev workflow 變動屬「使用者可見啟動指引」、CLAUDE.md §8 v1.1 規範符合）
- **下次 session 主 Agent 起手**：問工程師決定下一步（待決定 #10 剩餘候選：PLAN §14 sample DICOM / §6.3 logging / production 準備；§6.14 / §6.4 屬中後期）
- **commit 狀態**：4 個檔變動待 commit；commit message 草稿 `fix(api): §6.13 拿掉 startup init_db() — alembic 獨享 schema canonical 路徑`

---

### 2026-05-19 session 中段（§6.12 Upload duplicate detection 完工） — commit `e8d4250`

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
