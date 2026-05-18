# frontend/PROGRESS.md — 前端工作進度

> **文件定位**：本檔僅記錄前端的**狀態與進度**。
>
> 架構說明見 [`IMPLEMENTATION.md`](./docs/IMPLEMENTATION.md)；操作教學見 [`README.md`](./README.md)；AI 行為約束見 [`CLAUDE.md`](./CLAUDE.md)。
>
> **更新規則**：每完成一項任務、變更狀態、或回報新需求時，由前端 Agent 同步更新本檔（規則見 [`CLAUDE.md`](./CLAUDE.md) §6）。

---

## 目錄

1. [已完成任務](#1-已完成任務)
2. [進行中](#2-進行中)
3. [待辦](#3-待辦)
4. [已知缺口](#4-已知缺口)
5. [後端需求清單](#5-後端需求清單)
6. [文件維護](#6-文件維護)

---

## 1. 已完成任務

> 累積所有歷史里程碑。已廢棄項目應標註「已廢棄 — 原因」，不可刪除。

### Phase 2 — Frontend Viewer

- [x] **Phase 2 task #7：React + Vite + TypeScript 專案骨架**（2026-05-13，commit `2d055de`）
  - `npm create vite@latest frontend -- --template react-ts` 產出 React 19 + TS 6 + Vite 8
  - 153 個 npm 套件安裝完成
  - dev server 啟動 ~440ms，`http://localhost:5173` 正常回應
  - 取代 Vite 預設 README 為中文版專案文件
- [x] **Phase 2 task #8 Stage A：Cornerstone3D 套件安裝**（2026-05-13，commit `83b8c9a`）
  - `@cornerstonejs/core@4.22.6`
  - `@cornerstonejs/dicom-image-loader@4.22.6`
  - `@cornerstonejs/tools@4.22.6`
  - `dicom-parser@1.8.21`
  - Vite pre-bundle 驗證通過、App.tsx smoke test 撤回
  - 已知：6 個 moderate vulnerabilities（transitive deps，需 Cornerstone 上游升級才能消除）
- [x] **Phase 2 task #8 Stage B：CornerstoneJS 初始化設定**（2026-05-14，commit `8cd61f3`）
  - 新增 `src/cornerstone/setup.ts` — export idempotent `initCornerstone()`；以 `initialized` flag + 並發保護的 `initPromise` 確保多次呼叫只實際 init 一次
  - 修改 `src/main.tsx` — 新增 `bootstrap()` async 函數，render 前 `await initCornerstone()`；包 `.catch()` 防止 unhandled promise rejection
  - `vite.config.ts` **未動**（Vite pre-bundle 自動處理 `@cornerstonejs/dicom-image-loader`，無 esbuild 衝突）
  - 驗證：`npm run dev` 啟動 329ms，無 error / warning；curl /、/src/main.tsx、/src/cornerstone/setup.ts 皆回 HTTP 200；Vite log 顯示 dicom-image-loader 成功 optimize
  - 瀏覽器 DevTools console 驗證**待工程師於瀏覽器確認**（Agent 無法存取瀏覽器）
- [x] **Phase 2 task #9：業務元件層**（2026-05-16 → 2026-05-18，9 commits + 1 hash 回填）
  - Commit 0 `fb656c6` — 固化 codex 移除 outer div aspectRatio 設定（Fix-J 根因之一）
  - Commit 1 `e4fd960` — API client (`src/api/`) + `VITE_API_BASE_URL` env var 制度
  - Commit 2 `2e1d9fb` — AppContext（5 fields + Provider + `useAppContext()` hook + cascade auto-select）
  - Commit 3 `ea3cc1b` — Layout + TopBar 結構元件（CSS Grid 三欄 + 深色主題）
  - Commit 4 `fec64f5` — StudyList 三層展開
  - Commit 5 `7c8fe0b` — MetadataPanel（idle/loading/ok/error 四態）
  - Commit 6 `d66b6ab` — AIPanel（Run AI 按鈕 + stub JSON 顯示；mask overlay 留 Phase 3）
  - Commit 7 `40d766d` — DicomViewer ← AppContext + App.tsx 改寫（AppContextProvider+Layout）+ Vite scaffold 清掉（App.css/assets/public/*.svg）+ CSS Modules 整理 + Fix-J 嘗試
  - Commit 8 `4a016cd` — StudyList toggle + ▶▼ icon（驗收回報補強）
  - Commit 9 `498a845` — PROGRESS §1/§2/§3 finalize + §5.4 後端 audit findings + SESSION_HISTORY 同步
  - Commit 10（hash 回填，本 commit）— 把 commit 9 自身 hash 填回 §1 條目（沿用 Stage B `8cd61f3` + `acd2ced` 兩 commit pattern）
  - 驗收狀態：Layout / Cascade auto-select / DicomViewer / MetadataPanel / AIPanel / VITE_API_BASE_URL fallback 全 ✅；**Fix-J 看似有效**（DICOM viewer 在中央區渲染、user 驗收「ok 在中央區顯示」）
  - 已知 UX nuance：StudyList 只看到 5 個 instances（id 6-10），orphan instances (id 1, 3, 4) 透過 series tree 不可見 → 詳 §5.4 backend audit

- [x] **Phase 2 task #8 Stage C：第一張 DICOM 渲染**（2026-05-15 → 2026-05-16，commit `13cccd3`，含 UX 缺口）
  - 主體（2026-05-15）：
    - 新增 `src/components/DicomViewer/DicomViewer.tsx` — props `instanceId: number`、`useRef<HTMLDivElement>` 容器、`useEffect` 內建 `RenderingEngine` + `StackViewport`、`wadouri:http://localhost:8000/instances/${id}/file`、cleanup `destroy()` + `cancelled` flag 防 StrictMode race
    - 新增 `src/components/DicomViewer/DicomViewer.module.css` — `width: 100%; min-height: 400px; aspect-ratio: 4/3` CSS fallback + 黑底
    - 改寫 `src/App.tsx`（123 → 10 行）— 取代 Vite scaffold、`const INSTANCE_ID = 1`、render `<DicomViewer instanceId={INSTANCE_ID} />`
  - 累積演進（Fix-1 ~ Fix-4，2026-05-15 至 2026-05-16）：
    - **Fix-1** fit dispatch：加 `viewport.resetCamera()` + 靜態 aspect-ratio 4/3 → gate 失敗（§4.4 Fix-1）
    - **Fix-2** metadata dispatch：加 `cornerstone.metaData.get('imagePlaneModule')` 動態取 rows/columns + rAF + `resetCameraForResize` → 部分改善但 gate 失敗（§4.4 Fix-2）
    - **Fix-3** restack dispatch：再加二次 `await setStack` → gate 失敗（§4.4 Fix-3）
    - **Fix-4** 工程師授權方向 I：destroy+recreate engine 兩階段 → gate 失敗（§4.4 Fix-4）
  - `vite.config.ts` **未動**（dev server 端 Cornerstone pre-bundle 無 esbuild / wasm / worker 衝突）
  - dev server 驗證每次皆 ✅：tsc 通過、`npm run dev` 啟動乾淨、所有 HTTP probe 200
  - 瀏覽器驗收：以 `INSTANCE_ID=1`（`Peter_Quiet_1.dcm`，1640×1990 portrait US）功能 ✅（DICOM 顯示、metadata 主路成功、無 console error、cache hit 正確）；**UX 缺口 ❌：影像未撐滿 container**（從 80% 黑底改善到 60% 黑底後停滯）
  - 4 次嘗試後仍未解 → 根因可能在 CSS layout 層或 Cornerstone GPU+VTK module-level state；待主 Agent 拍板方向 J（CSS 層偵錯）或 H（暫退、留 task #9）— 詳 §4.4「整體狀況彙整」

### 文件

- [x] **`frontend/README.md`** — 新手向中文啟動指引、目錄結構解析、名詞速查表（commit `2d055de`）
- [x] **`frontend/IMPLEMENTATION.md`** — 元件樹、Context、API client、Cornerstone Stage A/B/C 計畫（commit `bd42ec9`）
- [x] **`frontend/CLAUDE.md`** — 前端 AI 操作規範（2026-05-13）
- [x] **`frontend/PROGRESS.md`** — 本檔（2026-05-13）

---

## 2. 進行中

> **目前無進行中項目。** task #9 已完成（commits `fb656c6` → 本 commit）；等主 Agent 派下個 dispatch（預期 Phase 3：真實 AI 推論 + mask overlay，或 Stage C UX 缺口最終收尾 + 後端 §5.4 audit 處理）。

---

## 3. 待辦

> 順序見 [`IMPLEMENTATION.md`](./docs/IMPLEMENTATION.md) §10「開發順序建議」。

### Phase 3 — AI 推論 + Mask Overlay (預告)

- [ ] **Backend**：`AIResult` model + Alembic migration + `ai_service.py` + PyTorch 模型載入
- [ ] **Backend**：`POST /ai/segment/{id}` 真實實作（取代 stub queued）
- [ ] **Backend**：`GET /ai/result/{id}/mask` 真 PNG endpoint（取代 stub_mask_data 字串）
- [ ] **Frontend**：AIPanel mask overlay 真渲染（取代目前的 stub JSON 顯示）
- [ ] **Frontend**：可能順手收尾 Stage C UX 缺口（若 Fix-J 結果不完美）

### Phase 4 — Demo 演練 (PLAN §13)

- [ ] sample DICOM 準備
- [ ] end-to-end demo 演練

---

## 4. 已知缺口

> 「知道有缺、但目前無法解決或未排入計畫」的項目。

### 4.1 後端 API 不足以支援前端需求

詳見 §5「後端需求清單」。本節保留追蹤前端視角的影響：

- **無法依 study 取得 series 清單** → StudyList 切換 study 時無法自動列出 series → 暫時 hack：fetch 所有 instances 後用 `study_instance_uid` 過濾
- **AI mask endpoint 不確定是否真實實作** → AIPanel mask overlay 渲染卡關

### 4.2 前端工具鏈

- **無 frontend 測試套件** — 尚未導入 Vitest / React Testing Library / Playwright，目前所有驗證靠手動 + 瀏覽器
- **無 E2E 測試** — Phase 4 demo 流程能否在前後端整合下穩定運作，仍是未知
- **無 lint pre-commit hook** — 程式碼風格仰賴 IDE + 手動 `npm run lint`

### 4.3 待主 Agent 決定的設計規範

詳見 [`CLAUDE.md`](./CLAUDE.md) §9：UI/UX 規範、瀏覽器相容性、效能、無障礙、錯誤呈現、i18n、測試。**前端 Agent 不自行決策**，等主 Agent 補上規範後再回頭處理。

### 4.4 DicomViewer 影像尺寸不完整（Stage C 驗收發現，2026-05-15）

> ✅ **已解決於 commit `40d766d` (Fix-J)**（2026-05-18 工程師裁示）。task #9 commit 7 內 codex 找到並修掉根因：① outer div `aspectRatio` 移除（commit 0 `fb656c6` 固化） ② Vite scaffold `#root max-width: 1126px` 改 `width:100% height:100%` ③ `html/body/#root` 100% chain + `.viewer/.viewport` wrapper 結構。user 驗收回報「ok 在中央區顯示」。Fix-1~Fix-4 詳細失敗紀錄保留以供未來 Cornerstone 整合除錯參考；不再追蹤。

- **症狀**：DICOM 成功載入並渲染，但影像被切掉一部分 — viewport 內看不到完整影像
- **可能原因**（未深查）：
  - Cornerstone StackViewport 預設無 fit-to-window 行為；未在 `setStack().then()` 後呼叫 `viewport.resetCamera()` 或設 `viewport.setProperties({ ...VOI/zoom })`
  - DicomViewer.module.css 容器固定 `height: 600px` — 與影像長寬比不匹配時會有黑邊或裁切
  - 影像實際長寬未從 DICOM metadata 取出來反映到 canvas 比例
- **影響**：功能性驗收通過（能看到 DICOM）；但 UX 不完整
- **建議下一步**（待主 Agent 決定範圍）：① 在 `setStack` 之後加 `viewport.resetCamera()` 試試 ② 容器改 aspect-ratio 自適應 ③ 等 Phase 2 task #9 期間順手處理（屬「CSS Modules 樣式整理」的延伸）

#### Fix-1 嘗試結果（dispatch `phase-2-task-8-stage-c-fit`，2026-05-15）

主 Agent 派 fit dispatch 採方案 ①+②：

- **手法**：
  - `DicomViewer.tsx`：把 `viewport.setStack([imageId]).then(viewport.render)` 改為 `async IIFE { await setStack; resetCamera; render }`，保留 `cancelled` flag 與 cleanup `destroy()`
  - `DicomViewer.module.css`：`width: 100%; height: 600px;` → `width: 100%; aspect-ratio: 4/3; min-height: 400px;`
- **dev server 端驗證**：tsc 通過、`npm run dev` 289ms ready、HTTP probe 全 200
- **瀏覽器驗收結果**：❌ **gate 失敗** — 「完整超音波影像沒有在正確的視窗框」（工程師回報 2026-05-15）
- **推斷**：
  - `aspect-ratio: 4/3` 對超音波影像不適配（US 通常為 fan-shaped、實際寬高比視 transducer 而異，常非 4:3）
  - `resetCamera()` 確實把 Cornerstone 的 camera/zoom 重設為「fit canvas」，但**「canvas 形狀」與「影像形狀」不匹配**時，仍會留邊或裁切
  - 靜態 aspect-ratio 無法涵蓋多種 DICOM 來源；尤其工程師指出 multi-frame vs single-frame 會有不同尺寸
- **依 DISPATCH §「具體工作」4 + §「禁止」4**：停下、不自行進 metadata-driven 尺寸；回報主 Agent 評估
- **可能的後續方向**（供主 Agent 評估、**前端 Agent 不自行決定**）：
  - **方向 A — 試其他靜態比例**：1/1（許多 echo / abdominal US 接近方形）、16/9、5/4 — 仍是不完整解，只能適配某一類 DICOM
  - **方向 B — runtime metadata-aware**（推薦但需新 dispatch 授權）：
    - `setStack` 完成後讀 Cornerstone 的 `cornerstone.metaData.get('imagePlaneModule', imageId)` 或 `get('imagePixelModule', imageId)` 取 `rows` / `columns` / `pixelSpacing`
    - 將 `<div>` 容器的 aspect-ratio 動態設為 `columns / rows`
    - 對 multi-frame，`NumberOfFrames` > 1 → 視為 cine（task #9 / Phase 3 才實作播放控制；本任務只需顯示第一 frame）
  - **方向 C — CSS-only 妥協**：容器保留 4/3 並加 `object-fit: contain` 概念（讓 Cornerstone 的 canvas 自己 letterbox） — 但 Cornerstone 的 canvas 是 WebGL 渲染、不吃 `object-fit`；可能需要外層 wrapper 強制 fit
  - **方向 D — 改 Cornerstone Viewport 設定**：Cornerstone3D 有 `viewport.setProperties({ ... })` 可設 zoom、translation；但 fit-to-image 該由 `resetCamera()` 處理，方向 D 不太可能比 B 更好
- **建議優先序**：B > A > C > D。B 是「正確解」；A 是「下個 dispatch 想快速看效果」可用、會留下 case-by-case 偏差；C 不確定可行性；D 不推薦
- **commit 狀態**：本次 fit dispatch 改動的 `DicomViewer.tsx` + `DicomViewer.module.css` **尚未 commit**；與既有 Stage C 4 個未 commit 檔（src/components/、src/App.tsx、PROGRESS.md、context/SESSION_HISTORY.md）一起留在工作樹，等主 Agent 新 dispatch 拍板處理方向

#### Fix-2 嘗試結果（dispatch `phase-2-task-8-stage-c-metadata`，2026-05-16，gate 失敗）

主 Agent 派 metadata dispatch 採方向 B：runtime metadata-aware 動態 aspect-ratio。

- **手法**：
  - `DicomViewer.tsx`：`await viewport.setStack(...)` 後加 metadata 主路 `cornerstone.metaData.get('imagePlaneModule', imageId)` 取 `rows`/`columns`（**註**：DISPATCH 寫 `imagePixelModule`，實際 Cornerstone 4.22.6 rows/columns 在 `imagePlaneModule` — 已按 §「允許但不強制」1 自行調整）→ 算 `aspectRatio = ${columns} / ${rows}`；備路 `viewport.getImageData?.()?.dimensions` 取 `[columns, rows, slices]`；fallback console.warn
  - 設 `element.style.aspectRatio = aspectRatio`
  - **rAF 等 layout reflow**（DISPATCH 未提但必要，否則 `getBoundingClientRect()` 讀到舊尺寸）
  - 呼叫 `renderingEngine.resize(true, false)`
  - 呼叫 `viewport.resetCameraForResize()`（後來發現等同 `resetCamera()`，見下）
  - 呼叫 `viewport.render()`
  - `DicomViewer.module.css`：保留 `width: 100%; min-height: 400px; aspect-ratio: 4/3` 為 CSS fallback
- **dev server 端驗證**：✅ tsc 通過、`npm run dev` 299ms、HTTP probe 全 200
- **瀏覽器驗收歷程**：
  1. **首次驗收**：影像縮在 viewport 右側 20%、黑底主導 ~80%。Console 無 `[DicomViewer]` warning（metadata 主路成功）。Elements 看到 container `aspect-ratio: 1640/1990`（DICOM 是 1640×1990 大尺寸超音波）但 canvas `width="1265" height="949"`（仍是 4/3 era 的舊值）→ **發現 timing 問題**：`renderingEngine.resize()` 雖 `immediate=true` 同步跑，但跑時瀏覽器還沒 layout reflow，`getBoundingClientRect()` 回舊尺寸 → canvas buffer 卡舊值
  2. **加 rAF 後第二次驗收**：canvas 變成 `width="1265" height="1535"`（aspect 1265/1535 ≈ 1640/1990 ✓）。影像區從 20% 擴到 ~40%、黑底從 80% 縮到 60%。但**仍未填滿** — image 依然偏一邊、container 內仍有大量黑底
- **深度根因分析**：
  - Cornerstone 4.22.6 `StackViewport.js:414-425` 的 `resetCamera` GPU dispatcher **只讀 `resetPan`、`resetZoom`**，完全 ignore `resetToCenter`、`suppressEvents`：
    ```js
    gpu: (options = {}) => {
        const { resetPan = true, resetZoom = true } = options;
        this.resetCameraGPU({ resetPan, resetZoom });  // ← resetToCenter 從未傳下去
        return true;
    },
    ```
    所以 `resetCameraForResize()` 與 `resetCamera()` 在 GPU 模式下**產出完全相同的結果**
  - `renderingEngine.resize()` 內部 (`ContextPoolRenderingEngine.js:169`) 已自動為每個需 resize 的 viewport 呼叫 `vp.resetCameraForResize()` — 所以我外層手動再呼叫是 no-op
  - **真正未解的問題**：Cornerstone GPU 模式底層用 VTK.js（actors + camera 架構）。`setStack` 當下，image actor 在 VTK scene 的 scaling 是**依當時 canvas 尺寸計算 + 鎖定**的；後續 canvas 變大、`resetCameraForResize` 只重設 camera view transform、**actor 的 scene-space scale 不會跟著改**。所以 image 在 canvas 內仍是「以舊 canvas 尺寸 fit 出來」的相對小尺寸，camera 重置只是把它擺中、不會把它放大
- **依 DISPATCH §「禁止」第 4 條 + §「具體工作」4**：停下、不自行擴 scope；本 dispatch gate 失敗待主 Agent 評估新方向
- **可能的後續方向**（供主 Agent 評估）：
  - **方向 E — Fetch metadata 後重 setStack**：metadata 取到、aspectRatio 設好、rAF + resize 後**再呼叫一次 `viewport.setStack([imageId])`**。第二次 setStack 會在新 canvas 尺寸下重做 image actor scene 設置。Cornerstone 內部 image cache 應該已 hit、不會二次下載 DICOM。風險：DISPATCH 從未授權，屬 scope creep
  - **方向 F — ResizeObserver 包外層**：監聽 container size 變動 → 自動 `renderingEngine.resize() + viewport.setStack()`。是 production-grade 解，但架構性改動，明確需新 dispatch
  - **方向 G — 「先 fetch metadata、知道 aspectRatio 再 mount viewport」**：把 metadata 取得提前到 setStack 之前（用 `cornerstone-image-loader` 或自定 image loader 解 DICOM header）。需 image loader API 介入、明確被 DISPATCH §「禁止」5 / 第 4 條禁
  - **方向 H — 暫退**：暫接受影像縮邊、commit 現狀、把完整 fit 留給 task #9 或 Phase 3 處理。但已知這會留下用戶體驗缺口
- **建議優先序**：E > F > H > G。E 改動最小、效果可期；F 是正解但工程量大；H 是務實妥協；G 太深入 Cornerstone 內部
- **commit 狀態**：本 metadata dispatch 改動的 `DicomViewer.tsx`（加 metadata-aware + rAF + resetCameraForResize）+ `DicomViewer.module.css`（加註解說明 CSS 為 fallback-only）**尚未 commit**；與既有 Stage C 主體 + fit dispatch 累積一起留在工作樹

#### Fix-3 嘗試結果（dispatch `phase-2-task-8-stage-c-restack`，2026-05-16，gate 失敗）

主 Agent 派 restack dispatch 採前端 Agent 推薦的方向 E：在 metadata + rAF + resize 之後加二次 `await viewport.setStack([imageId])`，讓 Cornerstone 在新 canvas 尺寸下重建 image actor。

- **手法**：在 `renderingEngine.resize(true, false)` 之後、`viewport.resetCameraForResize()` 之前插入一行：
  ```ts
  await viewport.setStack([imageId])
  if (cancelled) return
  ```
  其他 Fix-2 既有邏輯（metadata 主路/備路/fallback、rAF、resize、resetCameraForResize、cancelled flag、cleanup destroy）全部保留不動
- **dev server 端驗證**：✅ tsc 通過、`npm run dev` 已在跑、HTTP probe 服 Fix-3 新 code（curl 確認 `Re-setStack so Cornerstone` 註解在 served file 中）
- **瀏覽器驗收結果**：❌ **gate 失敗**
  - **影像仍未填滿** container（與 Fix-2 結果類似）
  - **Network tab 0 GET** — Cornerstone 內部 image cache 命中、無第二次下載，符合 DISPATCH 預期 ✓
  - **Console 0 warning** — metadata 主路成功 ✓
- **深度根因分析**（讀 Cornerstone 4.22.6 source code）：
  - `StackViewport.js:1233-1271 setStack` 在 line 1250 設 `stackInvalidated = true`、確保第二次呼叫不走 fast-path
  - `StackViewport.js:1558-1609 _updateActorToDisplayImageId` 在 `sameImageData && !stackInvalidated` 才走優化路徑（line 1561）；我們 stackInvalidated=true 所以走 line 1569 起的 **full rebuild**：建新 VTK image data、`createActorMapper` 建新 actor、`setActors`、`resetCameraNoEvent`
  - **理論上 full rebuild 應該讓 actor 對新 canvas 尺寸 fit**，但實際結果未填滿 → 表示 Cornerstone GPU 模式底層**還有更深的場景狀態與 enableElement 時的 canvas 尺寸綁定**（VTK offscreen render window / camera intrinsic / actor mapper bounds 等），單純 setStack 重建 actor 動不到
  - **重要觀察**：Network tab 0 GET 證明 setStack #2 確實執行到 image cache hit；Console 無 warning 證明 metadata 路徑成功 → **方向 E 在程式碼層面確實有跑，只是 Cornerstone 內部狀態還有其他綁定**
- **依 DISPATCH §「主 Agent 已拍板的決策」5**：停下、不自行擴 scope 到 F（ResizeObserver）或 destroy+recreate 路徑；待主 Agent 評估
- **更新後的後續方向評估**（E 失敗後）：
  - **方向 F — ResizeObserver 包外層**：監聽 container size 變動、自動 `renderingEngine.resize() + setStack`。是 production 解，但已知 setStack 重建單獨不夠 → F 可能也需要搭配 destroy+recreate engine 才有效
  - **方向 I（新增）— Destroy + Recreate engine**：metadata 取到、aspectRatio 設好、rAF 後 → `renderingEngine.destroy()` → `new RenderingEngine(...)` → `enableElement(...)` → `setStack` 一次。讓**整個 engine 在正確 canvas 尺寸下從零建立**，避開所有「綁定在第一次 enableElement 的 canvas 尺寸」的內部狀態。預期效果最徹底
  - **方向 H — 暫退**：commit 現狀（影像縮邊但功能基本可用）、把完整 fit 留到 task #9 / Phase 3。已知會留下 UX 缺口
- **建議優先序**：I > F > H。方向 I（destroy+recreate）改動仍小、針對根因；F 需驗證是否單獨足夠；H 是務實妥協
- **commit 狀態**：本 restack dispatch 改動的 `DicomViewer.tsx`（加 await setStack 第二次 + 註解說明）**尚未 commit**；與既有 Stage C 主體 + fit + metadata dispatch 累積一起留在工作樹

#### Fix-4 嘗試結果（工程師授權的方向 I：destroy+recreate engine，2026-05-16，gate 失敗）

restack dispatch（Fix-3）失敗後，工程師基於「目標是處理影像填滿（最重要）」明確授權前端 Agent 跳過 DISPATCH §「主 Agent 已拍板的決策」5 的「停下、不擴 scope」限制，試方向 I：**destroy+recreate engine**。屬授權的 scope 擴張，**非主 Agent 派發的正式 dispatch**。

- **手法**：useEffect 內部改寫為兩階段
  - **Phase 1（probe）**：在 container 的 CSS fallback aspect-ratio 下 `new RenderingEngine` → `enableElement` → `await setStack` → 讀 `imagePlaneModule` 取 rows/columns → 設 `element.style.aspectRatio` → `await rAF` 等 layout reflow
  - **Phase 2（rebuild）**：`engine.destroy()` → `new RenderingEngine` → `enableElement`（這次 canvas 直接在已 portrait 化的 container 上建立）→ `await setStack`（cache hit）→ `render`
  - 保留 cancelled flag + cleanup `destroy()` (StrictMode-safe)
  - **移除** Fix-2 / Fix-3 累積的 `renderingEngine.resize(true, false)` 與 `viewport.resetCameraForResize()` — 因為新 engine 已在正確尺寸下建立、不需事後修正
- **dev server 端驗證**：✅ tsc 通過、Vite HMR 推 Fix-4 code（curl 確認 `Phase 2 — rebuild` 註解在 served file 中）
- **瀏覽器驗收結果**：❌ **gate 失敗**（工程師回報 2026-05-16）— **影像仍未撐滿 container**
- **意義（重要）**：Fix-4 是針對「Cornerstone 內部狀態綁在第一次 enableElement 的 canvas 尺寸」這個假設的**最徹底解** — destroy 所有舊狀態、在正確尺寸下從零建立 engine + canvas + actor。**仍未解** → 表示：
  - **(a)** 我們對根因的假設不完全正確 — Cornerstone GPU/VTK 內部還有某些 module-level 或 global 狀態被綁定，destroy 解不掉（**最可能** — 例如 `cache`、`metaData provider` 內部對 viewport 的暫存）
  - **(b)** 或問題根本不在 Cornerstone — 而是 CSS layout 層級（container display size 與 inline aspect-ratio 互動有 quirk、`min-height: 400px` 與 aspect-ratio 衝突、`#root` Vite scaffold CSS 限制 max-width…）
  - **(c)** 或問題在 Cornerstone canvas 的 `image-rendering: pixelated` 或 `position: absolute` 與 ResizeObserver-less 行為的交互
- **依工程師指示**：commit 現狀、等主 Agent 下一步指示；不再自行擴 scope
- **更新後的後續方向評估**（I 也失敗後）：
  - **方向 F — ResizeObserver 包外層**：仍是 production 解，但前提是 Cornerstone 對 container resize 有正確回應（Fix-2/3 證明 `renderingEngine.resize()` API 無效、Fix-4 證明 destroy+recreate 也無效）→ F 單獨可能也不夠
  - **方向 J（新增）— CSS 層級偵錯**：暫不動 Cornerstone code、聚焦 CSS：`F12 → Computed`對照 `.viewport`、`.viewport-element`、`canvas` 三層的真實 box dimensions；可能 `min-height: 400px` 與 dynamic aspect-ratio 互動產生 mismatch；可能 `#root` Vite scaffold CSS（max-width / padding / text-align）限制了 container 實際寬度
  - **方向 K（新增）— 簡化 DOM**：拿掉 viewport-element 中間層（Cornerstone 自動建的），直接讓 canvas absolute fill `.viewport`；可能 viewport-element `position: relative` 與 .viewport 的 aspect-ratio 有微妙互動
  - **方向 L（新增）— 完全不同的 Cornerstone API**：放棄 StackViewport、改試 VolumeViewport 或 Wadors / WSI Viewport；US 影像可能更適合不同 viewport type
  - **方向 H — 暫退**：commit 現狀（功能可用、UX 缺口）、把完整 fit 留到 task #9 或 Phase 3。**目前最務實的選擇**
- **建議優先序**：**J > H > F > K > L**。方向 J 改動最小、可能找到真正根因；H 是務實妥協；F 不單獨足夠；K 改動 DOM 結構風險高；L 換 viewport type 屬重構
- **commit 狀態**：依工程師指示**即將 commit** Stage C 完整工作樹（主體 + Fix-1 + Fix-2 + Fix-3 + Fix-4 累積）；commit message 反映完整歷程與當前 UX 缺口；hash 回填 PROGRESS §1 + SESSION_HISTORY B 段

#### Stage C 尺寸缺口 — 整體狀況彙整（2026-05-18 結案）

- **嘗試了 4 個方向**（fit / metadata / restack / destroy-recreate engine），全部 dev server 端驗證通過，全部瀏覽器驗收 ❌
- **方向 J（CSS 層偵錯）— 解決**：task #9 commit 7 (`40d766d`) 內前端 Agent + codex 排查 CSS 層找到根因：① outer div `aspectRatio` 設定衝突（commit 0 `fb656c6` 已固化移除）② Vite scaffold `#root max-width: 1126px` 限制 → 改 `width:100% height:100%` ③ `html/body/#root` 100% chain + `.viewer/.viewport` wrapper 結構建立。user 2026-05-17 ~ 2026-05-18 驗收回報「ok 在中央區顯示」
- **2026-05-18 工程師裁示**：標已解決於 commit `40d766d` (Fix-J)；不再追蹤
- **保留歷史價值**：Fix-1~Fix-4 失敗紀錄不刪，作為未來 Cornerstone 4.x GPU/VTK 整合除錯參考（曾被嘗試但無效的方向：靜態 aspect-ratio / metadata-aware 動態 / 二次 setStack / destroy+recreate engine）

### 4.5 Stage C debug 紀錄（2026-05-15，作為 IMPLEMENTATION.md 補充參考）

驗收過程踩到的兩個非 code 問題、值得記錄：

1. **多個 Vite 實例搶 port** → 主 Agent 前次留的 background dev server + 工程師新啟動的 dev server 互搶 5173，新的 fallback 到 5174 → 後端 CORS 只 allow 5173 → 瀏覽器報 CORS block。對策：每次 Agent 啟動 dev server 完成驗收後須 `TaskStop`，避免 zombie；工程師啟動前可 `netstat -ano | findstr :5173` 確認 free
2. **`vite server` 子指令在 Vite 8 已失效但 process 仍 listen** → 某個 IDE / runner 留下 `cmd /c vite server`（Vite 8 該用 `vite` 而非 `vite server`），佔住 5173 但所有 path 回 404。對策：以 `Get-CimInstance Win32_Process` 看 CommandLine 識別、`Stop-Process` 殺掉
3. **`INSTANCE_ID` 對應 DB 不存在的 instance** → 工程師當下記到的 id=2 後端是 404；用 `curl http://localhost:8000/studies` 與 `curl http://localhost:8000/instances/{n}/file` 探測得 id 1 / 3 可用。對策：上傳 DICOM 時直接從 `POST /upload` response 抄 `instance_id`（HANDOFF §3.1 提及該欄位 2026-05-14 已加入）

---

## 5. 後端需求清單

> 前端開發過程中發現「需要後端配合」的事項。**前端 Agent 不自行 mock**，將需求列在此處等主 Agent 處理。
>
> 主 Agent 處理完成後，會更新 `HANDOFF.md` 反映最新後端狀態，並通知前端 Agent。

### 待回報 / 待處理

> **目前無待處理需求**（Stage B/C 尚未開始，待實際整合時可能浮現）。

### 已預期但尚未確認的需求

> 此節為「目前推測會需要、但實際開發到再確認」的清單，不算正式回報。

- **需要 `GET /studies/{id}/series`** — 列出該 study 的所有 series。
  - 用途：StudyList 點 study → 自動展開 series 子清單
  - 替代方案（前端 hack）：fetch 全部 instances 再過濾，效能不佳
  - 阻擋：StudyList 完整版

- **需要 `GET /series/{id}/instances`** — 列出該 series 的所有 instance。
  - 用途：series 切換時取得 instance 序列（multi-frame study）
  - 阻擋：DicomViewer 在同一 study 內切換 instance

- **需確認 `GET /ai/result/{id}/mask` 實際行為** — backend 目前不知道是否回真 PNG 或 stub。
  - 用途：AIPanel mask overlay 渲染
  - 預期：`image/png` content-type、與原 DICOM 同尺寸
  - 阻擋：AIPanel mask 渲染

### 5.4 後端 upload pipeline + orphan 修復需求（2026-05-18 audit）

> ✅ **已解決於 `scripts/backfill_series_uid.py --apply`**（2026-05-18，主 Agent）。3 個 orphan instances (id=1/3/4) 已補 series_instance_uid `...593537`、orphan count=0、API `/series/1/instances` 從 5 筆 → 8 筆。ID gap (2/5/11+) 結論：PostgreSQL SERIAL 設計、不是 bug。連帶發現新 known issue「upload pipeline 缺 graceful duplicate detection」記於根 PROGRESS §6.12。前端 StudyList 重整後會看到完整 8 個 instances。

工程師於 task #9 收尾時要求做後端全面 audit。發現後請主 Agent 評估處理。

**當前資料狀態**（2026-05-18 probe via `GET /studies` + 8000 endpoints）：
- `studies` 表：1 筆（id=1，patient `1760679216609`，modality=US，study UID `...593536`）
- `series` 表：1 筆（id=1，掛 study 1，series UID `...593537`）
- `instances` 表：8 筆有效記錄
  - id=1 (`Peter_Quiet_1.dcm`)、id=3 (`Peter_Quiet_2.dcm`)、id=4 (`Peter_Quiet_3.dcm`) — `series_instance_uid = NULL`（**orphan**，pre-2026-05-15 upload）
  - id=6 ~ id=10 — `series_instance_uid` 正確 link 到 series 1（post-2026-05-15 upload）
- ID gaps：id=2, 5, 11+ 為 HTTP 404 — 推測失敗上傳殘留 / 已刪除（待澄清）

**Pre/Post migration `e25c80289a9c` (2026-05-15) 狀態**：
- 該 migration 加 `instances.series_instance_uid` 欄 + FK→series
- Pre-upgrade upload 沒寫該欄 → orphan
- Post-upgrade upload 正常寫入

**Upload pipeline audit findings**：
1. ✅ **Idempotency 正確** — 同一組 (study_uid, series_uid, sop_uid) 重上傳會 upsert，無重複（8 instances 對應 8 個 unique SOP UID）
2. ✅ **Grouping 正確** — 同 DICOM session（StudyInstanceUID `...593536` + SeriesInstanceUID `...593537`）→ 1 study + 1 series + N instances，符合 DICOM standard
3. ❌ **Migration 後無 backfill** — pre-2026-05-15 instances (id 1, 3, 4) 仍是 NULL `series_instance_uid`；前端 StudyList 無法看到（`/series/1/instances` 只回 post-upgrade 5 筆）
4. ⚠️ **Instance ID gap 來源不明** — id 2/5/11+ 應確認是「失敗上傳殘留 → DB rollback 後留 sequence gap」還是「被人工 delete」

**建議給主 Agent 評估的後續處理**：
- **(a) 推薦 — 一次性 backfill script**：寫 `scripts/backfill_series_uid.py`，掃 `instances` 表 `series_instance_uid IS NULL` 的記錄、用 `file_path` 重讀 DICOM header、補欄位 + 補建/掛 series。執行 → 解決 orphan 問題
- **(b) 或 follow-up Alembic migration**：同上邏輯但走 alembic 流程、版本控制
- **(c) ID gap 來源澄清**：跑 `SELECT MAX(id) FROM instances` 對照已存在 IDs、確認 sequence 跳號原因（DB rollback / explicit delete / migration 副作用）。如果是 rollback 殘留 → 確認 transaction handling 是否正確
- **(d) Optional `/instances` 列全 endpoint**：給前端 admin / debug 用、可看 orphan；非 MVP 必要

**前端影響說明**：
- 工程師感受：「上傳多次但只看到 1 個 study/series」— **這是 DICOM standard 行為**（同 UID → 同 study/series），不是 bug。若要看到多 study，需要上傳不同 UID 的 DICOM 檔
- 工程師感受：「instance 1/3/4 在 DB 內，前端看不到」— **這是 (a)/(b) 處理才能解的 legacy gap**；目前前端 StudyList 行為正確（顯示 series link 正常的 instances）

---

## 6. 文件維護

| 項目 | 說明 |
|---|---|
| 文件版本 | v1.0 |
| 建立日期 | 2026-05-13 |
| 適用對象 | 前端 Agent、主 Agent、工程師 |
| 更新觸發條件 | 任務完成、發現新缺口、產出新後端需求 |
| 更新方式 | 前端 Agent 在每次任務後同步更新；遵守 [`CLAUDE.md`](./CLAUDE.md) §6 規則 |
