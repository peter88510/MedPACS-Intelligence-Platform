# MedPACS Frontend

MedPACS Intelligence Platform 的前端 viewer（React + Vite + TypeScript）。

> Phase 2 工作目錄。完整設計見 [`../PLAN.md`](../PLAN.md) §10。

---

## 目錄

1. [這份專案是什麼](#這份專案是什麼)
2. [技術棧（給前端新手的快速說明）](#技術棧給前端新手的快速說明)
3. [前置條件](#前置條件)
4. [第一次設定](#第一次設定)
5. [日常開發指令](#日常開發指令)
6. [目錄結構解析](#目錄結構解析)
7. [後端 API 對應](#後端-api-對應)
8. [常見開發動作](#常見開發動作)
9. [Phase 2 Roadmap](#phase-2-roadmap)
10. [名詞速查表](#名詞速查表)

---

## 這份專案是什麼

一個跑在瀏覽器裡的應用程式，會：

1. 透過 HTTP 向 backend（`http://localhost:8000`）拿 study / series / instance 清單
2. 用 **CornerstoneJS** 把原始 DICOM 檔渲染成可看的醫療影像
3. 提供「Run AI」按鈕觸發後端的 stub AI 分割，並把結果疊加到影像上

整個 frontend 是「**單頁應用**」（SPA）— 瀏覽器只載入一次 HTML，後續所有畫面切換都靠 JavaScript 在前端完成，**不會有換頁時的整頁重新整理**。

---

## 技術棧（給前端新手的快速說明）

| 工具 | 是什麼 | 在本專案的角色 |
|---|---|---|
| **React** | UI 函式庫，用「元件」（Component）組裝畫面 | 寫 `DicomViewer`、`MetadataPanel` 等元件 |
| **TypeScript** | JavaScript + 型別系統 | 寫程式碼時 IDE 會幫你抓型別錯誤；不影響執行 |
| **Vite** | **dev server + 打包工具** | 開發時跑 `npm run dev`，部署時跑 `npm run build` |
| **CornerstoneJS**（之後加） | DICOM 影像在瀏覽器渲染的函式庫 | 把 `.dcm` 檔變成可縮放、可拖動的影像 canvas |
| **CSS Modules**（規劃中） | CSS 局部作用域，避免樣式互相污染 | 每個元件帶自己的 `.module.css` |

### Vite 是什麼？為什麼用它？

傳統 JavaScript 專案需要把全部程式碼**打包**成一個大檔案瀏覽器才能跑（早期工具：webpack）。打包過程慢，每改一行要等好幾秒。

Vite 利用瀏覽器原生支援的 **ES Modules**：
- 開發時**不打包**，直接讓瀏覽器一個一個檔案載入 → 啟動快（這次測試 438ms）
- 修改檔案時，只重新傳送那個檔案 → 畫面立刻更新，不用整頁 reload。這叫 **HMR**（Hot Module Replacement）
- 部署時才打包成 production 可用的最小檔案

---

## 前置條件

- **Node.js**：22 LTS 以上（本機已裝 v24 在 `C:\Program Files\nodejs\`）
- **後端要在跑**：`http://localhost:8000`。前端會打 API。
  - 確認方法：另開瀏覽器訪 `http://localhost:8000/health` 應該回 `{"status": "ok", "version": "2.0"}`

---

## 第一次設定

在 repo 根目錄打開 PowerShell：

```powershell
cd frontend
npm install         # 從 package.json 讀取依賴清單、下載到 node_modules/
```

`node_modules/` 會放所有第三方套件（會很大、幾百 MB），**已被 .gitignore 排除**，不會進 git。

> ⚠️ 如果同事 / 換電腦時 clone 下來，**第一件事就是跑 `npm install`** 重建 `node_modules/`，否則啟動會失敗。

---

## 日常開發指令

| 指令 | 做什麼 | 何時用 |
|---|---|---|
| `npm run dev` | 啟動 Vite dev server（背景跑）+ 開 HMR | **寫程式時 90% 時間都是它在跑** |
| `npm run build` | 把專案打包成 `dist/`（壓縮、優化的靜態檔） | 要部署上線時 |
| `npm run preview` | 用本機 server 跑 `dist/`，模擬 production 環境 | 部署前最後驗證 |
| `npm run lint` | 跑 ESLint 檢查 code style / 常見錯誤 | 自己 review code 前 |

### `npm run dev` 詳細運作

1. PowerShell 顯示 `VITE v8.0.12 ready in XXX ms`
2. 在瀏覽器開 **`http://localhost:5173`**
3. 看到 Vite + React 預設歡迎頁（旋轉的 React logo）
4. **保持 PowerShell 開著**，server 持續運作
5. 改任何 `src/*.tsx` 檔案儲存 → 瀏覽器自動 reflect 變更（HMR）
6. 結束時 PowerShell 按 **Ctrl+C**

---

## 目錄結構解析

```
frontend/
├── index.html              ← 瀏覽器第一個載入的檔案
├── package.json            ← 專案清單：依賴、scripts、版本
├── package-lock.json       ← 精確鎖定每個依賴的版本（npm install 自動產出）
├── tsconfig.json           ← TypeScript 主設定
├── tsconfig.app.json       ← 應用程式碼的 TS 設定
├── tsconfig.node.json      ← 給 vite.config.ts 等 build tool 用的 TS 設定
├── vite.config.ts          ← Vite 設定（port、plugin、build options）
├── eslint.config.js        ← Linter 規則
├── .gitignore              ← Vite 預設產出，已正確排除 node_modules/ / dist/ / *.log
├── README.md               ← 本檔
├── node_modules/           ← 第三方套件（不進 git）
├── public/                 ← 靜態資源（不會被 build 處理）
│   └── ...                 ← e.g. favicon.svg
└── src/                    ← 你的程式碼都寫在這
    ├── main.tsx            ← 程式入口；把 React 掛到 index.html 的 <div id="root">
    ├── App.tsx             ← 最外層元件（目前是 Vite 預設範例）
    ├── App.css             ← App 的樣式
    ├── index.css           ← 全域樣式（重置、字型等）
    └── assets/             ← 圖片、SVG 等靜態素材
        └── react.svg
```

### 三個 tsconfig 為什麼？

- `tsconfig.json` 本身**不含設定**，只透過 `references` 指向另外兩份
- `tsconfig.app.json` 給你寫的 `src/*` 用（DOM、瀏覽器 API、JSX）
- `tsconfig.node.json` 給 `vite.config.ts` 用（Node 環境、不需 DOM）

這樣切分讓 IDE 知道：寫 `vite.config.ts` 時不該補 `window` 的提示，寫 `App.tsx` 時不該假設 `fs` 模組存在。

### 重點檔案位置

- **改 UI** → `src/App.tsx` 或之後新增的元件
- **改全域樣式** → `src/index.css`
- **加新元件** → `src/components/MyThing.tsx`（自己建 `components/` 資料夾）
- **加新 API 呼叫** → 之後會建 `src/api/`
- **加 npm 套件** → `npm install <package>`（會自動寫進 `package.json`）

### **不要碰** 的檔案

- `node_modules/` — npm 管理，手動改會被覆蓋
- `package-lock.json` — `npm install` 自動產出，**不要手改但要 commit**
- 任何 `tsconfig.*.json` — 除非你知道在做什麼

---

## 後端 API 對應

前端會打的所有 endpoint：

| Frontend 需要 | Backend 提供 | 用途 |
|---|---|---|
| `GET /studies` | `main.py:list_studies` | 列出所有研究 |
| `GET /series/{id}` | `main.py:get_series` | 取單一系列 |
| `GET /instances/{id}` | `main.py:get_instance` | 取單一 instance metadata |
| `GET /instances/{id}/file` | `main.py:download_instance_file` | **下載原始 DICOM** → CornerstoneJS 渲染 |
| `GET /instances/{id}/metadata` | `main.py:get_instance_meta` | 顯示在 MetadataPanel |
| `POST /ai/segment/{id}` | `main.py:ai_segment`（stub） | 觸發 AI 分割 |
| `GET /ai/result/{id}` | `main.py:ai_result`（stub） | 取分割結果 |

**API base URL 目前 hard-code 為 `http://localhost:8000`**。未來上線時會改為環境變數 `VITE_API_BASE_URL`。

### 為什麼 CORS 重要？

瀏覽器有「同源政策」(Same-Origin Policy)：JavaScript **預設不能跨 origin 打 API**。
- 前端 origin：`http://localhost:5173`
- 後端 origin：`http://localhost:8000`
- **port 不同 → 不同 origin → 被瀏覽器擋**

後端 `main.py` 加了 `CORSMiddleware` 並 allow `http://localhost:5173`，所以才能正常呼叫。詳見根目錄 `README.md` 的 **CORS (Dev)** 章節。

---

## 常見開發動作

### 我想加一個新元件

1. 在 `src/components/` 建檔，例如 `StudyList.tsx`：
   ```tsx
   export function StudyList() {
     return <div>study list 還沒做</div>
   }
   ```
2. 在需要的地方 import：
   ```tsx
   import { StudyList } from './components/StudyList'
   // ...
   <StudyList />
   ```

### 我想加一個 npm 套件

```powershell
npm install axios          # runtime 用的套件
npm install -D vitest      # 只有開發時需要（-D = devDependency）
```

`package.json` 會自動更新。記得 commit。

### 我想拉一個後端 API

之後會建立 `src/api/client.ts` 統一管理。基本範本：

```tsx
const API_BASE = 'http://localhost:8000'

export async function fetchStudies() {
  const res = await fetch(`${API_BASE}/studies`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}
```

### 我想改 port

`vite.config.ts` 加：

```ts
export default defineConfig({
  plugins: [react()],
  server: { port: 3000 },  // ← 改這
})
```

⚠️ 同時也要去後端 `main.py` 改 `CORSMiddleware` 的 `allow_origins`！否則跨域會被擋。

---

## Phase 2 Roadmap

- [x] Scaffold React + Vite + TS 專案
- [ ] **CornerstoneJS v3 整合**（task #8）
  - `npm install @cornerstonejs/core @cornerstonejs/dicom-image-loader @cornerstonejs/tools`
  - 設定 worker / wasm（這部分是 PLAN §12 標註的風險點）
- [ ] **四個核心元件**
  - `StudyList`：列出所有 study，點擊跳到該 study
  - `DicomViewer`：CornerstoneJS canvas，渲染 DICOM
  - `MetadataPanel`：顯示 instance metadata
  - `AIPanel`：「Run AI」按鈕 + 結果 overlay
- [ ] **API client**（`src/api/`）
- [ ] **AI stub endpoint 接通**

---

## 名詞速查表

| 詞 | 意思 |
|---|---|
| **Component** / 元件 | React 的最小單位，一個函數 return JSX |
| **JSX / TSX** | HTML-like 語法寫在 JS / TS 裡，編譯時轉成 `React.createElement(...)` |
| **HMR** | Hot Module Replacement — 改檔不用整頁 reload，畫面當場更新 |
| **bundler** / 打包工具 | 把多個 JS / CSS / image 檔合併最佳化（Vite 的 build 階段做這事） |
| **dev server** | 開發用的本地 HTTP server，提供 HMR、自動 reload |
| **SPA** | Single-Page Application，整個 app 在一個 HTML 裡靠 JS 動態切畫面 |
| **node_modules** | npm 下載第三方套件的存放處（不進 git） |
| **package.json** | 專案宣告檔，列出依賴、scripts、版本資訊 |
| **package-lock.json** | 精確鎖定每個依賴的版本，確保不同機器裝出一樣的東西 |
| **ESLint** | 程式碼風格 + 常見錯誤檢查器 |
| **TypeScript** | JavaScript + 靜態型別，編譯時抓錯，執行時是純 JS |
| **Vite plugin** | Vite 的擴充機制，e.g. `@vitejs/plugin-react` 啟用 React 支援 |
| **CORS** | Cross-Origin Resource Sharing — 跨 origin 呼叫 API 的瀏覽器安全機制 |
| **CornerstoneJS** | 醫療影像在瀏覽器渲染的開源函式庫，DICOM viewer 業界主流之一 |

---

## 學習資源（之後遇到問題可參考）

- [Vite 官方文件](https://vitejs.dev/) — 最權威
- [React 官方文件](https://react.dev/) — 新版（2023+）寫得很好，建議讀「Learn」段
- [CornerstoneJS docs](https://www.cornerstonejs.org/) — v3 文件，Phase 2 task #8 會大量用到
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html) — 不必通讀，遇到型別錯誤再查
