---
issued: 2026-05-14
issued_by: 主 Agent
task_id: phase-2-task-8-stage-c
status: active
---

# 當前任務 — CornerstoneJS Stage C（第一張 DICOM 渲染）

> **本檔機制**：本檔是**當前任務**的單一入口。主 Agent 派發新任務時會**整檔覆蓋**，不累積歷史。歷史請看 `frontend/PROGRESS.md` 的「已完成任務」段與 git commit log。
>
> **前端 Agent 啟動時必讀**（見 `frontend/CLAUDE.md` §1）。
>
> **修改規則**：前端 Agent **不修改本檔**；只讀。新版本由主 Agent 覆寫。

---

## 任務

### 目標

Stage C — **以 hardcoded instance ID + wadouri scheme，從 `GET /instances/{id}/file` 拉一張 DICOM、在 `<DicomViewer />` 元件內渲染**。範圍刻意縮小到「能看到圖」即過關。

完成後即可進入 Phase 2 task #9（API client + AppContext + 4 個業務元件）。

### 主 Agent 已拍板的決策（前端 Agent 不必再問）

- **Stage C 範圍**：純 viewer 起手。**不做** API client、AppContext、StudyList、MetadataPanel、AIPanel — 這些屬下一個 dispatch
- **CSS 方法**：CSS Modules（`*.module.css`），符合 `frontend/docs/IMPLEMENTATION.md` §9 預期
- **API base URL**：本 dispatch **暫時 hardcode** 為 `http://localhost:8000`。`VITE_API_BASE_URL` env var 制度於下個 dispatch 才正式導入（避免本任務 scope creep）

### 具體工作

1. **新增 `frontend/src/components/DicomViewer/DicomViewer.tsx`**
   - 接受 props `{ instanceId: number }`
   - 使用 `useRef<HTMLDivElement>` 取容器 element
   - 在 `useEffect` 內：
     - 建立 `RenderingEngine`（id 自取，建議含 `Date.now()` 或固定 id + cleanup destroy 避 StrictMode 雙 mount 衝突）
     - 建立 `StackViewport`（element 用 ref.current）
     - 建立 `imageId`：`` `wadouri:http://localhost:8000/instances/${instanceId}/file` ``
     - `viewport.setStack([imageId])`
     - `viewport.render()`
   - `useEffect` 的 cleanup：destroy RenderingEngine，避免記憶體洩漏與 StrictMode 雙 mount 衝突

2. **新增 `frontend/src/components/DicomViewer/DicomViewer.module.css`**
   - container 設明確尺寸（例：`width: 100%; height: 600px;` 或 `min-height: 600px`）— Cornerstone canvas 需明確尺寸才會 layout
   - 黑底（醫療影像慣例）

3. **修改 `frontend/src/App.tsx`**
   - 取代 Vite scaffold 內容
   - render `<DicomViewer instanceId={<工程師提供的 DB id>} />`
   - **hardcoded ID 由工程師上傳一張 DICOM 後告知**（見「驗證步驟」第 1-2 步）；前端 Agent 先把它寫成常數，例 `const INSTANCE_ID = 1;` 並在註解標「工程師驗收時替換」

4. **重啟 `npm run dev`**，驗證 PowerShell + 瀏覽器 DevTools console 皆乾淨

---

## 相關 API

| Endpoint | 用法 | 來源 |
|---|---|---|
| `GET /instances/{id}/file` | 回 `application/dicom` 二進位 — dicom-image-loader 透過 `wadouri:` scheme 拉取 | `HANDOFF.md` §1 / §3.4；完整 spec 見 `docs/generated/api_spec.md` |

> 本 stage **不**呼叫其他 endpoint。不需 fetch `/studies`、不需 `/instances/{id}`、不需 metadata。下個 dispatch 才需要。

---

## 相關深入文件

- **必查**：`frontend/docs/IMPLEMENTATION.md` — DicomViewer 元件設計、Cornerstone 整合計畫（Stage A/B/C 段落）
- **引用**：`frontend/context/HANDOFF.md` §3（API 補充說明）、`docs/generated/api_spec.md`（GET /instances/{id}/file spec 權威來源）
- **背景參考**：`docs/PLAN.md` §12（Cornerstone 整合風險點：v3+ 對 esbuild 預打包不友善、wasm / worker 邊界）

---

## 注意事項

### 已知技術陷阱

1. **Vite StrictMode 雙 mount**：`main.tsx` 預設用 `<React.StrictMode>` 包裹 → useEffect 會 run twice → RenderingEngine 同 id 衝突。對策：
   - **首選**：每次 mount 用 deterministic id（如 `'mainEngine'`），cleanup destroy；下次 mount 重建
   - **次選**：用 `Date.now()` 隨機 id（但 cleanup 一樣要 destroy）
   - **不可**：在 module scope 建 RenderingEngine（會綁全域）

2. **Cornerstone 物件不進 React state**（承襲 Stage B 注意事項 #7、PLAN §12）— 一律 useRef 或 module-level singleton（`initCornerstone()` 已是 singleton）

3. **若遇 wasm / worker / cors 問題**，debug 順序（同 Stage B 預演）：
   - `optimizeDeps.exclude` → `worker.format='es'` → `assetsInclude` → 最後才考慮版本鎖
   - 真的要動 `vite.config.ts` 超過 5 行 → 在 PROGRESS 進行中段說明理由

4. **`viewport.render()` 是同步 call 但 image load 是非同步**：第一次 render 可能看不到圖（image 還沒下載完）。Cornerstone 內建會在 image loaded 後 auto-rerender；如果沒看到圖、先檢查 Network tab 是否 200 拿到 DICOM、Console 是否有 cornerstone 的 image load event log

### Scope 邊界（禁忌）

- ❌ 不可動 backend 任何檔案（含 `main.py` CORS、`models.py`、`alembic/`）
- ❌ 不可動 `vite.config.ts` 中 `server.port = 5173`（後端 CORS 對齊）
- ❌ 不可寫 API client / AppContext / StudyList / MetadataPanel / AIPanel（下個 dispatch）
- ❌ 不可自行下載 sample DICOM；若工程師沒有可上傳的 DICOM → **暫停、回報主 Agent**（不要自己用 pydicom-data 或網路 sample，那是 `docs/PLAN.md` §14 + 根 `SESSION_HISTORY.md` 待決定事項 #2，需主 Agent 拍板）
- ❌ 不可加 zoom / pan / window-level 互動工具（屬 Phase 2 task #9 範圍）
- ❌ 不可修改 `frontend/context/DISPATCH.md`（本檔）
- ❌ 不可動 backend env var；前端目前不需任何 env var（暫 hardcode API URL）

---

## 完成標準

### 必須全部成立

- [ ] `frontend/src/components/DicomViewer/DicomViewer.tsx` 存在、export default 元件、接受 `instanceId: number` props
- [ ] `frontend/src/components/DicomViewer/DicomViewer.module.css` 存在、container 有明確尺寸與黑底
- [ ] `frontend/src/App.tsx` 改寫為 render `<DicomViewer instanceId={...} />`，hardcoded 常數含「工程師驗收時替換」註解
- [ ] `npm run dev` 啟動，PowerShell 無 error / warning
- [ ] 瀏覽器 `http://localhost:5173` 開啟，DevTools console 無 red error，**且 viewport 顯示 DICOM 影像**（工程師驗收）
- [ ] `frontend/PROGRESS.md` 已更新：
  - 收到此 dispatch 後在「進行中」段寫摘要（格式見 `frontend/CLAUDE.md` §6.4）
  - 完成後從「進行中」移到「已完成任務」，加 commit hash
  - 若有新發現的後端需求或缺口，加進對應區塊
- [ ] `frontend/context/SESSION_HISTORY.md` 更新：
  - A 段「進行中任務」完成後清空 / 改寫
  - A 段「待決定事項」移除 Stage C 起手點 + CSS Modules 兩項（已由主 Agent 拍板）
  - B 段「上次 session 結尾狀態」更新

### 允許但不強制

- viewport 顯示 metadata 標籤（patient name 等）— Stage C 不要求
- 多 frame 切換 — 不要求
- 任何互動工具 — 不要求

---

## 驗證步驟（工程師驗收用）

1. **準備一張 DICOM 並上傳取得 instance ID**（工程師執行；前端 Agent 不做這步）：
   ```powershell
   curl.exe -X POST http://localhost:8000/upload -F "file=@<path-to-sample.dcm>"
   ```
   Response 內取 `id` 欄位（**DB id，整數，不是 SOPInstanceUID**；見 HANDOFF §4.1）

2. 將該 ID 替換 `App.tsx` 內的 hardcoded 常數

3. `cd frontend && npm run dev`

4. 瀏覽器開 `http://localhost:5173`

5. 預期：viewport 黑底中顯示一張 DICOM 影像；F12 → Console 無 red error

6. 關閉 dev server、重啟、再次確認無 error（StrictMode 雙 mount 不會炸）

---

## 回報格式（寫進 PROGRESS 的「已完成任務」項目）

- 改動 / 新增的檔案清單（path + 大致行數）
- `vite.config.ts` 是否動到、動了什麼（若有）
- 驗收時用的 instance ID（紀錄方便重現）
- 遇到的坑（讓主 Agent 記進文件 / `frontend/docs/IMPLEMENTATION.md`）
- 新發現的後端需求 / 缺口
- 是否觸及 PLAN §12 預警的 wasm / worker / cors 邊界問題

---

## 預期下個 dispatch（Phase 2 task #9，僅供前端 Agent 心理準備）

- API client (`src/api/`)：含 `VITE_API_BASE_URL` env var 制度
- AppContext (`src/context/AppContext.tsx`)：5 欄位
- `<Layout />` + `<TopBar />` + `<StudyList />` + `<MetadataPanel />` + `<AIPanel />`
- 屆時 Stage C 的 hardcoded instanceId 改由 AppContext + StudyList 點選注入
