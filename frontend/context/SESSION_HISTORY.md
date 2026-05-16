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

### 系統現況（2026-05-15）

- **架構**：React 19.2 + Vite 8.0 + TypeScript 6.0；單頁 SPA。
- **目錄結構**：
  ```
  frontend/src/
  ├── main.tsx                                  ← 程式入口，啟動時 await initCornerstone() 才 render
  ├── App.tsx                                   ← 已改寫；hardcoded INSTANCE_ID + render <DicomViewer />
  ├── App.css / index.css                       ← App.css 不再 import（Vite scaffold 殘留，暫不刪）
  ├── assets/                                   ← Vite scaffold 圖片（暫不刪）
  ├── cornerstone/
  │   └── setup.ts                              ← initCornerstone() — idempotent module-level singleton
  └── components/
      └── DicomViewer/
          ├── DicomViewer.tsx                   ← Stage C；props instanceId、wadouri、StrictMode-safe
          └── DicomViewer.module.css            ← 黑底 + 100%×600px
  ```
- **dev server**：`npm run dev` → `http://localhost:5173`；metadata dispatch 期間 restart 299ms；**目前仍在跑（task `bp155c6gs`）** — 主 Agent 若快速 iterate 新 dispatch 可省一次冷啟動，否則前端 Agent 收尾前 TaskStop
- **已裝套件**：`@cornerstonejs/core@4.22.6`、`@cornerstonejs/dicom-image-loader@4.22.6`、`@cornerstonejs/tools@4.22.6`、`dicom-parser@1.8.21`、React 19.2、TypeScript 6.0。
- **目前可做到的事**：DICOM 渲染成功（`INSTANCE_ID=1`，`Peter_Quiet_1.dcm`，1640×1990 portrait 大尺寸超音波）；container aspect-ratio 已動態對齊 1640/1990；metadata 主路成功；無 console error；StrictMode-safe；cache hit 行為正確；**但影像仍未撐滿 container** — Fix-1/2/3/4 全部試過，皆未完整解。Fix-4 是「destroy+recreate engine」最徹底解仍失敗 → 根因可能比 Cornerstone API 層更深（CSS layout / Cornerstone module-level state）。**Stage C 已 commit 含 UX 缺口、等主 Agent 下一步**。PROGRESS §4.4 Fix-4 + 整體狀況彙整子段已詳記。

### 進行中的任務

> **無進行中任務**。工程師授權的 Fix-4 方向 I（destroy+recreate engine）也失敗 → 影像填滿問題比預期深。工程師決定 commit 現狀、等主 Agent 下一步指示。**Stage C 5 個檔（DicomViewer.tsx, .module.css, App.tsx, PROGRESS.md, SESSION_HISTORY.md）已 commit 完整版含 UX 缺口**；commit hash 待回填。

### 待決定事項

- **Stage C 尺寸缺口處理方向（4 次嘗試後）**：主 Agent 從 PROGRESS §4.4「Stage C 尺寸缺口 — 整體狀況彙整」給的 J/H/F/K/L 五方向擇一（前端 Agent 強推 **方向 J — CSS 層級偵錯**：拿掉所有 Cornerstone 假設、直接用瀏覽器 Computed style 看 `.viewport` / `.viewport-element` / `canvas` 三層真實尺寸，可能 root cause 在 Vite scaffold `#root` CSS 限制或 `min-height: 400px` 與動態 aspect-ratio 衝突；或 **方向 H — 暫退、留 task #9 順手處理**也務實）— 需新 dispatch 才能執行
- **Multi-frame 處理**：工程師提出「多張 frame vs 單張 frame 會有不同尺寸」— 屬下個 dispatch 範圍；本任務仍僅需顯示第一 frame，cine 播放 / frame slider 屬 task #9 或 Phase 3
- **`vite.config.ts` 何時要動**：本次 Stage C 四次嘗試**皆未需動**（無 wasm/worker/cors 邊界錯）；下個 dispatch 若遇問題，debug 順序仍是 `optimizeDeps.exclude` → `worker.format='es'` → `assetsInclude` → 最後才考慮版本鎖
- **Vite scaffold 殘留清理**：`App.css`、`assets/`、`public/icons.svg`、`public/vite.svg` 在 Stage C 改寫後已不再被 import — 方向 J 偵錯時可能需要動 `#root` CSS，那時可一併清理（兩者相關）

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

### 上次 session 結尾狀態（2026-05-16）

- **跨 session 累積改了什麼（皆未 commit）**：
  - **Stage C 主體**（`phase-2-task-8-stage-c`）：DicomViewer.tsx 新增、.module.css 新增、App.tsx 改寫
  - **Stage C fit dispatch**（`phase-2-task-8-stage-c-fit`，gate 失敗）：DicomViewer.tsx async IIFE + resetCamera、.module.css `height: 600px` → `aspect-ratio: 4/3; min-height: 400px`
  - **Stage C metadata dispatch**（`phase-2-task-8-stage-c-metadata`，gate 失敗）：DicomViewer.tsx 加 `import { metaData }`、metadata 主路 + 備路 + warning fallback、`element.style.aspectRatio` 動態設定、rAF 等 layout、`renderingEngine.resize(true, false)`、`viewport.resetCameraForResize()`；.module.css 加註解說明 CSS aspect-ratio 為 fallback-only
  - **doc**：PROGRESS §1 加 Stage C 條目 + §2 / §3 整理 + §4.4 加 + §4.5 加 + §4.4 Fix-1 + §4.4 Fix-2 子段加；SESSION_HISTORY A/B 兩段多次同步
  - **未動**：`vite.config.ts`、`main.tsx`、`cornerstone/setup.ts`、backend 任何檔、IMPLEMENTATION.md、Vite scaffold 殘留
- **驗證歷程總結**：
  - Stage C 主體：瀏覽器渲染 ✅ — **但影像尺寸不完整**（image 縮邊）
  - Stage C fit (4/3)：dev server 端 ✅、瀏覽器 gate ❌（image 在 4/3 container 內被切）
  - Stage C metadata + rAF + resetCameraForResize：dev server 端 ✅、container & canvas aspect ratio 對齊 1640/1990 ✅、但 image 仍在 canvas 內縮邊（80% → 60% 黑底，部分改善但 gate ❌）
- **本 session 兩個關鍵技術發現**（PROGRESS §4.4 Fix-2 詳記）：
  1. **timing 問題**：JS 改 `element.style.aspectRatio` 後，瀏覽器尚未 layout reflow，立即呼叫 `renderingEngine.resize(true, false)` 會 measure 到舊尺寸 → canvas buffer 卡舊值。對策：**rAF 等 layout 完才呼叫 resize**
  2. **`resetCameraForResize()` 在 GPU 模式 = `resetCamera()`**：Cornerstone 4.x `StackViewport.js:414-425` 的 dispatcher 只讀 `resetPan` + `resetZoom`，**完全忽略 `resetToCenter`/`suppressEvents`**。且 `renderingEngine.resize()` 內部已自動呼叫 resetCameraForResize（`ContextPoolRenderingEngine.js:169`），所以外層手動再呼叫是 no-op
  - **真正未解的問題**：Cornerstone GPU 用 VTK actors+camera 架構；`setStack` 當下 image actor 在 VTK scene 的 scene-space scale 被鎖定在「當時 canvas 尺寸」；後續 resize+resetCameraForResize 只重設 camera view、**動不到 actor scale** → image 仍以舊大小 fit 入新 canvas → 縮在角落
- **debug 過程踩到的非 code 坑**（PROGRESS §4.5）：CORS 5174→8000、`vite server` zombie 404、`instance_id=2` 後端不存在、靜態 4/3 不適用變動 DICOM、Cornerstone VTK actor scale 鎖定
- **commit 狀態**：**完全未 commit**（三份 dispatch 累積在工作樹）。`git status` 應該見：
  - M PROGRESS.md
  - M context/SESSION_HISTORY.md
  - M src/App.tsx
  - M src/components/DicomViewer/DicomViewer.tsx
  - M src/components/DicomViewer/DicomViewer.module.css
  - ?? src/components/（首次新增）
- **背景任務**：dev server `bp155c6gs` **仍在跑**（沒 TaskStop） — 主 Agent 若快速 iterate 新 dispatch 可省冷啟動；若不快速 iterate、前端 Agent 應在 session 結尾前 TaskStop 避免 zombie 5173
- **下次起手建議**：
  1. **等主 Agent 看 §4.4 「整體狀況彙整」段（含 J/H/F/K/L 五方向選項）+ 給新 dispatch**（前端 Agent 強推 **方向 J — CSS 層級偵錯**：拿掉所有 Cornerstone 假設、用瀏覽器 Computed style 對照 `.viewport`/`.viewport-element`/`canvas` 三層真實尺寸；可能 root cause 在 `#root` Vite scaffold CSS 限制 max-width / padding、或 `min-height: 400px` 與動態 aspect-ratio 衝突。次選 **方向 H — 暫退**：把完整 fit 留到 task #9）
  2. Stage C 5 個檔已 commit (`13cccd3`) 含 UX 缺口（image 未撐滿）
  3. 不要再自行擴 scope 試方向 K/L（DOM 簡化 / 換 viewport type）；那些是重構級工作，需主 Agent 拍板

---

## 文件維護

| 項目 | 說明 |
|---|---|
| 文件版本 | v1.1（2026-05-14 由主 Agent 做結構性重組為 A/B 兩段，內容未動） |
| 建立日期 | 2026-05-14（v1.0 由前端 Agent 寫於 Stage B 收尾） |
| 維護者 | 前端 Agent（內容）；主 Agent 在結構升級時例外動 |
| 更新時機 | 每次 session 結尾、完成 dispatch 任務後 |
| 主 Agent 行為 | 可讀；原則上不寫；例外：結構性重組 / 緊急修正過時資訊，需在 commit message 說明 |
