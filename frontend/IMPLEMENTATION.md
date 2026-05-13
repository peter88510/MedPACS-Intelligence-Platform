---
docspec: "1.0"
type: ARCHITECTURE
title: "MedPACS Frontend Architecture"
version: "0.1.0"
status: "design"
---

# MedPACS Frontend Architecture

> **文件定位**：本檔記錄前端的**架構與實作細節**。
>
> - 想知道「**怎麼啟動跑起來**」 → 看 [`README.md`](./README.md)
> - 想知道「**整體 MVP 規劃**」 → 看 [`../PLAN.md`](../PLAN.md) §10
> - 想知道「**後端架構**」 → 看 [`../IMPLEMENTATION.md`](../IMPLEMENTATION.md)
> - 想知道「**目前進度**」 → 看 [`../PROGRESS.md`](../PROGRESS.md)
>
> **狀態標記**：⚪ Planned / 🟡 In progress / ✅ Done

---

## 目錄

1. [Frontend 在系統中的角色](#1-frontend-在系統中的角色)
2. [整體架構](#2-整體架構)
3. [元件樹](#3-元件樹)
4. [元件詳述](#4-元件詳述)
5. [狀態管理](#5-狀態管理)
6. [API Client](#6-api-client)
7. [CornerstoneJS 整合計畫](#7-cornerstonejs-整合計畫)
8. [完整渲染流程](#8-完整渲染流程)
9. [預期最終檔案結構](#9-預期最終檔案結構)
10. [開發順序建議](#10-開發順序建議)
11. [Non-goals（明確不做）](#11-non-goals明確不做)

---

## 1. Frontend 在系統中的角色

```
[User Browser]
     │
     │  HTTP/JSON  +  DICOM binary  +  PNG mask
     ▼
[Frontend (this dir)]                     [Backend (../)]
 React + Vite                              FastAPI
 CornerstoneJS DICOM viewer    ◀────────▶  pydicom parser
 4 components                              PostgreSQL
 ~500-800 lines TS/TSX                     local file storage
                                           AI inference (stub for MVP)
```

**邊界明確**：
- Frontend **只**負責「呈現」與「使用者互動」
- 所有 DICOM 檔解析、儲存、查詢都在 backend
- Frontend 透過 7 個 API endpoint 跟 backend 對話（見 [§6](#6-api-client)）

---

## 2. 整體架構

### 2.1 畫面（單頁式 SPA）

```
┌────────────────────────────────────────────────────────────────────┐
│ TopBar — 「MedPACS Intelligence Platform v2.0」                   │
├──────────────┬─────────────────────────────────┬───────────────────┤
│              │                                 │ MetadataPanel     │
│ StudyList    │                                 │  ────────────     │
│              │                                 │  PatientID: P001  │
│ ▶ Study #1   │                                 │  StudyUID: 1.2.3  │
│   Study #2   │     DicomViewer                 │  Modality: US     │
│   Study #3   │     (Cornerstone canvas)        │  Rows: 512        │
│              │                                 │  Columns: 512     │
│              │     - 縮放 / 拖移               │  ...              │
│              │     - Window/Level              │ ──────────────────│
│              │                                 │ AIPanel           │
│              │     + AI mask 半透明疊加        │                   │
│              │       (toggle 顯示/隱藏)        │  [Run AI]         │
│              │                                 │  status: idle     │
│              │                                 │  confidence: --   │
└──────────────┴─────────────────────────────────┴───────────────────┘
```

**Layout**：CSS Grid，三欄式（左 20% / 中 60% / 右 20%）。

### 2.2 資料流向

```
                       ┌─────────────────┐
                       │  AppContext     │ ← 全域狀態
                       │  (5 個欄位)     │
                       └────────┬────────┘
                                │
        ┌───────────────────────┼────────────────────────┐
        │                       │                        │
        ▼                       ▼                        ▼
┌──────────────┐       ┌────────────────┐       ┌────────────────┐
│  StudyList   │       │  DicomViewer   │       │ MetadataPanel  │
│              │       │                │       │   AIPanel      │
│  讀 studies  │       │  讀 currentInst│       │  讀 currentInst│
│  寫 currentSt│       │  讀 aiResult   │       │  寫 aiResult   │
└──────┬───────┘       └────────┬───────┘       └────────┬───────┘
       │                        │                        │
       ▼                        ▼                        ▼
   GET /studies          GET /instances/         POST /ai/segment
                            {id}/file            GET /ai/result
                                                 GET /ai/result/{id}/mask
                                │                        │
                                ▼                        ▼
                         ┌────────────────┐       ┌────────────────┐
                         │   Backend      │       │   Backend AI   │
                         └────────────────┘       └────────────────┘
```

---

## 3. 元件樹

```
<App>
 ├── <AppContextProvider>              ← Context 包整個 app
 │    ├── <TopBar />                   ← 標題列（無互動）
 │    │
 │    ├── <Layout>                     ← Grid 三欄容器
 │    │    ├── <StudyList />           ← 左欄
 │    │    ├── <DicomViewer />         ← 中央
 │    │    └── <RightPanel>            ← 右欄容器
 │    │         ├── <MetadataPanel />
 │    │         └── <AIPanel />
```

**元件總數：4 個業務元件 + 3 個結構元件（App/Layout/TopBar）+ 1 個 Provider = 8 個 .tsx 檔**。

---

## 4. 元件詳述

### 4.1 `<StudyList />` ⚪ Planned

**職責**：列出所有 studies，使用者點擊 → 切換中央顯示。

**Props**：無（從 Context 拿 state）

**從 Context 讀**：
- `studies: Study[]`
- `currentStudyId: number | null`

**Context 寫**：
- `setCurrentStudyId(id)`

**呼叫 API**：
- `GET /studies`（在 `<AppContextProvider>` 掛載時拉一次，元件本身不打）

**狀態相依**：點擊 study → 同時觸發自動選 series 與 instance（見 [§8](#8-完整渲染流程)）

**最簡實作（伪代码）**：
```tsx
export function StudyList() {
  const { studies, currentStudyId, setCurrentStudyId } = useAppContext()
  return (
    <ul className="study-list">
      {studies.map(s => (
        <li
          key={s.id}
          className={s.id === currentStudyId ? 'active' : ''}
          onClick={() => setCurrentStudyId(s.id)}
        >
          Study {s.id} ({s.study_instance_uid})
        </li>
      ))}
    </ul>
  )
}
```

---

### 4.2 `<DicomViewer />` ⚪ Planned

**職責**：用 CornerstoneJS 渲染目前選中 instance 的 DICOM；提供 zoom / pan / window-level；在 `aiResult.mask_url` 存在時疊加半透明 mask。

**Props**：無

**從 Context 讀**：
- `currentInstanceId: number | null`
- `aiResult: AIResult | null`

**呼叫 API**：
- `GET /instances/{id}/file`（透過 Cornerstone `wadouri:` scheme，**Cornerstone 內部自己 fetch**，不是用 `fetch()`）
- `GET /ai/result/{id}/mask`（mask 圖片）

**內部狀態**（local `useState`，不進 Context）：
- `renderingEngine: cornerstone.RenderingEngine | null`
- `viewport: cornerstone.StackViewport | null`

**生命週期**：
```
mount      → 建立 RenderingEngine + Viewport + element
            → 第一次 enable / setup viewport
update     → currentInstanceId 變了 → viewport.setStack([wadouri:...])
            → aiResult 變了      → 切 mask overlay 顯示
unmount    → renderingEngine.destroy()
```

**這是整個前端最複雜的元件**。CornerstoneJS 設定佔大部分（見 [§7](#7-cornerstonejs-整合計畫)）。

---

### 4.3 `<MetadataPanel />` ⚪ Planned

**職責**：顯示目前選中 instance 的 metadata。

**Props**：無

**從 Context 讀**：
- `currentInstanceId: number | null`

**呼叫 API**：
- `GET /instances/{id}/metadata`（在 `currentInstanceId` 變更時觸發）

**內部狀態**：
- `metadata: Record<string, unknown> | null`
- `loading: boolean`
- `error: Error | null`

**最簡實作**：
```tsx
export function MetadataPanel() {
  const { currentInstanceId } = useAppContext()
  const [metadata, setMetadata] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    if (!currentInstanceId) return
    fetchInstanceMetadata(currentInstanceId).then(setMetadata)
  }, [currentInstanceId])

  if (!metadata) return <div>Select a study</div>
  return (
    <table>
      {Object.entries(metadata).map(([k, v]) => (
        <tr key={k}><td>{k}</td><td>{String(v)}</td></tr>
      ))}
    </table>
  )
}
```

---

### 4.4 `<AIPanel />` ⚪ Planned

**職責**：「Run AI」按鈕 + 狀態顯示 + mask overlay toggle。

**Props**：無

**從 Context 讀 / 寫**：
- 讀 `currentInstanceId`、`aiResult`
- 寫 `setAiResult(result)`

**呼叫 API**：
- `POST /ai/segment/{id}` → 觸發推論
- `GET /ai/result/{id}` → 拿結果

**最簡實作**：
```tsx
export function AIPanel() {
  const { currentInstanceId, aiResult, setAiResult } = useAppContext()
  const [loading, setLoading] = useState(false)

  async function handleRun() {
    if (!currentInstanceId) return
    setLoading(true)
    try {
      await postAiSegment(currentInstanceId)            // 觸發
      const result = await getAiResult(currentInstanceId) // 拿結果（MVP 同步、無 polling）
      setAiResult(result)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <button onClick={handleRun} disabled={loading || !currentInstanceId}>
        {loading ? 'Running...' : 'Run AI'}
      </button>
      {aiResult && (
        <div>
          <div>Status: {aiResult.status}</div>
          <div>Confidence: {aiResult.confidence ?? '-'}</div>
        </div>
      )}
    </div>
  )
}
```

> **MVP 簡化**：MVP 不做 polling，假設 backend `POST /ai/segment` 同步完成。Backend stub 確實也是同步回 `{"status": "queued"}` 然後立刻 `/ai/result` 可拿到（雖然目前是 mock）。Phase 3 真正接 PyTorch 推論時若仍同步、且 < 30s 完成，可繼續這個寫法；超過則需改為 polling。

---

## 5. 狀態管理

### 5.1 為何用 Context 而不是 Redux

- **狀態只有 5 個欄位**、邏輯簡單，Redux 是 overkill
- **單頁無路由**，不需要 URL synced state
- **無 server-state caching 需求**（資料量小、不重複 fetch）

### 5.2 AppContext shape

```tsx
type Study = {
  id: number
  study_instance_uid: string
  patient_id?: string
  modality?: string
}

type AIResult = {
  instance_id: number
  status: 'queued' | 'running' | 'completed' | 'failed'
  mask_url: string | null
  confidence: number | null
  model_name: string
}

type AppContextValue = {
  // Data
  studies: Study[]
  currentStudyId: number | null
  currentSeriesId: number | null
  currentInstanceId: number | null
  aiResult: AIResult | null

  // Setters
  setCurrentStudyId: (id: number | null) => void
  setAiResult: (result: AIResult | null) => void
}
```

### 5.3 啟動時資料載入順序

```
1. <AppContextProvider> mount
2. useEffect → fetch /studies → setStudies()
3. useEffect (依 studies) → 若有 studies，setCurrentStudyId(studies[0].id)
4. useEffect (依 currentStudyId) → fetch /series for this study → 取第一個 series
5. useEffect (依 currentSeriesId) → fetch /instances for this series → 取第一個 instance
6. 此時 currentInstanceId 已 set，<DicomViewer> 與 <MetadataPanel> 各自反應
```

> 注意：backend 的 `/studies` 目前只回每個 study 一筆紀錄，沒有 nested series/instances。要拿 series 列表需 `/series` 或 `/instances`，但這些 endpoint 還沒有「by study」的版本。**這是 MVP 已知缺口之一**，會在 Phase 2 task #8 接通時補；暫時用 hack：fetch 所有 instances、用 `study_instance_uid` 過濾。

---

## 6. API Client

### 6.1 設計原則

- **集中於 `src/api/`** — 不直接在元件裡 `fetch()`
- **每個 endpoint 一個函數** — function name = backend handler name 對照
- **TypeScript 型別共享** — `src/api/types.ts` 定義所有 response shape
- **錯誤處理統一** — `client.ts` 提供 fetch wrapper，HTTP 非 2xx 拋 `ApiError`

### 6.2 預期檔案

```
src/api/
├── client.ts        ← fetch wrapper、ApiError、base URL
├── types.ts         ← Study / AIResult / ... 共享型別
├── studies.ts       ← fetchStudies()
├── instances.ts     ← fetchInstance / fetchInstanceMetadata / instanceFileUrl
├── series.ts        ← fetchSeries
└── ai.ts            ← postAiSegment / getAiResult / aiMaskUrl
```

### 6.3 範本（`client.ts`）

```tsx
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  constructor(public status: number, public body: string) {
    super(`API ${status}: ${body}`)
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init)
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json() as Promise<T>
}

export function apiUrl(path: string): string {
  return `${API_BASE}${path}`
}
```

### 6.4 7 個函數對應 backend handler

| 前端函數 | HTTP | 後端 handler |
|---|---|---|
| `fetchStudies()` | `GET /studies` | `main.py:list_studies` |
| `fetchSeries(id)` | `GET /series/{id}` | `main.py:get_series` |
| `fetchInstance(id)` | `GET /instances/{id}` | `main.py:get_instance` |
| `fetchInstanceMetadata(id)` | `GET /instances/{id}/metadata` | `main.py:get_instance_meta` |
| `instanceFileUrl(id)` | `GET /instances/{id}/file` | `main.py:download_instance_file` |
| `postAiSegment(id)` | `POST /ai/segment/{id}` | `main.py:ai_segment`（stub） |
| `getAiResult(id)` | `GET /ai/result/{id}` | `main.py:ai_result`（stub） |
| `aiMaskUrl(id)` | `GET /ai/result/{id}/mask` | （Backend 尚未實作） |

> `instanceFileUrl` 與 `aiMaskUrl` **不打 fetch**，只回傳完整 URL — Cornerstone / `<img>` 自己會 fetch。

---

## 7. CornerstoneJS 整合計畫

### 7.1 整合分三階段

| Stage | 內容 | 狀態 |
|---|---|---|
| A | `npm install` 4 個套件 + smoke test | ✅ Done（commit `83b8c9a`） |
| B | `cornerstone.init()` + dicom-image-loader configure + worker config | ⚪ Planned |
| C | 第一個 DICOM 在 viewport 上渲染 | ⚪ Planned |

### 7.2 Stage B 預期工作

**新增**：`src/cornerstone/setup.ts`

```tsx
import { init as csInit } from '@cornerstonejs/core'
import { init as dicomImageLoaderInit } from '@cornerstonejs/dicom-image-loader'

let initialized = false

export async function initCornerstone() {
  if (initialized) return
  await csInit()
  await dicomImageLoaderInit({
    maxWebWorkers: navigator.hardwareConcurrency || 1,
    // ... 其他 worker / wasm 設定
  })
  initialized = true
}
```

呼叫點：`main.tsx` 啟動時呼叫一次，**早於** React render。

**可能需動 `vite.config.ts`**：
- 加 `optimizeDeps.exclude` 排除某些 Cornerstone deps（v3 對 esbuild 預打包不友善的問題已知）
- 設定 worker 處理器（如 `worker.format = 'es'`）
- 開 CORS for cross-origin DICOM URLs（本專案 same-origin 不需）

> 這是 PLAN §12 標註的「v3 整合風險、預留 1 天 buffer」。Stage B 可能會有反覆試錯。

### 7.3 Stage C 預期工作

**修改**：`<DicomViewer />` 完整實作

```tsx
useEffect(() => {
  if (!currentInstanceId || !elementRef.current) return

  const renderingEngine = new RenderingEngine('myEngine')
  const viewport = renderingEngine.enableElement({
    viewportId: 'CT_AXIAL',
    type: ViewportType.STACK,
    element: elementRef.current,
  })

  const imageId = `wadouri:${instanceFileUrl(currentInstanceId)}`
  viewport.setStack([imageId])
  viewport.render()

  return () => renderingEngine.destroy()
}, [currentInstanceId])
```

關鍵字 `wadouri:` 告訴 Cornerstone 用 dicom-image-loader 去 fetch 該 URL。

---

## 8. 完整渲染流程

從「使用者點擊 study」到「mask 出現在影像上」的完整 call chain：

```
1. User 點 <StudyList> 的 Study #2
        │
        ▼
2. setCurrentStudyId(2)        ← Context state 變更
        │
        ▼
3. useEffect 觸發 → fetchSeries() → 取第一個 series → setCurrentSeriesId()
        │
        ▼
4. useEffect 觸發 → fetchInstances by series → 取第一個 instance → setCurrentInstanceId()
        │
        ├──→ <DicomViewer> useEffect 觸發
        │       │
        │       ▼
        │    viewport.setStack([wadouri:.../instances/123/file])
        │       │
        │       ▼
        │    Cornerstone 內部 GET /instances/123/file → 解析 → 畫到 canvas
        │
        └──→ <MetadataPanel> useEffect 觸發
                │
                ▼
             fetchInstanceMetadata(123) → setMetadata() → 畫表格

5. User 點 <AIPanel> 的 [Run AI]
        │
        ▼
6. POST /ai/segment/123 → 等回應 → GET /ai/result/123 → setAiResult()
        │
        ▼
7. <DicomViewer> useEffect (依 aiResult) → 在 viewport 加 mask overlay layer
        │
        ▼
8. 半透明 mask 顯示在 DICOM 影像上
```

---

## 9. 預期最終檔案結構

Phase 2 完成時 `frontend/src/` 應該長這樣：

```
src/
├── main.tsx                          ← 程式入口（呼叫 initCornerstone + render <App>）
├── App.tsx                           ← 最外層（包 Provider + Layout）
├── App.css                           ← App 容器樣式
├── index.css                         ← 全域樣式（重置 / 字型）
│
├── components/                       ← 所有 UI 元件
│   ├── TopBar.tsx
│   ├── TopBar.module.css
│   ├── Layout.tsx
│   ├── Layout.module.css
│   ├── StudyList.tsx
│   ├── StudyList.module.css
│   ├── DicomViewer.tsx
│   ├── DicomViewer.module.css
│   ├── MetadataPanel.tsx
│   ├── MetadataPanel.module.css
│   ├── AIPanel.tsx
│   └── AIPanel.module.css
│
├── context/                          ← React Context
│   ├── AppContext.tsx                ← Provider + hook (useAppContext)
│   └── types.ts                      ← Context value 型別
│
├── api/                              ← API client（見 §6）
│   ├── client.ts
│   ├── types.ts
│   ├── studies.ts
│   ├── series.ts
│   ├── instances.ts
│   └── ai.ts
│
├── cornerstone/                      ← CornerstoneJS 整合
│   └── setup.ts                      ← initCornerstone()（見 §7.2）
│
└── assets/                           ← 靜態素材（圖示等）
```

**總計約 25 個檔案**，~500-800 行 TS/TSX。

---

## 10. 開發順序建議

依依賴度排序：

```
1. CornerstoneJS Stage B (cornerstone/setup.ts)        ← 阻擋 viewer
2. API client (src/api/*)                              ← 元件都依賴
3. AppContext (src/context/AppContext.tsx)             ← 元件都依賴
4. Layout + TopBar (結構元件)                          ← 中層
5. StudyList                                            ← 最簡單，先讓「列表能看」
6. MetadataPanel                                        ← 純展示，次簡單
7. CornerstoneJS Stage C — <DicomViewer>               ← 最複雜
8. AIPanel                                              ← 依賴 viewer 才有意義
9. CSS 細修 + responsive                                ← 最後
```

> 為什麼 viewer 不先做？因為 viewer 沒有 study/instance state 就沒有東西可渲染。先把資料流打通、列表能看、metadata 顯示，**再**處理 viewer 比較不會迷失方向。

---

## 11. Non-goals（明確不做）

| 不做 | 為什麼 |
|---|---|
| Router（react-router） | SPA 單頁、無需 |
| Redux / Zustand / Recoil | Context 足夠 |
| TanStack Query | 資料量小、無需 cache layer |
| 認證 / 登入頁面 | PLAN §3 排除 |
| 多語系 i18n | MVP 中文寫死即可（介面字詞少） |
| 響應式（手機 / 平板） | MVP 假設 desktop only，CornerstoneJS 也是桌面取向 |
| 上傳介面 | 已知缺口 — MVP 用 curl / Postman 上傳，frontend 不做 |
| 多 study 同時打開 | 一次一個 study |
| 多模型結果比較 | 單模型 stub |
| 標註工具 | 超出 MVP |
| 暗色模式 / 主題切換 | YAGNI |

---

## 文件維護

| 項目 | 說明 |
|---|---|
| 文件版本 | v0.1.0（Phase 2 task #8 起手） |
| 建立日期 | 2026-05-13 |
| 更新觸發條件 | 元件清單變更 / API client 結構變更 / Cornerstone 整合方式變更 |
| 更新方式 | PR + 工程師 review |
| 與 root IMPLEMENTATION.md 關係 | root 含摘要 + 指向本檔；本檔負責 frontend 內部詳述 |
