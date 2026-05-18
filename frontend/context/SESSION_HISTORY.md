# frontend/context/SESSION_HISTORY.md — 前端 Agent 工作記憶

> **文件定位**：本檔是**前端 Agent 自己**維護的跨 session 工作記憶。讓「下次 session 起手能無縫接續」。
>
> 與 `PROGRESS.md` 互補：PROGRESS 是進度追蹤（事實清單）、本檔是當下脈絡記憶（前端視角的 mental state）。
>
> **誰維護**：前端 Agent。主 Agent 可讀不可寫（除非緊急修正過時資訊或結構性重組，需在 commit message 說明）。
>
> **更新規則**：見 `frontend/CLAUDE.md` §9。
>
> **結構說明（2026-05-14 起）**：
> - **A 段（系統現況快照）**：當前狀態、in-flight 任務、待決定事項 — 每次 session 必讀
> - **B 段（工作脈絡）**：里程碑歷史、上次 session 結尾狀態 — 按需查閱、需要回顧時才讀

---

## A. 系統現況快照（必讀，每次 session 啟動）

### 系統現況（2026-05-18）

- **架構**：React 19.2 + Vite 8.0 + TypeScript 6.0；單頁 SPA；CSS Modules；React Context state；no Redux/UI framework。
- **目錄結構**（task #9 完成後）：
  ```
  frontend/
  ├── .env.example                       ← VITE_API_BASE_URL=http://localhost:8000
  ├── public/
  │   └── favicon.svg                    ← 唯一保留的 Vite scaffold
  └── src/
      ├── main.tsx                       ← await initCornerstone() 才 render
      ├── App.tsx                        ← <AppContextProvider><Layout>...</></...>
      ├── index.css                      ← html/body/#root 100%×100% (Fix-J 一部分)
      ├── api/                           ← task #9 commit 1
      │   ├── client.ts                  ← fetch wrapper + ApiError + base URL env var
      │   ├── types.ts                   ← Study / Series / Instance / AI*
      │   ├── studies.ts / series.ts / instances.ts / ai.ts
      ├── context/
      │   └── AppContext.tsx             ← 5 fields + Provider + useAppContext() + cascade
      ├── cornerstone/
      │   └── setup.ts                   ← initCornerstone() idempotent
      └── components/
          ├── Layout/                    ← CSS Grid 三欄
          ├── TopBar/                    ← MedPACS title + selection debug
          ├── StudyList/                 ← 三層 toggle 展開（commit 8 加 toggle）
          ├── DicomViewer/               ← useAppContext().currentInstanceId；Fix-4 destroy+recreate
          ├── MetadataPanel/             ← idle/loading/ok/error 四態
          └── AIPanel/                   ← Run AI + stub JSON (mask overlay 留 Phase 3)
  ```
- **dev server**：`npm run dev` → `http://localhost:5173`；task #9 期間用 user 自己的 dev server (PID 32648)；前端 Agent 沒另開、收尾不 TaskStop（屬 user 所有）。
- **已裝套件**：`@cornerstonejs/core@4.22.6` + `dicom-image-loader@4.22.6` + `tools@4.22.6`、`dicom-parser@1.8.21`、React 19.2、TypeScript 6.0；**task #9 沒引入任何新 npm 依賴**（fetch + React Context，無 Redux/UI framework）。
- **目前可做到的事（task #9 完整 SPA 已 end-to-end 驗收 ✅）**：
  - Layout 三欄 + TopBar 渲染正確（深色主題）
  - AppContext cascade 自動選 study → series → instance；StudyList 可手動 toggle expand/collapse + ▶▼ icon
  - DicomViewer **影像在中央區顯示**（user 驗收回報「ok 在中央區顯示」— **Fix-J 看似有效**，不過 user 未明示「完全填滿」、保留 §4.4 為「待主 Agent 最終確認」狀態）
  - MetadataPanel 四態 + key-value 顯示
  - AIPanel Run AI → stub JSON 顯示（mask overlay 留 Phase 3）
  - `VITE_API_BASE_URL` env var fallback `http://localhost:8000` 生效

### 進行中的任務

> **無進行中任務**。task #9 已 commit `fb656c6` → 本 commit（9 commits + 1 hash 回填）；StudyList toggle 行為已補 (commit 8)；後端 audit 已寫進 PROGRESS §5.4 待主 Agent 處理。**等主 Agent 下個 dispatch**（預期 Phase 3 真實 AI + mask overlay、或 Stage C UX 缺口最終收尾 + 後端 §5.4 audit 處理）。

### 待決定事項

- **後端 §5.4 audit findings 處理**：主 Agent 看完 PROGRESS §5.4 後決定（推薦方向 (a) backfill script 解決 pre-2026-05-15 orphan instances 1/3/4；以及 (c) instance ID gap 來源澄清）
- **Stage C UX 缺口最終狀態**：Fix-J 看似有效（user 驗收「ok」），但未完全用 §4.4 「已解決於 commit XXX」標記 — 因 user 用「ok 在中央區顯示」字眼、未明示「完全填滿」；保留 §4.4 為「待主 Agent 最終確認」
- **Multi-frame 處理 / cine 播放**：Phase 3 範圍
- **`vite.config.ts` 何時要動**：task #9 期間皆未需動；下個 dispatch 若遇問題，debug 順序不變

---

## B. 工作脈絡（按需查閱）

### 已完成里程碑

> 精選大事（非全部完成項目；全表參見 `PROGRESS.md` §1）。

- **Phase 2 task #7（2026-05-13, `2d055de`）** — React + Vite + TS 專案骨架
- **Phase 2 task #8 Stage A（2026-05-13, `83b8c9a`）** — 安裝 4 個 Cornerstone 套件、Vite pre-bundle 驗證
- **Phase 2 task #8 Stage B（2026-05-14, `8cd61f3`）** — `setup.ts` + `main.tsx` 改造完成，dev server 端驗證乾淨
- **文件架構重組 Phase 1-4（2026-05-14, `5f8acae` → `08ee711`）** — 主 Agent 主導；前端側影響：`frontend/context/` + `frontend/docs/` 分層、SESSION_HISTORY 拆 A/B 段、CLAUDE.md v1.1（加 §6.5 觸發式 Archive 與 §9.7 Stale Warning）
- **Phase 2 task #8 Stage C — 瀏覽器驗收通過（2026-05-15，commit 待回填）** — `DicomViewer.tsx` + `DicomViewer.module.css` 新增、`App.tsx` 改寫 hardcoded `INSTANCE_ID`；dev server 兩次 boot 皆乾淨；瀏覽器以 `INSTANCE_ID=1`（`Peter_Quiet_1.dcm`）成功渲染 DICOM。⚠️ **影像尺寸不完整** — 見 PROGRESS §4.4 follow-up
- **Stage C fit dispatch `phase-2-task-8-stage-c-fit` — gate 失敗（2026-05-15，未 commit）** — 加 `viewport.resetCamera()` + `aspect-ratio: 4/3`，dev server 端 tsc + HTTP 全通過；但瀏覽器仍見「完整超音波影像未在正確視窗框」。依 DISPATCH §「具體工作」4 停下、寫 §4.4 Fix-1 結果、待主 Agent 派新 dispatch（推薦方向 B：metadata-aware 動態 aspect-ratio）
- **Stage C metadata dispatch `phase-2-task-8-stage-c-metadata` — gate 失敗（2026-05-16，未 commit）** — 加 `cornerstone.metaData.get('imagePlaneModule', imageId)` 動態取 rows/columns、設 container aspect-ratio、rAF 等 layout、`renderingEngine.resize` + `resetCameraForResize` + `render`。Container 與 canvas 兩者 aspect ratio 都對齊到 1640/1990，但 image actor 在 VTK scene 仍縮在角落（80% → 60% 黑底）。根因：Cornerstone 4.x GPU 模式底層 VTK actor 的 scene-space scale 在 setStack 時鎖定、後續 camera reset 動不到 actor scale。依 DISPATCH §「禁止」4 停下、寫 §4.4 Fix-2 詳記、待主 Agent 派新 dispatch（推薦方向 E：重 setStack）
- **Stage C restack dispatch `phase-2-task-8-stage-c-restack` — gate 失敗（2026-05-16，未 commit）** — 在 metadata + rAF + resize 之後加二次 `await viewport.setStack([imageId])`。Network 0 GET（cache hit ✓）、Console 0 warning（metadata 主路成功 ✓）、setStack #2 確實執行；但影像仍未撐滿 canvas。Cornerstone source 分析：second setStack 確實走 full rebuild（stackInvalidated=true 強制）建新 actor + resetCameraNoEvent — 仍未填滿 → **Cornerstone 內部還有更深狀態綁在 enableElement 當下的 canvas 尺寸**（VTK offscreen render window / camera intrinsic 等）。依 DISPATCH §「主 Agent 已拍板的決策」5 停下、寫 §4.4 Fix-3 詳記、待主 Agent 派新 dispatch（推薦新方向 I：destroy+recreate engine）
- **Stage C 完整版含 UX 缺口（2026-05-16, `13cccd3`）** — 主體 + Fix-1 (fit) + Fix-2 (metadata) + Fix-3 (restack) + Fix-4 (destroy+recreate engine) 全部 4 次嘗試已 commit；功能可用、影像未撐滿 container 的 UX 缺口未解，等主 Agent 拍板方向 J（CSS 層偵錯）或 H（暫退）
- **Phase 2 task #9 — 業務元件層完工（2026-05-16 → 2026-05-18，commits `fb656c6` → 本 commit）** — 9 個 commit (含 commit 0 固化 codex Fix-J 嘗試) 完成 API client + VITE_API_BASE_URL env var 制度 + AppContext (5 fields) + Layout/TopBar/StudyList/MetadataPanel/AIPanel 全部業務元件 + DicomViewer ← AppContext + Vite scaffold 清掉。E2E 瀏覽器驗收通過（Layout、cascade、DICOM viewer、metadata、AI、env var fallback 全 ✅）。StudyList toggle 行為已補 (commit 8)。後端 audit 完成、寫進 PROGRESS §5.4 待主 Agent 處理 (orphan instances 1/3/4 + instance ID gap 來源澄清)

### 上次 session 結尾狀態（2026-05-18）

- **task #9 完成跨 session 工作 — 9 commits 全 push 完畢**：
  - Commit 0 `fb656c6` 固化 codex 移除 outer div aspectRatio（Fix-J 根因之一）
  - Commit 1 `e4fd960` API client + .env.example + VITE_API_BASE_URL 制度
  - Commit 2 `2e1d9fb` AppContext (5 fields + cascade)
  - Commit 3 `ea3cc1b` Layout + TopBar (CSS Grid 三欄 + 深色)
  - Commit 4 `fec64f5` StudyList 三層
  - Commit 5 `7c8fe0b` MetadataPanel
  - Commit 6 `d66b6ab` AIPanel
  - Commit 7 `40d766d` DicomViewer ← AppContext + App.tsx 改寫 + Vite scaffold 清掉 + Fix-J 嘗試
  - Commit 8 `4a016cd` StudyList toggle + ▶▼ icon（user 驗收回報補強）
  - Commit 9（本 commit）PROGRESS §1/§2/§3 + §5.4 後端 audit + SESSION_HISTORY 同步
- **驗證歷程**：
  - 每個 commit 後 tsc 通過、push 到 `origin/master`
  - End-to-end 瀏覽器驗收（user 報告）：Layout / cascade auto-select / DicomViewer 顯示 / MetadataPanel / AIPanel Run AI / VITE_API_BASE_URL fallback **全 ✅**
  - **Fix-J 看似有效**：user「ok 在中央區顯示」(commit 0 移除 outer div aspectRatio + commit 7 codex CSS `html/body/#root 100%` + `.viewer/.viewport` wrapper 結構)；未 100% 確認「完全填滿」、保留 §4.4 為「待主 Agent 最終確認」
  - StudyList toggle (commit 8) 是 user 驗收回報後補強
- **本 session 兩個重要技術 finding**：
  1. **TypeScript 6 `erasableSyntaxOnly`** 禁用 constructor parameter properties — `client.ts:ApiError` 必須用顯式 field declaration 才能編譯
  2. **Vite scaffold `#root max-width: 1126px`** 是 Fix-J 根因之一 — codex 已先排查、改為 `width: 100%; height: 100%`（commit 7 採納）
- **後端 audit 重要發現（PROGRESS §5.4 詳記）**：
  - 8 個 instances，id=1/3/4 是 pre-2026-05-15 orphan (series_instance_uid=NULL)、id=6-10 正確 link
  - Instance ID gap (2/5/11+) 來源待澄清
  - Upload pipeline idempotency + grouping 都正確
  - 建議方向 (a) backfill script 解決 legacy orphan、(c) ID gap 來源澄清
- **commit 狀態**：9 個 commits 已 push、工作樹乾淨
- **背景任務**：user 自己的 dev server (PID 32648) 仍在跑、不關（屬 user）
- **下次起手建議**：
  1. 等主 Agent 看 PROGRESS §5.4 audit findings + 給新 dispatch（推薦 Phase 3 真實 AI + mask、或先處理 §5.4 backend backfill）
  2. Stage C UX 缺口 §4.4：user 驗收「ok」但未明示「完全填滿」、保留待主 Agent 最終確認
  3. 後續若 DICOM 填滿仍有問題、再考慮方向 F/K/L (ResizeObserver / DOM 簡化 / 換 viewport type)

---

## 文件維護

| 項目 | 說明 |
|---|---|
| 文件版本 | v1.1（2026-05-14 由主 Agent 做結構性重組為 A/B 兩段，內容未動） |
| 建立日期 | 2026-05-14（v1.0 由前端 Agent 寫於 Stage B 收尾） |
| 維護者 | 前端 Agent（內容）；主 Agent 在結構升級時例外動 |
| 更新時機 | 每次 session 結尾、完成 dispatch 任務後 |
| 主 Agent 行為 | 可讀；原則上不寫；例外：結構性重組 / 緊急修正過時資訊，需在 commit message 說明 |
