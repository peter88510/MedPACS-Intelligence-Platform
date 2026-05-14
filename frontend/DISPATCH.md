---
issued: 2026-05-14
issued_by: 主 Agent
task_id: phase-2-task-8-stage-b
status: active
---

# 當前任務 — CornerstoneJS Stage B（初始化設定）

> **本檔機制**：本檔是**當前任務**的單一入口。主 Agent 派發新任務時會**整檔覆蓋**，不累積歷史。歷史請看 `frontend/PROGRESS.md` 的「已完成任務」段與 git commit log。
>
> **前端 Agent 啟動時必讀**（見 `frontend/CLAUDE.md` §1）。
>
> **修改規則**：前端 Agent **不修改本檔**；只讀。新版本由主 Agent 覆寫。

---

## 任務

### 目標

CornerstoneJS Stage B — 初始化設定。完成後即可進入 Stage C（實際渲染 DICOM）。

### 具體工作

1. **新增 `frontend/src/cornerstone/setup.ts`**，提供 export 的 `initCornerstone()`
   - 內部呼叫 `@cornerstonejs/core` 的 `init()`
   - 內部呼叫 `@cornerstonejs/dicom-image-loader` 的 `init()`，含 worker config
   - 使用模組層級 boolean flag 確保 idempotent（重複呼叫安全）

2. **修改 `frontend/src/main.tsx`**：在 `createRoot().render()` 前 `await initCornerstone()`
   - `main` 函數改為 `async`，或用 IIFE 包覆

3. **視情況調整 `frontend/vite.config.ts`**：
   - `optimizeDeps.exclude` / `include` 可能需加 cornerstonejs 相關套件
   - worker 設定（如 `worker.format = 'es'`）
   - 若遇 wasm 載入問題，加 `server.fs.allow` / `assetsInclude`

4. **重啟 `npm run dev`**，驗證無 error / warning

---

## 相關 API

此 stage **不**直接呼叫 backend API。

Stage C（下一階段）才會用 `wadouri:` scheme 呼叫 `GET /instances/{id}/file`，該 endpoint 後端已就緒，見 `HANDOFF.md` §3.4。

---

## 注意事項

1. **Stage A 已完成**（4 個套件已安裝、Vite pre-bundle 已驗證）— 詳見 `PROGRESS.md`「已完成任務」段，本次不需要重複套件安裝
2. **PLAN.md §12 標註 CornerstoneJS 整合為已知風險**：v3+ 對 esbuild 預打包不友善，預留 1 天 buffer 反覆試錯
3. **不可動 `vite.config.ts` 中的 `server.port`（5173）** — 後端 CORS 對齊
4. **不可動 backend 任何檔案**（含 `main.py` CORS 設定）
5. **不要新增非 cornerstone 必須的 npm 套件**；若 cornerstone 整合需要新依賴，先在 PROGRESS「後端需求清單」記下、回報主 Agent
6. **若 `vite.config.ts` 改動超過 5 行**，在 PROGRESS 中說明理由
7. **不要把 cornerstone 物件存到 React state**（會引發 deep equality 問題）— 一律保留為 module-level singleton 或 useRef
8. **不要在 `setup.ts` 以外的地方呼叫 `cornerstone.init()`**（封裝原則）

---

## 完成標準

### 必須全部成立

- [ ] `frontend/src/cornerstone/setup.ts` 存在、export `initCornerstone()`
- [ ] `frontend/src/main.tsx` 在 render 前呼叫 `initCornerstone()`
- [ ] `npm run dev` 啟動，PowerShell 無 error / warning
- [ ] 瀏覽器 `http://localhost:5173` 開啟，DevTools console 無 error
- [ ] `frontend/PROGRESS.md` 已更新：
  - 收到此 dispatch 後，在「進行中」段寫摘要（格式見 `CLAUDE.md` §6.4）
  - 完成後從「進行中」移到「已完成任務」，加 commit hash
  - 若有新發現的後端需求或缺口，加進對應區塊
- [ ] `frontend/SESSION_HISTORY.md` 第一版建立（首次 dispatch 收尾時）

### 允許但不強制

- 視覺仍是 Vite 預設畫面（Stage C 才看到 DICOM）
- `vite.config.ts` 不一定要動（看 Cornerstone 行為而定）

### 禁止

- ❌ 撈任何 DICOM 並渲染（那是 Stage C）
- ❌ 寫 `<DicomViewer />` 元件實作（那是 Stage C）
- ❌ 在 `setup.ts` 內 fetch backend API
- ❌ 修改 `frontend/DISPATCH.md`（本檔由主 Agent 維護）

---

## 驗證步驟（工程師驗收用）

1. `cd frontend`
2. `npm run dev`
3. 開瀏覽器 `http://localhost:5173`
4. F12 → Console 應該乾淨（無 red error）
5. 關閉 dev server、重啟、再次確認無 error

---

## 回報格式（完成後寫進 PROGRESS 的「已完成任務」項目）

- 改動的檔案清單（path + 大致行數）
- `vite.config.ts` 是否動到、動了什麼
- 遇到的坑（讓主 Agent 可以記進文件）
- `frontend/PROGRESS.md` diff 摘要
- `frontend/SESSION_HISTORY.md` 是否建立（第一版內容快照）
