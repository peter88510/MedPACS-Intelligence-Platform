# frontend/PROGRESS.md — 前端工作進度

> **文件定位**：本檔僅記錄前端的**狀態與進度**。
>
> 架構說明見 [`IMPLEMENTATION.md`](./IMPLEMENTATION.md)；操作教學見 [`README.md`](./README.md)；AI 行為約束見 [`CLAUDE.md`](./CLAUDE.md)。
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

### 文件

- [x] **`frontend/README.md`** — 新手向中文啟動指引、目錄結構解析、名詞速查表（commit `2d055de`）
- [x] **`frontend/IMPLEMENTATION.md`** — 元件樹、Context、API client、Cornerstone Stage A/B/C 計畫（commit `bd42ec9`）
- [x] **`frontend/CLAUDE.md`** — 前端 AI 操作規範（2026-05-13）
- [x] **`frontend/PROGRESS.md`** — 本檔（2026-05-13）

---

## 2. 進行中

> **目前無進行中項目。**

---

## 3. 待辦

> 順序見 [`IMPLEMENTATION.md`](./IMPLEMENTATION.md) §10「開發順序建議」。

### Phase 2 task #8 — CornerstoneJS 整合（接續）

- [ ] **Stage B — Cornerstone init 設定**
  - 新增 `src/cornerstone/setup.ts`，提供 `initCornerstone()`
  - `main.tsx` 啟動時呼叫一次
  - 視需要調整 `vite.config.ts`（worker / wasm / optimizeDeps）
  - 驗證 dev server 啟動無 error / warning
- [ ] **Stage C — 第一個 DICOM 渲染**
  - 完成 `<DicomViewer />` 實作
  - 透過 `wadouri:` scheme 從 `/instances/{id}/file` 載入並渲染
  - 提供 zoom / pan / window-level 互動

### Phase 2 task #9 — 四個業務元件

- [ ] **API Client (`src/api/`)**
  - `client.ts`（fetch wrapper + ApiError）
  - `types.ts`（Study / AIResult 等共享型別）
  - `studies.ts` / `series.ts` / `instances.ts` / `ai.ts`
- [ ] **AppContext (`src/context/AppContext.tsx`)**
  - 5 個欄位：`studies` / `currentStudyId` / `currentSeriesId` / `currentInstanceId` / `aiResult`
  - `useAppContext()` hook
- [ ] **`<Layout />` + `<TopBar />`** — 結構元件、CSS Grid 三欄
- [ ] **`<StudyList />`** — 左欄、列出 study、點擊切換
- [ ] **`<MetadataPanel />`** — 右上、顯示 instance metadata
- [ ] **`<AIPanel />`** — 右下、Run AI 按鈕 + 結果顯示
- [ ] **CSS Modules 樣式整理** — 收尾、視覺微調

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

---

## 6. 文件維護

| 項目 | 說明 |
|---|---|
| 文件版本 | v1.0 |
| 建立日期 | 2026-05-13 |
| 適用對象 | 前端 Agent、主 Agent、工程師 |
| 更新觸發條件 | 任務完成、發現新缺口、產出新後端需求 |
| 更新方式 | 前端 Agent 在每次任務後同步更新；遵守 [`CLAUDE.md`](./CLAUDE.md) §6 規則 |
