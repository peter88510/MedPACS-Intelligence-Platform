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

> **Phase 3 #2（task_id: `phase-3-frontend-ai-mask-overlay`）— A 段完成；B 段：marker 已能畫出（B1），但正確對齊卡後端資料。**
> - A 段（commit `a2a52dc`）：AIPanel 接真實 AI contract + 結果依 instanceId 快取 + 選 instance 自動唯讀載入既有結果。
> - B 段（向量 overlay，用 crest/trough 座標自畫）：實作 5 檔 + B1 修 US 座標映射（imageToWorldCoords→indexToWorld），marker 已能畫在影像上。**但 overlay 位置仍錯**——① 座標是裁切後座標系（下半部 M-mode）需 crop offset ② multiframe per-frame 未對應、count>150。三項待後端補資料（PROGRESS §5 需求 E/C/D）+ 主 Agent 裁示 multiframe 方向。尚未 commit。

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
- **Phase 2 task #9 — 業務元件層完工（2026-05-16 → 2026-05-18，commits `fb656c6` → `fa0dd34`）** — 11 個 commit (commit 0 固化 codex Fix-J + commits 1-8 業務 + commit 9 docs finalize + commit 10 hash 回填) 完成 API client + VITE_API_BASE_URL env var 制度 + AppContext (5 fields) + Layout/TopBar/StudyList/MetadataPanel/AIPanel 全部業務元件 + DicomViewer ← AppContext + Vite scaffold 清掉。E2E 瀏覽器驗收通過（Layout、cascade、DICOM viewer、metadata、AI、env var fallback 全 ✅）。StudyList toggle 行為已補 (commit 8)。後端 audit 完成、寫進 PROGRESS §5.4 待主 Agent 處理 (orphan instances 1/3/4 + instance ID gap 來源澄清)

### 上次 session 結尾狀態（2026-06-15）

- **Phase 3 #2 A 段完成並 commit `a2a52dc`**（branch `feat/phase3-ai-overlay`）：types/AppContext/AIPanel/css 4 檔 — 接真實 AI contract + 結果依 instanceId 快取 + 選 instance 自動唯讀載入既有結果（`GET /ai/result`）。`tsc -b --noEmit` 乾淨。
- **HANDOFF.md §3.3.1**（mask overlay 正解：用 crest/trough 座標自畫、別用 mask PNG）由主 Agent 更新；該變更**未進 A 段 commit**（前端不寫 HANDOFF），留工作樹待主 Agent 收。
- **座標空間已驗證**：instance 12 crest/trough x∈[103,699]≈Columns 720、y∈[285,326]<Rows 930 → **完整原圖座標系**；overlay 定為 Option B（前端自畫向量 marker），不用 mask PNG。
- **B 段暫停 — 卡後端兩問題**（PROGRESS §5）：A) segmenter 第二次推論崩潰（process 級 model 中毒 `conv2d EagerParamBase`，需重啟 backend）；B) `GET /ai/result` 回 latest-only，失敗 error 紀錄遮蔽先前 completed 好結果（id≈7 被 id 16 蓋）。皆待後端/主 Agent。
- **DICOM 實況**：instance 12 = 720×930、**NumberOfFrames=150 multi-frame**，viewer 顯示 frame 0；B 段目視須確認 crest/trough 是否疊在顯示 frame 上（M-mode 語意）。
- **下次起手**：① 等後端修 A/B → 有可達 completed 結果後開新 branch 做 B 段 overlay（crest/trough → Cornerstone `imageToWorldCoords`→`worldToCanvas`、toggle+opacity、原 DICOM 不動） ② merge/push A 段視工程師決定（建議先 merge）。

### 上次 session 結尾狀態（2026-06-15 晚 — B 段實作）

- **B 段 overlay 實作完成**（後端 A/B 修好、主 Agent 通知後續做），5 檔改動、**尚未 commit**（等工程師敲 git）：
  - `src/api/ai.ts`：`getResult` → `/ai/result/{id}?status=completed`
  - `src/context/AppContext.tsx`：加 `aiOverlayVisible`(true)/`aiOverlayOpacity`(1) + setter 進 context value + memo deps
  - `src/components/DicomViewer/DicomViewer.tsx`：加 `viewportRef`/`imageIdRef`/`viewportEpoch`；Phase 2 render 後公開 viewport + bump epoch；新 overlay effect 用 `utilities.imageToWorldCoords(imageId,[x,y])`→`viewport.worldToCanvas()` 映射 crest/trough 成 canvas 座標，存 `markers` state，監聽 `IMAGE_RENDERED`/`CAMERA_MODIFIED`+`ResizeObserver` 重算；JSX 加 `<svg>` 疊層（line+2 circle/組，opacity 綁 context）
  - `DicomViewer.module.css`：`.viewer` 加 `position:relative`；新增 `.overlay`(absolute/inset0/pointer-events none) + `.exLine`/`.crest`(cyan)/`.trough`(amber)
  - `AIPanel.tsx` + `.module.css`：measurements>0 顯示 toggle + opacity slider
- **技術決策**：
  - overlay 技術選型 = **SVG 疊層 + worldToCanvas 映射**（非 Cornerstone segmentation API、非 mask `<img>`）。理由：crest/trough 是向量座標、§3.3.1 明示不用 mask PNG；worldToCanvas 自動處理 letterbox/zoom/resize 對齊，最穩。
  - overlay 控制狀態放 **AppContext**（AIPanel 控制、DicomViewer 渲染共用），非各自 local state。
- **驗證**：`npx tsc -b --noEmit` 乾淨；`npm run dev` boot 乾淨（483ms；fallback 到 5174 因 5173 已被佔 — 工程師那台的 dev server，CORS 對齊請用 5173 那個）。`npm run lint` 4 個 error 全為**既有**（StudyList setState-in-effect ×2、AppContext react-refresh ×1），本次改動無新 error。
- **未做 / 待 gate（無法由 Agent 完成）**：
  - 瀏覽器目視：overlay 是否對齊、調 opacity / toggle 是否如預期。
  - **multi-frame frame 對應疑問**：instance 12 NumberOfFrames=150、viewer 顯示 frame 0；若量測座標對應的不是 frame 0（M-mode 合成影像 / 另一 frame）→ 會對不齊 → 屆時回報主 Agent，可能需後端補 frame index。
  - `getMaskUrl` builder **未做**：DISPATCH B 原列此項，但 §3.3.1 改用向量 overlay、不需 mask PNG，故略（避免無用 code）。

### 本次 session 結尾狀態（2026-06-16 — B 段驗收回報 + B1 修映射）

- **工程師瀏覽器回報**：A 段 ✅（excursion 數值顯示、Run AI 不再出錯、count 顯示）；**B 段 overlay 完全不顯示**。另指出：演算法 per-frame 跑、一個 DICOM ~150 frame、應 ~150 值，但 **count > 150**（疑後端）；前端尚未處理 multiframe 呈現。
- **overlay 不顯示根因（已查實）**：原用 `utilities.imageToWorldCoords` 對 US 拋 TypeError —— US 無 ImageOrientationPatient/ImagePositionPatient，`dicom-image-loader` 回 `rowCosines/columnCosines=null`、`origin=undefined`，`vec3.scaleAndAdd(out, undefined, null, …)` 炸；被 try/catch 吞 → markers 全空。（loader 原始碼 `wadouri/metaData/metaDataProvider.js` + `extractPositioningFromDataset.js` 證實。）
- **B1 已修（工程師選「先做 B1 修映射」）**：改用 `viewport.getImageData().imageData.indexToWorld([col,row,0])` → `worldToCanvas`（不碰病患座標 tag）。`indexToWorld` 型別為 optional + 回 `Point3|Float32Array` → bind 到 narrowed const + `as Types.Point3`。移除 unused `imageIdRef` 與 `utilities` import。React key 改陣列 index（防 count>150 batch_index 重複）。`tsc -b --noEmit` 乾淨、lint 無新 error。**尚未 commit**。
- **B1 後工程師再回報（2026-06-16）**：marker **畫得出來了，但位置錯 + 多 marker 重疊**。兩主因：
  - **裁切座標系（新發現、最關鍵）**：演算法只取 DICOM **下半部 M-mode 區**計算 → crest/trough 是 crop 後座標、非整圖 → 需 crop offset。**這推翻 A 段「完整原圖座標系」結論**（已更正 PROGRESS §1 + types.ts 註解）。HANDOFF §3.3.1 早預判此情況（`apply_dicom_crop`）。裁切 func 位置工程師可告知。
  - multiframe 未對應（per-frame 全畫 frame 0、重疊）。
- **回報主 Agent（已整理成 PROGRESS §5「後端需求清單」，待工程師轉交）**：需求 E（crop bbox/offset，最優先）+ 問題 C（count>150）+ 需求 D（frame_index）+ 設計疑問（multiframe 呈現 a/b/c，前端不自決）。
- **下次起手**：① B1（映射 bug 修正）可先收尾 commit —— 它是正確的、且是後續任何對齊的前提（marker 已能畫出）② overlay **正確對齊**等後端補 E/C/D + 主 Agent 裁示 multiframe 方向後做（B2/B3）③ git：branch `feat/phase3-ai-overlay-b`、commit message 見回報。

### 更早 session 結尾狀態（2026-05-18）

- **task #9 完成跨 session 工作 — 11 commits 全 push 完畢**（`fb656c6` → `fa0dd34`，皆在 `origin/master`）：
  - Commit 0 `fb656c6` 固化 codex 移除 outer div aspectRatio（Fix-J 根因之一）
  - Commit 1 `e4fd960` API client + .env.example + VITE_API_BASE_URL 制度
  - Commit 2 `2e1d9fb` AppContext (5 fields + cascade)
  - Commit 3 `ea3cc1b` Layout + TopBar (CSS Grid 三欄 + 深色)
  - Commit 4 `fec64f5` StudyList 三層
  - Commit 5 `7c8fe0b` MetadataPanel
  - Commit 6 `d66b6ab` AIPanel
  - Commit 7 `40d766d` DicomViewer ← AppContext + App.tsx 改寫 + Vite scaffold 清掉 + Fix-J 嘗試
  - Commit 8 `4a016cd` StudyList toggle + ▶▼ icon（user 驗收回報補強）
  - Commit 9 `498a845` PROGRESS §1/§2/§3 finalize + §5.4 後端 audit + SESSION_HISTORY 同步
  - Commit 10 `fa0dd34` 回填 commit 9 hash 至 PROGRESS §1（沿用 Stage B/C 兩 commit pattern）
- **驗證歷程**：
  - 每個 commit 後 tsc 通過、push 到 `origin/master`
  - End-to-end 瀏覽器驗收（user 2026-05-17 報告）：Layout / cascade auto-select / DicomViewer 顯示 / MetadataPanel / AIPanel Run AI / VITE_API_BASE_URL fallback **全 ✅**；user 後續要求補 StudyList toggle (commit 8)
  - **Fix-J 看似有效**：user「ok 在中央區顯示」(commit 0 移除 outer div aspectRatio + commit 7 codex CSS `html/body/#root 100%` + `.viewer/.viewport` wrapper 結構)；user 未明示「完全填滿」、保留 §4.4 為「待主 Agent 最終確認」
- **本 session 兩個重要技術 finding**：
  1. **TypeScript 6 `erasableSyntaxOnly`** 禁用 constructor parameter properties — `client.ts:ApiError` 必須用顯式 field declaration 才能編譯
  2. **Vite scaffold `#root max-width: 1126px`** 是 Fix-J 根因之一 — codex 已先排查、改為 `width: 100%; height: 100%`（commit 7 採納）
- **後端 audit 重要發現（PROGRESS §5.4 詳記）**：
  - 8 個 instances，id=1/3/4 是 pre-2026-05-15 orphan (series_instance_uid=NULL)、id=6-10 正確 link
  - Instance ID gap (2/5/11+) 來源待澄清
  - Upload pipeline idempotency + grouping 都正確
  - 建議方向 (a) backfill script 解決 legacy orphan、(c) ID gap 來源澄清
- **commit 狀態**：11 個 commits 已 push 至 `origin/master`、本地與 remote 同步、工作樹**乾淨**（`git status` empty）
- **背景任務**：user 自己的 dev server (PID 32648) 仍在跑、不關（屬 user）；前端 Agent 本 session 沒啟動過 background dev server，無 zombie 需 TaskStop
- **下次起手建議**：
  1. 等主 Agent 看 PROGRESS §5.4 audit findings + 給新 dispatch（推薦 Phase 3 真實 AI + mask、或先處理 §5.4 backend backfill）
  2. Stage C UX 缺口 §4.4：user 驗收「ok」但未明示「完全填滿」、保留待主 Agent 最終確認
  3. 後續若 DICOM 填滿仍有問題、再考慮方向 F/K/L (ResizeObserver / DOM 簡化 / 換 viewport type)
  4. 上傳 DICOM 測試多 study/series 行為：需要用不同 StudyInstanceUID/SeriesInstanceUID 的 DICOM 檔（user 目前手上的都是同一檢查 UID、後端 upsert 都合併成 1+1+N）

---

## 文件維護

| 項目 | 說明 |
|---|---|
| 文件版本 | v1.1（2026-05-14 由主 Agent 做結構性重組為 A/B 兩段，內容未動） |
| 建立日期 | 2026-05-14（v1.0 由前端 Agent 寫於 Stage B 收尾） |
| 維護者 | 前端 Agent（內容）；主 Agent 在結構升級時例外動 |
| 更新時機 | 每次 session 結尾、完成 dispatch 任務後 |
| 主 Agent 行為 | 可讀；原則上不寫；例外：結構性重組 / 緊急修正過時資訊，需在 commit message 說明 |
