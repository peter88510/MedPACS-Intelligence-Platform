---
issued: 2026-05-16
issued_by: 主 Agent
task_id: phase-2-task-9-business-components
status: active
supersedes: phase-2-task-8-stage-c-restack (Stage C 已 commit 13cccd3 含 UX 缺口；UX 缺口由本 dispatch CSS 整理段順手處理)
---

# 當前任務 — Phase 2 task #9：4 業務元件 + AppContext + API client + env var 制度

> **本檔機制**：本檔是**當前任務**的單一入口。主 Agent 派發新任務時會**整檔覆蓋**，不累積歷史。歷史請看 `frontend/PROGRESS.md` 的「已完成任務」段與 git commit log。
>
> **前端 Agent 啟動時必讀**（見 `frontend/CLAUDE.md` §1）。
>
> **修改規則**：前端 Agent **不修改本檔**；只讀。新版本由主 Agent 覆寫。

---

## 任務

### 目標

完成 Phase 2 業務元件層 — 從「hardcoded INSTANCE_ID 顯示一張 DICOM」進化到「完整 SPA：選 study → 自動列 series → 列 instance → 渲染 + metadata 顯示 + AI stub 觸發」。

依賴：
- ✅ Stage C 已 commit `13cccd3`（DicomViewer 元件已存在，本 task 改造其 props 來源）
- ✅ Backend 補完 `9967f71` + `40fd1e9`（`/upload` 回 instance_id、`/studies/{id}/series`、`/series/{id}/instances` 都已上線）
- ✅ 工程師已跑 `alembic upgrade head`（migration `e25c80289a9c` 已 apply）

### 主 Agent 已拍板的決策

- **起手 commit 0（先於下面 7 個 commit）— 固化 codex 已做的 aspectRatio 移除修正**：
  - 工程師於 2026-05-16 用 codex 排查找到根因之一：`element.style.aspectRatio = '${cols}/${rows}'` 套在 Cornerstone-managed outer div 上 → 在 flex / grid + `min-height` / `height: 100%` chain 環境下與瀏覽器 size derive 衝突 → viewport 被壓縮（曾觀察到 ~165px 寬）
  - codex 已動：移除 `DicomViewer.tsx` 內所有 `element.style.aspectRatio` 設定（不再 runtime 套 aspect-ratio 到 outer div）
  - **本 commit 0 只固化 codex 的這個刪除動作**，與其 1:1、不擴 scope、不動 module.css、不引入其他變更
  - Commit message: `fix(frontend): 移除 DicomViewer outer div 的 aspectRatio 設定 (避免與 layout height chain 衝突)`，body 簡述 codex 排查與 root cause、指向 `frontend/PROGRESS §4.4` 與 `根 PROGRESS §6.11`
- **拒絕 codex 提的 setTimeout 300ms workaround**：那是 race condition 掩蓋、不是 root cause。Layout 三欄就位後若仍有 race（resize 時機晚於 render），用 `useLayoutEffect` + rAF 或 `ResizeObserver`，**禁止 setTimeout**
- **API base URL**：採 `VITE_API_BASE_URL` env var 制度（本 task dispatch 內正式導入）
- **State 管理**：React Context（`AppContext`，5 fields）— **不引入** Redux / Zustand / TanStack Query
- **CSS**：CSS Modules（與 Stage C 同）
- **Layout**：CSS Grid 三欄 — TopBar 在頂、StudyList 在左、DicomViewer 在中、MetadataPanel + AIPanel 在右上下分（依 frontend/docs/IMPLEMENTATION.md §架構圖）
- **DicomViewer**：改 props 從 AppContext.currentInstanceId 取；**移除** App.tsx 的 hardcoded `INSTANCE_ID = 1`
- **AI mask overlay**：本 task **不**做（依賴 Phase 3 真實 mask；frontend §5「後端需求清單」第 3 條 still pending）
- **Multi-frame UI / cine**：本 task **不**做（Phase 3）
- **upload UI**：本 task **不**做（依 PLAN §10.5、frontend HANDOFF §3.4）
- **Stage C UX 缺口（影像未填滿 container）**：在「CSS Modules 樣式整理」子段**順手做方向 J（CSS 層偵錯）**；若 J 無解、留為 known issue（PROGRESS §6.11、根 PROGRESS §6.11）

### 具體工作（commit 0 + 7 個業務 commit，共 8 個）

**Commit 0**：見上方「主 Agent 已拍板的決策」第一條 — 固化 codex 的 aspectRatio 移除修正。

1. **API client + env var 制度**（`src/api/`）
   - `client.ts`：fetch wrapper（含 base URL 從 `import.meta.env.VITE_API_BASE_URL` 讀，default `http://localhost:8000`）+ `ApiError` class（含 status code + parsed body）
   - `types.ts`：共享 TypeScript types（`Study`、`Series`、`Instance`、`InstanceMetadata`、`AISegmentResponse`、`AIResultResponse`）
   - `studies.ts`：`listStudies()` → `GET /studies`、`listSeriesForStudy(studyId)` → `GET /studies/{id}/series`
   - `series.ts`：`listInstancesForSeries(seriesId)` → `GET /series/{id}/instances`
   - `instances.ts`：`getInstance(id)`、`getInstanceMetadata(id)`、`getInstanceFileUrl(id)`（純 URL builder，給 wadouri 用）
   - `ai.ts`：`triggerSegmentation(instanceId)` → `POST /ai/segment/{id}`、`getResult(instanceId)` → `GET /ai/result/{id}`
   - `.env.example` 加 `VITE_API_BASE_URL=http://localhost:8000`；建議建 `.env.local`（前端 Agent 不 commit、`.gitignore` 應已涵蓋 `.env*`，若沒涵蓋確認後加）
   - **commit**：`feat(frontend): API client + VITE_API_BASE_URL env var 制度`

2. **AppContext**（`src/context/AppContext.tsx`）
   - 5 fields：`studies: Study[]`、`currentStudyId: number | null`、`currentSeriesId: number | null`、`currentInstanceId: number | null`、`aiResult: AIResultResponse | null`
   - Provider 含 setter helpers + reducers（用 useReducer 或 useState 視複雜度）
   - `useAppContext()` hook + null check
   - 啟動時 fetch `/studies` 填 `studies`、預設選第一個（若有）→ 觸發 series fetch → instance fetch → 預設選第一個 instance
   - **commit**：`feat(frontend): AppContext + 5 field state shape`

3. **結構元件**（`src/components/Layout/` + `src/components/TopBar/`）
   - `Layout.tsx` + `Layout.module.css`：CSS Grid `grid-template-areas: "topbar topbar topbar" "studylist viewer rightpanel"; grid-template-columns: 240px 1fr 280px; grid-template-rows: 56px 1fr;`
   - `TopBar.tsx` + `TopBar.module.css`：簡單 header（標題 "MedPACS"、可加目前選中的 study/series/instance UID 顯示作 debug）
   - **commit**：`feat(frontend): Layout + TopBar 結構元件`

4. **`<StudyList />`**（`src/components/StudyList/`）
   - 左欄、列出 `appContext.studies`、可展開 series 子清單（點 study → fetch + show series → 點 series → fetch + show instances）
   - 三層 nested list 或 expandable tree（看實作偏好）
   - 點 instance → 設 `currentStudyId / currentSeriesId / currentInstanceId`
   - **commit**：`feat(frontend): StudyList 元件 + 三層展開`

5. **`<MetadataPanel />`**（`src/components/MetadataPanel/`）
   - 右上、依 `currentInstanceId` fetch `/instances/{id}/metadata` 顯示 key-value 表
   - Loading / empty / error 三態（不必過度設計）
   - **commit**：`feat(frontend): MetadataPanel 元件`

6. **`<AIPanel />`**（`src/components/AIPanel/`）
   - 右下、`Run AI` 按鈕（disabled if no `currentInstanceId`）
   - 按下 → `POST /ai/segment/{id}` → polling or one-shot fetch `/ai/result/{id}` → 顯示 `aiResult` JSON
   - **mask overlay 不做**（pending Phase 3 真實 mask）— UI 顯示「Mask 渲染待 Phase 3」字樣即可
   - **commit**：`feat(frontend): AIPanel 元件 + AI stub 接通`

7. **DicomViewer 改造 + App.tsx 改寫 + CSS Modules 樣式整理**
   - DicomViewer：移除 prop `instanceId`、改從 `useAppContext().currentInstanceId` 取（或保留 prop 但 App.tsx 從 context 傳入 — 視 prop 純度偏好）
   - `currentInstanceId === null` 時顯示空狀態（避免 wadouri URL 變成 `/instances/null/file`）
   - App.tsx 改為：`<AppContextProvider><Layout><TopBar /><StudyList /><DicomViewer /><MetadataPanel /><AIPanel /></Layout></AppContextProvider>`
   - 移除 hardcoded `INSTANCE_ID = 1` 與相關註解
   - **CSS Modules 樣式整理**：
     - 統一視覺風格（深色主題或淺色擇一、本 task 限縮為深色 — viewer 黑底為主、配深灰 panel）
     - 清掉 Vite scaffold 殘留（`App.css` 不再 import 可刪、`assets/` 留空、`public/vite.svg` 等）
     - **方向 J — CSS 層偵錯 Stage C UX 缺口**：
       - F12 → Computed 對照 `#root`、`.viewport`、`.viewport-element`、`canvas` 四層的真實 box dimensions
       - 確認 Vite scaffold `#root` 是否有 `max-width` / `padding` / `text-align: center` 限制
       - 確認 DicomViewer container 在 Layout 三欄內（`grid-area: viewer`）的實際寬高、`min-height` 與 dynamic `aspect-ratio` 是否衝突
       - 嘗試移除 `min-height` 或改用 `display: flex` + `flex: 1` 給 viewport
       - 若找到 root cause、修；**若 30 分鐘內無解、停下、加進 PROGRESS §4.4 Fix-J 子段、留為 known issue 進 task #9 commit**
   - **commit**：`feat(frontend): DicomViewer ← AppContext + CSS Modules 整理 (含方向 J 嘗試)`

---

## 相關 API

完整 spec 見 `docs/generated/api_spec.md`（11 routes 全可用）。本 task 用到：

| Endpoint | 用途 | Component |
|---|---|---|
| `GET /studies` | 啟動時填 AppContext.studies | AppContext init |
| `GET /studies/{id}/series` | 點 study 展開 series | StudyList |
| `GET /series/{id}/instances` | 點 series 展開 instances | StudyList |
| `GET /instances/{id}/file` | DICOM bytes（透過 wadouri） | DicomViewer（既有） |
| `GET /instances/{id}/metadata` | metadata 顯示 | MetadataPanel |
| `POST /ai/segment/{id}` | 觸發 AI（stub queued） | AIPanel |
| `GET /ai/result/{id}` | 取 AI 結果（stub completed） | AIPanel |

**已知缺口**：
- `/upload` UI 不做（HANDOFF §3.4）
- AI mask 真實 PNG 不存在（HANDOFF §6 第 3 條）— AIPanel 顯示 JSON、不做 overlay

---

## 相關深入文件

- **必查**：`frontend/docs/IMPLEMENTATION.md` §10「開發順序建議」+ §架構圖 + §components 表
- **必查**：`frontend/context/HANDOFF.md` §3 / §4 / §6 / §7（後端 API 補充說明 + endpoint 狀態 + 重大變更）
- **必查**：`docs/generated/api_spec.md`（API 權威來源）+ `docs/generated/db_schema.md`（schema 權威來源）
- **背景**：`frontend/PROGRESS.md` §4.4（Stage C UX 缺口完整紀錄、4 個方向都 fail 的歷程；方向 J 候選）

---

## 注意事項

### 渲染原則（與 Stage C 同，重申）

- **等比縮放 + 保留原始資料**：DicomViewer 內部不可寫自訂 image resize / canvas redraw / Image() hack / 改 image data
- Cornerstone WebGL canvas 永遠等比 + 高品質 resampling
- 原 DICOM bytes 全程不變

### Stage C UX 缺口處理（方向 J）

- 在「CSS Modules 樣式整理」commit 內順手做
- **30 分鐘 timebox**：若 30 分鐘 CSS 偵錯找不到、停下、寫 §4.4 Fix-J 結果、留為 known issue
- 不要 scope creep 到 Cornerstone code、不要再做 Fix-5/6 type 的 deep dive
- 若 J 找到根因 + 修好 → PROGRESS §4.4 主段標「已解決於 commit XXX (Fix-J)」+ 根 PROGRESS §6.11 同步更新

### Scope 邊界（禁忌）

- ❌ 不可動 backend / `vite.config.ts` server.port / `main.tsx` / `setup.ts`
- ❌ 不可改 Stage C 既有的 metadata-aware aspect-ratio / 二次 setStack / destroy+recreate 邏輯（保留 Fix-4 累積結果）
- ❌ 不可加 frame 切換 / cine / multi-frame UI（Phase 3）
- ❌ 不可實作 AI mask overlay 渲染（Phase 3 真實 mask 才做）
- ❌ 不可實作 upload UI（PLAN §10.5）
- ❌ 不可引入 Redux / Zustand / TanStack Query / SWR / React Query（Context 夠用）
- ❌ 不可引入 UI framework（MUI / Antd / Chakra）— 用 CSS Modules
- ❌ 不可改 `frontend/CLAUDE.md` §11 待補規範（屬主 Agent + 工程師決策範圍）
- ❌ 不可修改本檔
- ❌ Fix-J 不可超時 30 分鐘 / 不可動 Cornerstone code

### Commit 操作

- **拆 7 個 commit**（見「具體工作」段標註）— 不要單一 commit
- 每個 commit 都要：tsc 通過 + dev server 啟動乾淨 + 該 commit 範圍內的元件可運作（不必所有元件都跑、只測新加的）
- 最後一個 commit 後做 end-to-end 瀏覽器驗收（點 study → 渲染 → metadata → AI 觸發）
- pre-commit hook 對前端檔不觸發（仍會跑、不影響）
- 完成後 TaskStop background dev server

### 環境變數規範（新導入）

- `VITE_API_BASE_URL=http://localhost:8000` 寫進 `.env.example`
- 前端 Agent 在自己 dev 環境**可建** `.env.local` 覆蓋（不 commit；確認 `.gitignore` 涵蓋 `.env*` 或至少 `.env.local`）
- 若 `.gitignore` 沒涵蓋、回報主 Agent（這屬 backend `.gitignore` 範圍、主 Agent 處理）
- `client.ts` 應 fallback：`const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'`

---

## 完成標準

### 必須全部成立

- [ ] `src/api/` 完整：`client.ts` / `types.ts` / `studies.ts` / `series.ts` / `instances.ts` / `ai.ts`
- [ ] `.env.example` 含 `VITE_API_BASE_URL`；`client.ts` 有 fallback
- [ ] `src/context/AppContext.tsx` 完整：5 fields + Provider + `useAppContext()` hook
- [ ] `<Layout />` + `<TopBar />` + `<StudyList />` + `<MetadataPanel />` + `<AIPanel />` 全部存在 + module.css
- [ ] App.tsx 改為 `AppContextProvider` 包 `Layout` + 5 元件；移除 hardcoded `INSTANCE_ID`
- [ ] DicomViewer 改用 `useAppContext().currentInstanceId`；`null` 時顯示空狀態
- [ ] CSS Modules 樣式整理：深色主題、Vite scaffold 殘留清乾淨
- [ ] **方向 J 嘗試結果**：成功 → §4.4 標已解決；timebox 內無解 → §4.4 加 Fix-J 結果 + 留 known issue
- [ ] `npx tsc -b --noEmit` 通過
- [ ] `npm run dev` 啟動乾淨（無 error / warning）
- [ ] **End-to-end 瀏覽器驗收**：
  - 開 `http://localhost:5173` → 看到 Layout 三欄
  - StudyList 顯示 studies → 點一個 study → 自動展開 series → 點一個 series → 展開 instances → 點一個 instance
  - DicomViewer 渲染該 instance（影像出現；填滿狀況依 J 結果）
  - MetadataPanel 顯示 metadata
  - AIPanel `Run AI` 按下 → response 顯示
- [ ] 8 個 commit（commit 0 codex 固化 + 7 業務 commit；依「具體工作」段拆分）
- [ ] 每 commit 都 push（不要全做完才 push、避免單筆 push 過大）
- [ ] PROGRESS.md §1 加各元件完成項；§2 進行中清空；§3 待辦移除 task #9 / 加 Phase 3 預告（如「真實 AI 推論 / mask overlay」）
- [ ] SESSION_HISTORY 更新到反映 task #9 完工
- [ ] 完成後 TaskStop background dev server

### 允許但不強制

- AppContext 用 useState 或 useReducer 任一 — 視 5 fields 互動複雜度
- StudyList 三層展開 vs flat list 任一 — 看 UX 偏好
- AIPanel polling 還是 one-shot fetch — 視體驗
- 深色主題具體配色 — 黑底為主、深灰 panel；不需精細設計

### 禁止

- ❌ 單一 commit
- ❌ 動 backend / 既有 Stage C Cornerstone 邏輯 / Phase 3 範圍
- ❌ 引入 Redux / UI framework / 任何超出 fetch wrapper 的 HTTP library
- ❌ Fix-J 超時 30 分鐘繼續鑽
- ❌ 跳過 end-to-end 驗收

---

## 驗證步驟（工程師驗收用）

1. 確認 backend 跑著 + 至少有 2 個 study 在 DB（用 `curl /studies` 確認）
2. `cd frontend && npm install`（若有新依賴；本 task 不應引入新 npm 依賴、純前端）
3. `cd frontend && npm run dev`
4. 瀏覽器開 `http://localhost:5173`
5. **預期**：
   - 看到三欄 Layout + TopBar
   - StudyList 顯示 studies
   - 點 study → 展開 series → 展開 instances
   - 點 instance → DicomViewer 渲染 + MetadataPanel 顯示 metadata
   - Run AI 按下 → AIPanel 顯示 stub 結果
6. F12 → Console 無 red error
7. F12 → Network：所有 fetch 走 `http://localhost:8000`（即 fallback 生效；若想驗證 env var、改 `.env.local` 設不同 URL 重啟 dev server）
8. **方向 J 驗收**：影像填滿狀況比 Stage C `13cccd3` 改善？或仍同樣 60% 黑底？依 PROGRESS §4.4 Fix-J 結果

---

## 回報格式（每 commit message + 最後總結）

每個 commit message 格式：
```
feat(frontend): <component name> — <one-line summary>

<2-3 lines on what + why>

<optional: gotchas observed>
```

最後總結（寫進 SESSION_HISTORY B 段「上次 session 結尾狀態」）：
- 7 個 commit hash 序列
- 方向 J 結果（成功 / 30 分鐘 timebox 觸發 / 找到 root cause 但未修）
- 任何意外發現（後端 API 行為、Cornerstone 整合細節、CSS quirks）
- 新發現的 known issue（加進 PROGRESS §4 已知缺口）

---

## 預期下個 dispatch（Phase 3 起手，主 Agent 規劃中）

- **Phase 3 backend**：`AIResult` model + Alembic migration + `ai_service.py` + PyTorch 模型載入 + `/ai/segment/{id}` 真實實作 + `/ai/result/{id}/mask` 真 PNG endpoint
- **Phase 3 frontend**：AIPanel mask overlay 真渲染（取代 stub JSON 顯示）
- **Phase 4**：sample DICOM 準備 + end-to-end demo 演練（PLAN §13）
- **可能的 Stage C UX 缺口收尾**：若 task #9 期方向 J 仍無解、可能在 Phase 3 期單獨派 viewer-fit dispatch（depending on demo gating）
