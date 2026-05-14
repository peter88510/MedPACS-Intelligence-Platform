# frontend/SESSION_HISTORY.md — 前端 Agent 工作記憶

> **文件定位**：本檔是**前端 Agent 自己**維護的跨 session 工作記憶。讓「下次 session 起手能無縫接續」。
>
> 與 `PROGRESS.md` 互補：PROGRESS 是進度追蹤（事實清單）、本檔是當下脈絡記憶（前端視角的 mental state）。
>
> **誰維護**：前端 Agent。主 Agent 可讀不可寫（除非緊急修正過時資訊，需在 commit message 說明）。
>
> **更新規則**：見 `frontend/CLAUDE.md` §9。

---

## 系統現況（2026-05-14）

- **架構**：React 19.2 + Vite 8.0 + TypeScript 6.0；單頁 SPA。
- **目錄結構**：
  ```
  frontend/src/
  ├── main.tsx           ← 程式入口，啟動時 await initCornerstone() 才 render
  ├── App.tsx            ← Vite 預設範例（StageC 才會改）
  ├── App.css / index.css
  ├── assets/            ← Vite scaffold 圖片
  └── cornerstone/
      └── setup.ts       ← initCornerstone() — idempotent, module-level singleton flag
  ```
- **dev server**：`npm run dev` → `http://localhost:5173`，啟動 329ms，目前確認無 PowerShell error / warning。Vite pre-bundle 自動處理 `@cornerstonejs/dicom-image-loader`。
- **已裝套件**：`@cornerstonejs/core@4.22.6`、`@cornerstonejs/dicom-image-loader@4.22.6`、`@cornerstonejs/tools@4.22.6`、`dicom-parser@1.8.21`、React 19.2、TypeScript 6.0。
- **目前可做到的事**：dev server 啟動、Cornerstone 已 init（但尚未掛 viewport，因為沒元件需要）。

---

## 進行中的任務

> **無進行中任務**。Stage B 已實作完，等待工程師瀏覽器 DevTools console 驗證後 commit；commit hash 將回填 PROGRESS.md。

---

## 已完成里程碑

> 精選大事（非全部完成項目；全表參見 `PROGRESS.md` §1）。

- **Phase 2 task #7（2026-05-13, `2d055de`）** — React + Vite + TS 專案骨架
- **Phase 2 task #8 Stage A（2026-05-13, `83b8c9a`）** — 安裝 4 個 Cornerstone 套件、Vite pre-bundle 驗證
- **Phase 2 task #8 Stage B（2026-05-14, `<pending commit>`）** — `setup.ts` + `main.tsx` 改造完成，dev server 端驗證乾淨

---

## 待決定事項

- **`<DicomViewer />` Stage C 起手點**：要直接寫 `<DicomViewer />` 元件、還是先做 API client + AppContext 把資料流打通？IMPLEMENTATION.md §10「開發順序建議」傾向後者（先資料流、後 viewer），等下次 dispatch 確認。
- **CSS Modules vs. plain CSS**：IMPLEMENTATION.md §9 預期使用 CSS Modules（`*.module.css`），但 `CLAUDE.md` §11 標 UI 規範未定。Stage C 起步時若要寫第一個元件樣式，先回報主 Agent。
- **`vite.config.ts` 何時要動**：本次 Stage B 證實**不需動**；Stage C 真正載入 DICOM 二進位時可能仍會觸發 wasm / worker 邊界問題（PLAN §12 風險點），屆時再決定。

---

## 上次 session 結尾狀態（2026-05-14）

- **改了什麼**：
  - 新增 `frontend/src/cornerstone/setup.ts`（25 行）
  - 改寫 `frontend/src/main.tsx`（10 → 17 行）
  - 更新 `frontend/PROGRESS.md`：
    - §1 加 Stage B 已完成項
    - §2「進行中」恢復為空
    - §3 移除 Stage B 待辦
  - **未動** `frontend/vite.config.ts`
- **commit 狀態**：**尚未 commit**。dev server 仍在背景跑（task id `bpn5mq48c`）等工程師驗證瀏覽器 DevTools console。
- **下次起手建議**：
  1. 確認工程師對 Stage B 瀏覽器驗證結果 → commit
  2. 若工程師發現 console 噴 cornerstone 相關 error / warning：debug 方向先看 worker / wasm 路徑、再考慮加 `vite.config.ts` 的 `optimizeDeps.exclude`、最後才考慮版本鎖
  3. 若驗證通過 → 等主 Agent 派 Stage C（DICOM 渲染） dispatch

---

## 文件維護

| 項目 | 說明 |
|---|---|
| 文件版本 | v1.0（首版） |
| 建立日期 | 2026-05-14 |
| 維護者 | 前端 Agent |
| 更新時機 | 每次 session 結尾、完成 dispatch 任務後 |
| 主 Agent 行為 | 可讀、原則上不寫 |
