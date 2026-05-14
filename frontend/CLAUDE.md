# frontend/CLAUDE.md — 前端 AI 操作規範

> **文件定位**：本檔為 `frontend/` 子專案的 **AI Operating Contract**，**僅適用於前端 Agent**。
>
> 後端 / 跨專案規範以根目錄 [`../CLAUDE.md`](../CLAUDE.md) 為準；當本檔與根 CLAUDE.md 衝突時，**根 CLAUDE.md 優先**。

---

## 目錄

1. [啟動時必讀文件](#1-啟動時必讀文件)
2. [適用範圍](#2-適用範圍)
3. [角色定位](#3-角色定位)
4. [與後端的協作流程](#4-與後端的協作流程)
5. [後端需求清單格式](#5-後端需求清單格式)
6. [PROGRESS.md 更新規則](#6-progressmd-更新規則)
7. [HANDOFF.md 機制](#7-handoffmd-機制)
8. [DISPATCH.md 機制](#8-dispatchmd-機制)
9. [SESSION_HISTORY.md 規則](#9-session_historymd-規則)
10. [與根 CLAUDE.md 的關係](#10-與根-claudemd-的關係)
11. [待補充規範（TODO）](#11-待補充規範todo)
12. [文件維護](#12-文件維護)

---

## 1. 啟動時必讀文件

### 1.1 必讀（每次 session 啟動）

下列 **5 份**為前端 Agent 啟動的最小工作集，**每次 session 開始都要讀**：

| # | 文件 | 用途 |
|---|---|---|
| 1 | `frontend/CLAUDE.md`（本檔） | 行為規範與角色定位 |
| 2 | `frontend/HANDOFF.md`（主 Agent 維護） | **持續更新**的後端狀態文件，每次啟動讀最新版 |
| 3 | `frontend/DISPATCH.md`（主 Agent 維護） | **當前任務交付**；每次新任務會整檔覆蓋 |
| 4 | `frontend/PROGRESS.md` | 前端工作進度（含已知缺口、後端需求清單） |
| 5 | `frontend/SESSION_HISTORY.md` | 跨 session 工作記憶（前端 Agent 自己維護） |

讀完後，依 `DISPATCH.md` 的當前任務開始工作。

### 1.2 按需查閱（僅當任務指引指向時讀）

下列文件**不在啟動必讀範圍**，避免重複載入大份文件。當 `DISPATCH.md`「相關深入文件」段落指向、或開發過程明確需要時才讀：

| 文件 | 何時讀 |
|---|---|
| `frontend/IMPLEMENTATION.md` | 任務涉及元件設計、Context 設計、API client、CornerstoneJS 整合計畫等架構層 |
| `frontend/README.md` | 任務涉及啟動流程、環境設定、新依賴安裝等工程環境層 |

> **理由**：兩份檔合計 ~895 行（~8K tokens），多數 dispatch 只需要其中一小段。改為按需查閱可降啟動 token 消耗約 40%（從 ~18K 降到 ~11K）。

---

## 2. 適用範圍

### ✅ 可操作的範圍

- `frontend/` 資料夾**內**的所有檔案
- 撰寫、修改、刪除 `frontend/src/`、`frontend/public/`、`frontend/*.{json,ts,js,md,html}` 等
- 新增前端依賴（`npm install`）— 但需記得同步 `package.json` / `package-lock.json` 進 git

### ❌ 不可操作的範圍

- `frontend/` **以外的任何檔案**（含根目錄 `.md`、backend 程式碼、`alembic/`、`tests/`、`validation/`、`storage/` 等）
- 後端 API（不可動 `main.py` 路由、handler、response schema）
- DB schema（不可動 `models.py`、`alembic/` migration）
- 系統架構分層（不可重構 Service / Model / DB layer）
- 根目錄文件（`README.md`、`PLAN.md`、`PROGRESS.md` 等由主 Agent 負責）
- `CLAUDE.md`（含本檔）— 文件本身受保護，修改需工程師發起

---

## 3. 角色定位

### 3.1 核心原則

```
1. 只動 frontend/ 內，不越界
2. 後端需要配合的事情 → 回報主 Agent，不自行處理
3. API 尚未就緒時 → 不要自己 mock 後就當作完成；要明確回報
4. 每次任務完成後更新 frontend/PROGRESS.md
5. 所有新建文件一律使用繁體中文
```

### 3.2 應該做的

- 寫 / 改 React 元件、Hook、Context、Utility
- 寫 / 改 CSS（CSS Modules 為主，無 UI framework）
- 寫 / 改 API client（`src/api/`） — **只串接已存在的後端 endpoint**
- 寫 / 改前端測試（Vitest / React Testing Library，若日後導入）
- 撰寫前端文件（`frontend/*.md`）
- 升級 / 安裝 npm 套件（事先說明用途，符合 PLAN.md 範圍）

### 3.3 不應該做的

- ❌ 自行修改後端任何檔案（即使「順手」）
- ❌ 自行 mock 後端 API 並當作完成（除非主 Agent 明確同意）
- ❌ 自行決定 UI 設計系統、色系、元件庫（屬於主 Agent 決策範圍，見 §9）
- ❌ 重大架構決策（如導入 Redux / Next.js / SSR / 切 monorepo）— 必須先回報主 Agent
- ❌ 修改 `vite.config.ts` 中**影響 dev origin（port 5173）的設定**，會破壞後端 CORS 對齊
- ❌ 修改 frontend/CLAUDE.md（本檔受保護）

### 3.4 不確定時的行為

- 不確定該不該動某個檔案 → **停下來問主 Agent**
- 不確定後端 API 是否已就緒 → 先查 `HANDOFF.md`，仍不確定 → **問主 Agent**
- 不確定 UI / UX 決策 → 見 §9 待補充規範，回報主 Agent
- 多種解法都合理 → 列出選項與 trade-off，讓主 Agent / 工程師決定

> 此規則承襲根 CLAUDE.md §10「不確定就問，不猜測就停」。

---

## 4. 與後端的協作流程

### 4.1 一般流程

```
主 Agent 派任務
    ↓
讀取 HANDOFF.md（檢視後端目前可用 API、Schema）
    ↓
任務在現有 API 範圍內？
    ├─ 是 → 直接開發 → 完成 → 更新 frontend/PROGRESS.md
    └─ 否 → 整理「後端需求清單」(§5) → 回報主 Agent → 暫停
                ↓
            等待主 Agent 完成後端調整、更新 HANDOFF.md
                ↓
            收到新版 HANDOFF → 重新開始
```

### 4.2 不可單方面進行的情況

- API endpoint 尚未存在 → 回報、不要 mock 假裝有
- API response schema 不夠用 → 回報，不要前端自己組裝
- DICOM 渲染需要的欄位後端沒回 → 回報，不要前端硬猜
- 需要新增 backend env var → 回報，不要在 `.env` 改

### 4.3 例外：純前端決策可自行進行

- React 元件內部實作細節（state shape、useEffect 依賴清單等）
- CSS 樣式（在 §9 UI 規範補上前，**輕量視覺調整**可自行決定，但避免引入大型設計系統）
- 前端 utility 函數
- TypeScript 型別定義（**前提**：對應的 backend response schema 已明確）

---

## 5. 後端需求清單格式

當任務需要後端配合時，**前端 Agent 暫停實作**，產出以下格式回報主 Agent：

```markdown
## 後端需求清單

**情境**：[簡述前端任務 + 為何卡住]

**需要後端做的事**：

1. [需求 1：例如「`/studies/{id}/series` endpoint 列出該 study 的所有 series」]
   - 用途：StudyList 點擊後展開 series 子清單
   - 預期 response shape：[ {id, series_instance_uid, modality}, ... ]
   - 阻擋的前端任務：StudyList 元件 v2

2. [需求 2：例如「`/ai/result/{id}/mask` 實際回傳 PNG，目前 backend 似乎是 stub」]
   - 用途：AIPanel 顯示 mask overlay
   - 預期：`image/png` content-type、與原 DICOM 同尺寸
   - 阻擋的前端任務：AIPanel mask 渲染

**目前進度**：[列出本次任務已完成的部分（若有）]

**建議優先序**：[需求 1 > 需求 2，因為...]
```

完成回報後：
1. 將此清單**同時**寫進 `frontend/PROGRESS.md` 的「後端需求清單」區塊
2. 等待主 Agent 處理、更新 `HANDOFF.md`
3. 重新讀取 HANDOFF 後再續做

---

## 6. PROGRESS.md 更新規則

### 6.1 更新時機

- **每次任務完成後**，**必須**更新 `frontend/PROGRESS.md`
- 更新內容必須反映：① 主 Agent 此次分配的任務、② 累積的過往任務

### 6.2 更新原則

- 只更新有變動的區塊，不重寫整檔
- 已完成項目從「進行中」或「待辦」移到「已完成任務」
- 新發現的缺口加進「已知缺口」
- 新發現的後端需求加進「後端需求清單」
- 不記錄對話流水帳，只記錄狀態與結論

### 6.3 不可刪除已完成項目

「已完成任務」區塊**累積**所有歷史里程碑，不可移除（即使該任務後來被廢棄，應改標註「已廢棄 — 原因」而非刪除）。

### 6.4 任務生命週期（待辦 → 進行中 → 已完成）

主 Agent 派發任務的方式：**整檔覆寫 `DISPATCH.md`**（機制見 §8）。前端 Agent 啟動讀到新版 DISPATCH 後，必須把任務的精簡常駐版本寫進 `PROGRESS.md`「進行中」段，作為當下工作狀態的單一真實源。

#### 工作流

```
DISPATCH.md（主 Agent 覆寫） ← 當前任務
    ↓ 前端 Agent 讀
PROGRESS.md「待辦」  ← 想做但尚未開工的事
    ↓
PROGRESS.md「進行中」← 加入該任務的精簡摘要（見下方格式）；從「待辦」移除對應項
    ↓ 前端 Agent 完成
PROGRESS.md「已完成」← 加入（含 commit hash 與簡短結果）；從「進行中」移除
```

#### 進行中段格式（從 DISPATCH 萃取，不是原文複製）

```markdown
### <任務名稱>
- **任務來源**：<YYYY-MM-DD DISPATCH.md（task_id: xxx）>
- **核心工作**：
  - <bullet 1>
  - <bullet 2>
  - <bullet 3-5>
- **完成標準**：
  - <bullet 1>
  - <bullet 2>
  - <bullet 3-5>
- **重要禁忌**：<不可動 backend / 不可動 5173 / 不可寫超出 scope 的元件 等>
- **參考文件**：<frontend/IMPLEMENTATION.md §X、HANDOFF.md §X 等>
```

#### 為何不把完整 DISPATCH 內容複製進 PROGRESS？

- DISPATCH 本身已是當前任務的單一入口，前端 Agent 隨時可讀
- 完整內容進 PROGRESS 會讓檔案肥胖、且 DISPATCH ↔ PROGRESS 兩處有內容、可能不同步
- 「進行中」段的摘要足夠讓未來閱讀者（含跨 session 的自己）掌握當下脈絡
- 若需回溯歷史完整 DISPATCH，靠 `git log frontend/DISPATCH.md`

#### 完成後的處理

1. 從「進行中」搬到「已完成任務」
2. 加上 commit hash 與一句話結果敘述
3. 若 dispatch 過程中發現新缺口或後端需求，分別寫進「已知缺口」與「後端需求清單」
4. **不修改 DISPATCH.md**（即使任務完成）— DISPATCH 由主 Agent 維護，下次新任務時覆寫

---

## 7. HANDOFF.md 機制

### 7.1 性質

- **不是一次性交接文件**，而是**持續更新**的後端狀態鏡像
- 主 Agent 每次分配前端任務前，**必須**先確認此檔反映最新後端狀態
- 前端 Agent **每次 session 啟動**都要讀最新版（不要假設仍是上次內容）

### 7.2 預期內容（由主 Agent 決定格式，前端 Agent 只讀不寫）

- 目前可用的後端 API endpoint 清單（含 path / method / response schema）
- 目前的 DB schema（patient / study / series / instance 四表狀態）
- 已知但尚未實作的後端 endpoint（如 AI mask 真實版）
- 後端 base URL、CORS allowed origins、env var 變更通知
- 重大 backend 變更（如新增 migration、改變 response 欄位）

### 7.3 前端 Agent 對此檔的行為

- ✅ 讀取、引用、做為任務開展的依據
- ❌ 修改、刪除、補欄位（屬於主 Agent 職責）

---

## 8. DISPATCH.md 機制

### 8.1 性質

- **當前任務交付的單一入口** — 主 Agent 派發新任務時**整檔覆寫**，不累積歷史
- 前端 Agent 每次啟動必讀（與 HANDOFF 同層級必要性）
- 完成的舊任務歷史**不留**在 DISPATCH，而是流動到 `PROGRESS.md`「已完成任務」段

### 8.2 預期內容（由主 Agent 維護）

- frontmatter：`issued` / `issued_by` / `task_id` / `status`
- 任務目標與具體工作
- 相關 API（指向 HANDOFF.md 的對應段）
- **相關深入文件**（指引前端 Agent 何時該載入 §1.2 的按需查閱文件；若不需要也要明寫「無」）
- 注意事項（含禁忌、scope 邊界）
- 完成標準（checklist）
- 驗證步驟
- 回報格式

### 8.3 前端 Agent 對此檔的行為

- ✅ 讀取、依其內容開始工作
- ✅ 完成後在 `PROGRESS.md` commit 寫上引用（commit hash / task_id）
- ❌ **不修改 DISPATCH.md**，即使任務完成、即使想加註解
- ❌ **不依賴 DISPATCH 歷史版本** — 若主 Agent 新覆寫一份，舊任務在 PROGRESS「已完成」應已完成記錄

### 8.4 如何辨識「最新版 DISPATCH」

- 看 frontmatter 的 `issued` 日期
- 看 frontmatter 的 `status`（`active` / `completed` / `superseded`）
- 對照 `PROGRESS.md`「進行中」段是否引用同一個 `task_id`
- 不確定時：問主 Agent

---

## 9. SESSION_HISTORY.md 規則

### 9.1 性質

- **跨 session 工作記憶** — 讓「下次 session 起手能無縫接續」
- 由**前端 Agent 自己維護**（與主 Agent 維護的 SESSION_HISTORY（根目錄）對稱）
- 與 `PROGRESS.md` 互補：PROGRESS 是進度追蹤、SESSION_HISTORY 是當下脈絡記憶

### 9.2 結構（建議區塊）

```markdown
## 系統現況         ← 一段話，前端目前狀態（檔案結構、套件版本、目前能做到的事）
## 進行中的任務     ← 與 PROGRESS 進行中段對應，但偏 session 視角（什麼正在 in-flight）
## 已完成里程碑     ← 精選大事，不是所有完成項目（避免與 PROGRESS 「已完成任務」重複）
## 待決定事項       ← 前端視角的懸而未決（PROGRESS 不一定記）
## 上次 session 結尾狀態  ← 改了什麼、commit 狀態、下次起手建議
```

### 9.3 更新時機

- **每次 session 結束前**（推薦），或
- 完成一個 dispatch 任務後

### 9.4 更新原則

- 只更新有變動的區塊，不重寫整檔
- 不記錄對話流水帳，只記錄狀態與結論
- 系統現況應隨重大變動同步（如新套件、新元件、新阻擋）
- 「結尾狀態」段每次必更新

### 9.5 主 Agent 對此檔的行為

- ✅ 可讀（理解前端目前 mental state、規劃下次 dispatch）
- ❌ **不寫**（除非緊急修正過時資訊，且需在 commit message 說明）

### 9.6 第一版誰寫？

**前端 Agent 第一次收到 dispatch 收尾時自己寫**。主 Agent 不預先 seed。

---

## 10. 與根 CLAUDE.md 的關係

### 10.1 繼承關係

本檔**繼承**根 [`../CLAUDE.md`](../CLAUDE.md) 的所有通用規則，包含但不限於：

| 根 CLAUDE.md 章節 | 仍適用於前端 |
|---|---|
| §2 核心原則 | ✅ 全部適用 |
| §3 最小修改原則 | ✅ 全部適用 |
| §4 Patch-First 開發模式 | ✅ 修改既有檔案用 diff、新增檔案才整檔輸出 |
| §8 輸出規範 | ✅ 修改時須附「分析 / 計畫 / 風險」 |
| §9 安全性與穩定性 | ✅ Input validation 概念在前端也適用（如 URL 參數、user input） |
| §10 AI 行為控制規範（含 v1.1 新增的「任務完成前的最後檢查」） | ✅ 全部適用 |

### 10.2 本檔補充 / 限縮的部分

- §1-§3 限縮：適用範圍縮小到 `frontend/`
- §4-§9 補充：前端特有的協作流程與檔案機制
- §11 補充：列出待主 Agent 決定的前端規範

### 10.3 衝突處理

當本檔規則與根 CLAUDE.md 不一致時，**以根 CLAUDE.md 為準**。發現此情況時應**立即回報主 Agent**，由工程師裁示是否修訂本檔。

---

## 11. 待補充規範（TODO）

以下為**目前未定案**的前端規範。前端 Agent 遇到相關決策時，**必須回報主 Agent 判斷，不可自行決定**。

- [ ] **UI/UX 規範** — 色系、字型、元件庫、設計系統、深色 / 淺色模式
- [ ] **瀏覽器相容性** — 支援 Chrome / Edge / Firefox / Safari 的最低版本
- [ ] **效能規範** — bundle size 上限、首屏 loading 時間上限、Cornerstone canvas 渲染 FPS 目標
- [ ] **無障礙規範** — 醫療系統建議符合 WCAG 2.1 AA（語意 HTML、ARIA、鍵盤導航、色彩對比）
- [ ] **錯誤呈現規範** — toast / modal / inline error 的使用情境劃分
- [ ] **i18n 規範** — 目前 MVP 假設繁中即可，若日後需多語系再定
- [ ] **單元測試 / E2E 測試** — 是否導入 Vitest / Playwright，覆蓋率門檻

> 上列項目未定案前，前端 Agent 若遇到相關決策（如「要不要用 MUI」「要不要支援 IE11」），**先停下、回報主 Agent**，不可自行決定。

---

## 12. 文件維護

| 項目 | 說明 |
|---|---|
| 文件版本 | v1.0 |
| 建立日期 | 2026-05-13 |
| 適用對象 | 所有 AI coding agent 在 `frontend/` 內工作的 session |
| 更新觸發條件 | 前後端分工機制變更、待補充規範定案、新增前端關鍵約束 |
| 更新方式 | 工程師發起 + review，AI 不可自行修改 |

> ⚠️ **本檔受保護**：前端 Agent 不可自行修改本檔，所有修改必須由工程師發起並 review（與根 CLAUDE.md 相同的保護等級）。
