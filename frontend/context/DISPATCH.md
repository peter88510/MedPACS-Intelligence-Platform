---
issued: 2026-05-16
issued_by: 主 Agent
task_id: phase-2-task-8-stage-c-restack
status: active
supersedes: phase-2-task-8-stage-c-metadata (gate failed — see PROGRESS §4.4 Fix-2)
---

# 當前任務 — Stage C 收尾 Fix-3：在 resize 後二次 setStack 重建 actor scene

> **本檔機制**：本檔是**當前任務**的單一入口。主 Agent 派發新任務時會**整檔覆蓋**，不累積歷史。歷史請看 `frontend/PROGRESS.md` 的「已完成任務」段與 git commit log。
>
> **前端 Agent 啟動時必讀**（見 `frontend/CLAUDE.md` §1）。
>
> **修改規則**：前端 Agent **不修改本檔**；只讀。新版本由主 Agent 覆寫。

---

## 任務

### 目標

接續 Stage C 修正。Fix-2 dispatch 把 metadata-aware aspect-ratio 設對、canvas buffer 也擴對，但**影像仍縮在 container 一角不撐滿**。前端 Agent 讀 Cornerstone 4.22.6 source code 定位根因（PROGRESS §4.4 Fix-2 段詳述）：

> **`setStack` 當下、image actor 在 VTK scene 的 scaling 是依當時 canvas 尺寸鎖定的；後續 canvas 變大、`resetCameraForResize` 只重設 camera view transform、actor scene-space scale 不跟著改**

本 dispatch 採前端 Agent 提出的方向 E（最小針對性解）：**在 metadata 設好 + reflow + resize 之後，再呼叫一次 `viewport.setStack([imageId])`，讓 image actor scene 在正確 canvas 尺寸下重建**。

### 主 Agent 已拍板的決策

- **方向**：E（二次 setStack）。不採 F（ResizeObserver）/ G（image loader）/ H（暫退）
- **Cornerstone image cache**：第二次 setStack 應該 hit cache、不會二次下載 DICOM；若意外發現會二次下載、回報但不阻斷（task #9 才需要 ResizeObserver-grade 解）
- **保留所有 Fix-2 改動**：metadata 主路 + 備路 + fallback console.warn、rAF、`renderingEngine.resize(true, false)`、`resetCamera()`、`cancelled` flag、cleanup `destroy()`
- **Multi-frame 仍延後**：本 dispatch 仍只顯示第 1 frame，不做 frame UI（task #9 / Phase 3）
- **若 Fix-3 仍失敗**：停下、回報、PROGRESS §4.4 加 Fix-3 子段；**不自行升級到 F（ResizeObserver）**，主 Agent 會評估

### 具體工作

**唯一改動**：在 `frontend/src/components/DicomViewer/DicomViewer.tsx` 現有 Fix-2 代碼的 `renderingEngine.resize(true, false)` **之後、`viewport.resetCamera()` 之前**，加一行：

```ts
await viewport.setStack([imageId]);
```

完整的 init flow（關鍵步驟順序）：

```ts
// 1. First setStack — load image, populate metadata
await viewport.setStack([imageId]);
if (cancelled) return;

// 2. Get image dimensions (Fix-2 既有邏輯：metaData 主路 + viewport.getImageData 備路 + fallback warn)
let aspectRatio: string | null = ...;

// 3. Set container aspect-ratio
if (aspectRatio && containerRef.current) {
  containerRef.current.style.aspectRatio = aspectRatio;
}

// 4. Wait for browser reflow
await new Promise(r => requestAnimationFrame(r));
if (cancelled) return;

// 5. Re-buffer canvas at new container size
renderingEngine.resize(true, false);
if (cancelled) return;

// 6. ★ NEW: Second setStack — re-create image actor scene at correct canvas size
await viewport.setStack([imageId]);
if (cancelled) return;

// 7. Reset camera + render
viewport.resetCamera();
viewport.render();
```

**為什麼第二次 setStack 解問題**：
- 第一次 setStack 在「container 還是 fallback aspect-ratio (`4/3`)」的 canvas 上建立 image actor、actor 的 scene-space scale 鎖定在那個 canvas 尺寸
- 第二次 setStack 在「container 已是正確 aspect-ratio (e.g. `1640/1990`) + canvas 已 re-buffer」的環境下重建 actor、actor 的 scale 對應正確尺寸
- Cornerstone 內部 image data cache 已 hit、不會二次 fetch DICOM 檔（DISPATCH 期待如此；若 Network tab 顯示二次 GET、回報）

### 不需要做的

- ❌ 不需要動 `DicomViewer.module.css`（保留 Fix-2 既有：`width: 100%; min-height: 400px; aspect-ratio: 4/3` CSS fallback）
- ❌ 不需要動 `App.tsx` / `main.tsx` / `setup.ts` / `vite.config.ts` / backend
- ❌ 不需要動 metadata 取得邏輯（Fix-2 主路成功）
- ❌ 不需要 ResizeObserver、不需要新 React state、不需要新 hook

---

## 相關 API

無新 endpoint 呼叫。

---

## 相關深入文件

- `frontend/PROGRESS.md` §4.4 Fix-2 — 根因分析（Cornerstone GPU dispatcher 行為、VTK actors vs camera 區別、4 個方向 E/F/G/H trade-off）
- `frontend/PROGRESS.md` §4.4 Fix-1 — 前次 fit dispatch 失敗紀錄（保留歷史追溯）

---

## 注意事項

### 渲染原則（與 Fix-2 dispatch 同，重申）

- **等比縮放 + 保留原始資料**：container 比例 = image 比例 → Cornerstone WebGL fit 自然等比、無扭曲
- Cornerstone WebGL canvas **永遠等比 + 高品質 resampling**
- 不可寫自訂 image resize / canvas redraw / Image()-based hack / 修改 image data
- 原 DICOM bytes **全程不變**

### 二次 setStack 的潛在風險與處理

1. **Race condition**：兩次 setStack 之間若元件 unmount → cancelled flag 已存、會 return。但要確認**第二次 setStack 也包在 cancelled check 之後**（見上方流程第 6 步前）

2. **Image cache miss**：理論上 Cornerstone 第二次 setStack 同 imageId 應 hit cache、瞬間完成。**若 Network tab 看到二次 GET `/instances/{id}/file`** → 回報主 Agent，可能 cache 沒 hit、需評估其他方案

3. **第一次 setStack 的 actor 是否需顯式釋放**：理論上第二次 setStack 會 swap actor、不需手動釋放。若觀察到記憶體緩慢增長 → 回報

4. **Fix-2 既有行為保留**：metadata 主路 / 備路 / fallback warn 全部保留；rAF + resize + resetCamera 全部保留；StrictMode-safe 機制全部保留

### Scope 邊界（禁忌）

- ❌ 不可動 backend / vite.config.ts / main.tsx / setup.ts / DISPATCH.md
- ❌ 不可寫 API client / AppContext / 任何業務元件（task #9）
- ❌ 不可加 ResizeObserver（屬方向 F、需新 dispatch；本任務只做方向 E）
- ❌ 不可加 frame 切換 / cine / multi-frame UI
- ❌ 不可改 metadata 取得邏輯（Fix-2 主路已成功）
- ❌ 不可改 `DicomViewer.module.css`（保留 Fix-2 狀態）
- ❌ 不可改 `App.tsx` 既有的 hardcoded `INSTANCE_ID = 1`
- ❌ 不可寫自訂 resize / canvas redraw / Image() hack / 改 image data
- ❌ 不可在第二次 setStack 之外加任何 setStack 呼叫（避免無限 retrigger）

### Commit 操作

- 與既有所有未 commit 改動一起做**單一 commit**：
  ```
  M  frontend/PROGRESS.md
  M  frontend/context/SESSION_HISTORY.md
  M  frontend/src/App.tsx
  M  frontend/src/components/DicomViewer/DicomViewer.tsx        (Fix-2 + Fix-3 加一行)
  M  frontend/src/components/DicomViewer/DicomViewer.module.css (Fix-2 狀態)
  ?? frontend/src/components/                                    (Stage C 新建目錄)
  ```
- Commit message 反映完整 Stage C 歷程（主體 + Fix-1 + Fix-2 + Fix-3）
- 不拆 commit

---

## 完成標準

### 必須全部成立

- [ ] `DicomViewer.tsx` 在 `renderingEngine.resize(true, false)` 之後、`viewport.resetCamera()` 之前，加 `await viewport.setStack([imageId])` + `if (cancelled) return;`
- [ ] 其他 Fix-2 既有邏輯**不動**
- [ ] `npx tsc -b --noEmit` 通過
- [ ] `npm run dev` 啟動乾淨
- [ ] **瀏覽器以 `INSTANCE_ID=1` 開啟、影像完整填滿 container（工程師肉眼確認、無大量黑底、無切割）**
- [ ] F12 → Network tab：第二次 setStack **不應**觸發二次 `GET /instances/1/file`（若觸發、回報但不阻斷）
- [ ] F12 → Console：metadata 主路成功、無 `[DicomViewer]` warning
- [ ] 單一 commit 含 Stage C 全部累積；commit hash 回填 PROGRESS §1 + SESSION_HISTORY B 段
- [ ] PROGRESS §4.4 主段標「已解決於 commit XXX」、加 Fix-3 結果摘要子段；**保留 Fix-1 + Fix-2 子段不刪**（歷史追溯）
- [ ] 完成驗收後 TaskStop background dev server

### 允許但不強制

- 若實作中發現 cancelled check 點需微調以配合二次 setStack 的 await，可動 — 但保持 StrictMode-safe 核心邏輯
- 若工程師肉眼覺得影像「完整但偏置」（aspect 對但 camera 沒在中心），可在 `resetCamera()` 後加 `viewport.setProperties({ ... })` 微調 — 但保持 fit-to-canvas 原則

### 禁止

- ❌ 多個 commit
- ❌ 改 metadata 邏輯 / module.css / App.tsx / 任何 Fix-2 既有結構
- ❌ 加第三次 setStack 或迴圈 setStack（無限觸發風險）
- ❌ 加 ResizeObserver（升級 F、需新 dispatch）
- ❌ 自行擴展到 image loader 介入 / dcmread / 自訂 image data 操作

---

## 驗證步驟（工程師驗收用）

1. 確認 backend 跑著（`http://localhost:8000/health` 回 OK；若沒跑、`.\.venv\Scripts\python.exe -m uvicorn main:app --reload`）
2. 確認 instance id 1 仍可用：`curl.exe http://localhost:8000/instances/1`
3. `cd frontend && npm run dev`
4. 瀏覽器開 `http://localhost:5173`
5. **預期**：
   - viewport container 內影像**完整填滿**、無大量黑底、無切割
   - DICOM 1640×1990 fan-shape US 應該完整可見、長寬比正確
6. F12 → Network tab：應只看到**一次** `GET /instances/1/file`（第二次 setStack 應 cache hit）
7. F12 → Console：metadata 主路成功時無 warning；如果出現 warning、紀錄是哪一條
8. F12 → Elements：`.container` style 應有 inline `aspect-ratio: 1640 / 1990`、canvas 尺寸應對應
9. 關掉 dev server、前端 Agent 須在 commit 前 TaskStop background dev server

---

## 回報格式（commit message + PROGRESS §4.4 Fix-3 子段）

- 二次 setStack 是否解決問題？影像填滿率？
- Network tab：是否真的只有一次 GET？或意外二次？
- Image cache hit 時間（第二次 setStack 完成多快）？
- 任何意外發現（VTK actor swap 行為、記憶體變化等）

---

## 預期下個 dispatch（Phase 2 task #9，主 Agent 規劃中）

- API client (`src/api/`)：含 `VITE_API_BASE_URL` env var 制度
- AppContext (`src/context/AppContext.tsx`)：5 欄位
- 4 業務元件 + 結構元件
- 後端新 endpoints `/studies/{id}/series` 與 `/series/{id}/instances` 屆時可用（已 push + alembic upgraded）
- DicomViewer 屆時改由 AppContext 傳入 `instanceId`、移除 hardcoded 常數
- ResizeObserver / 窗縮放適配可在 task #9 重構元件時順便加（屬方向 F）
