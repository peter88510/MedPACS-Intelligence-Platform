---
issued: 2026-05-15
issued_by: 主 Agent
task_id: phase-2-task-8-stage-c-metadata
status: active
supersedes: phase-2-task-8-stage-c-fit (gate failed — see PROGRESS §4.4 Fix-1)
---

# 當前任務 — Stage C 收尾 Fix-2：metadata-aware 動態 aspect-ratio

> **本檔機制**：本檔是**當前任務**的單一入口。主 Agent 派發新任務時會**整檔覆蓋**，不累積歷史。歷史請看 `frontend/PROGRESS.md` 的「已完成任務」段與 git commit log。
>
> **前端 Agent 啟動時必讀**（見 `frontend/CLAUDE.md` §1）。
>
> **修改規則**：前端 Agent **不修改本檔**；只讀。新版本由主 Agent 覆寫。

---

## 任務

### 目標

接續 Stage C 修正。前次 fit dispatch（`phase-2-task-8-stage-c-fit`）試 `resetCamera() + aspect-ratio: 4/3` gate 失敗 — 靜態 4:3 對超音波 fan-shape 不適配、`resetCamera()` 在 canvas 形狀與影像形狀不匹配時無解。本 dispatch 採方向 B（前端 Agent 推薦）：**用 Cornerstone metadata 取 image rows/columns、動態設 container aspect-ratio**。

完成後一併 commit Stage C 完整版（含 fit dispatch 累積的改動 + 本 dispatch 的 metadata-aware）。

### 主 Agent 已拍板的決策

- **方向**：B（runtime metadata-aware），不採 A / C / D（PROGRESS §4.4 Fix-1 已分析）
- **Multi-frame 處理**：仍**不做** cine / frame slider — 屬 task #9 / Phase 3
- **保留 fit dispatch 的好東西**：`resetCamera()` 不回退、`cancelled` flag 不動、cleanup destroy 不動
- **靜態 4/3 改由 runtime 動態 aspect-ratio 取代**；`min-height: 400px` 兜底保留

### 具體工作

1. **修 `frontend/src/components/DicomViewer/DicomViewer.tsx`**

   在 `await viewport.setStack([imageId])` 完成後、`resetCamera()` 之前，加 metadata 取尺寸與 container aspect-ratio 動態設定。建議流程：

   ```ts
   // (concept — 實作細節由前端 Agent 根據 Cornerstone 實際 API 決定)
   await viewport.setStack([imageId]);

   // 取 image dimensions：主路 metaData，備路 viewport.getImageData()
   let aspectRatio: string | null = null;
   try {
     const pixelModule = cornerstone.metaData.get('imagePixelModule', imageId);
     if (pixelModule?.rows && pixelModule?.columns) {
       aspectRatio = `${pixelModule.columns} / ${pixelModule.rows}`;
     }
   } catch (e) {
     console.warn('[DicomViewer] imagePixelModule fetch failed:', e);
   }

   // 備路：若主路失敗、試 viewport.getImageData()
   if (!aspectRatio) {
     const imageData = viewport.getImageData?.();
     if (imageData?.dimensions) {
       const [w, h] = imageData.dimensions;
       if (w > 0 && h > 0) aspectRatio = `${w} / ${h}`;
     }
   }

   // 動態設 container aspect-ratio；若仍取不到、保留 CSS fallback (見 module.css)
   if (aspectRatio && containerRef.current) {
     containerRef.current.style.aspectRatio = aspectRatio;
   } else {
     console.warn('[DicomViewer] Could not determine image dimensions, falling back to CSS default');
   }

   viewport.resetCamera();
   viewport.render();
   ```

   - 保留 `cancelled` flag 與 cleanup `destroy()`（StrictMode-safe）
   - 不要把 `cornerstone` import 到 React state（同 Stage B/C 注意事項）

2. **修 `frontend/src/components/DicomViewer/DicomViewer.module.css`**

   移除靜態 `aspect-ratio: 4/3`，改為 fallback-only 形式：

   ```css
   .container {
     width: 100%;
     min-height: 400px;
     /* aspect-ratio 由 DicomViewer.tsx runtime 動態設；
        若 runtime 取不到 metadata、瀏覽器仍會用 min-height 兜底 */
     aspect-ratio: 4 / 3;  /* CSS fallback；JS 設定後會覆蓋此值 */
     background-color: #000;
   }
   ```

   - 保留黑底
   - `min-height: 400px` 兜底（即使 aspect-ratio 算出極端比例也有最低高度）
   - CSS `aspect-ratio: 4/3` 留作 fallback，JS runtime 會 override

3. **驗證流程**

   - `npx tsc -b --noEmit` 通過
   - `npm run dev` 乾淨啟動（無 error / warning）
   - 瀏覽器以 `INSTANCE_ID=1`（`Peter_Quiet_1.dcm`，超音波 fan-shape）開啟、確認**影像完整顯示無切割**
   - 工程師肉眼驗收：影像比例正確、container 高度合理、無黑邊溢出
   - F12 → Console 應看到 console.warn fallback log（如果有的話）— 用以判斷是否走了 metadata 主路

4. **若主路 + 備路都失敗（取不到 dimensions）**：

   - **不可**自行進入更深的 metadata 探索（如直接 dcmread DICOM 檔、自訂 image loader）
   - 在 PROGRESS §4.4 加 Fix-2 子段、寫下：
     - 試了哪些 API（log Cornerstone metaData 實際可用的 module names）
     - Console log 內容
     - 觀察到什麼
   - **回報主 Agent**，主 Agent 會評估是否：(a) 升級到 image-loaded callback 路徑、(b) 換用 cornerstone-image-loader 直接讀 imageId 元資料、(c) 暫時回退靜態 1/1

5. **若成功**：

   - **單一 commit** 含 Stage C 全部工作（自最初 Stage C dispatch 至本 metadata-aware 修正的所有改動）
   - Commit message 模板：
     ```
     feat(frontend): Phase 2 task #8 Stage C — DicomViewer 第一張 DICOM 渲染

     新增：
     - src/components/DicomViewer/DicomViewer.tsx — wadouri scheme + StrictMode-safe
       + viewport.resetCamera() + runtime metadata-aware aspect-ratio
     - src/components/DicomViewer/DicomViewer.module.css — min-height + CSS fallback
     改寫：
     - src/App.tsx — 取代 Vite scaffold、hardcoded INSTANCE_ID

     歷程：先派 stage-c 純 viewer 過關但影像被切；fit dispatch 試
     resetCamera + aspect-ratio 4/3 gate 失敗（PROGRESS §4.4 Fix-1）；
     本 metadata dispatch 採 cornerstone.metaData.get('imagePixelModule')
     動態設 container aspectRatio = columns/rows，瀏覽器驗收完整顯示。

     Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
     ```
   - Commit hash 回填：
     - PROGRESS §1 Stage C 條目
     - SESSION_HISTORY B 段「已完成里程碑」Stage C 項
   - PROGRESS §4.4 標已解決（含 Fix-2 結果摘要）；保留 §4.4 Fix-1 紀錄不刪（歷史追溯）
   - 完成後 **TaskStop 你的 background dev server**（fit dispatch §4.5 教訓）

---

## 相關 API

無新 endpoint 呼叫。後端 `GET /instances/{id}/file` 不變。

**Backend 狀態變動通知**（與本 dispatch 無直接關係、僅供 context）：
- 工程師已跑 `alembic upgrade head` → migration `e25c80289a9c` 上線
- Backend 新 endpoints `GET /studies/{id}/series` + `GET /series/{id}/instances` 已可用
- 但本 dispatch **不**呼叫這些（屬 task #9 範圍）

---

## 相關深入文件

- `frontend/PROGRESS.md` §4.4 Fix-1 — 前次 fit dispatch 失敗分析、4 個方向選項（A/B/C/D 各自 trade-off）
- `frontend/context/SESSION_HISTORY.md` A 段「待決定事項」第 1 條 — 已由本 dispatch 拍板選 B
- `frontend/docs/IMPLEMENTATION.md` — 元件樹與 Cornerstone 整合架構（背景參考）
- Cornerstone3D 官方 API（如有疑問）：`@cornerstonejs/core` 的 `metaData` 與 `Types.IImageData`

---

## 注意事項

### 渲染原則（核心，工程師 2026-05-15 明示）

**等比縮放 + 保留原始資料**：

```
container 比例 = image.columns / image.rows
       ↓
container 與原圖**同比例**
       ↓
viewport.resetCamera() → Cornerstone WebGL canvas fit-to-container
       ↓
整張影像剛好填滿 container · 無切割 · 無留邊 · 無拉伸 · 無扭曲
```

要點：
- Cornerstone WebGL canvas **永遠等比 + 高品質 resampling** — 不會做像素層 stretch
- container 的 aspect-ratio 設定**只影響顯示框大小**、**不影響原始 DICOM pixel data**
- 原 DICOM bytes 在 backend / 在傳輸 / 在 Cornerstone 內部 image cache **全程不變**
- WindowLevel / VOI LUT 是顯示時的轉換、不修改原資料
- **不可**寫自訂 resize / canvas redraw / Image()-based hack / 修改 image data — 這些都會破壞醫療影像保真度

### Cornerstone 取 metadata 的常見坑

1. **`metaData.get(moduleType, imageId)` 在 image 還沒 load 完前回 `undefined`** — 必須在 `await setStack` **之後**才呼叫；本 dispatch 流程已是 await 後，但要確認沒插入更早的 path

2. **不同 `moduleType` 名稱**：
   - `imagePixelModule`：含 `rows`、`columns`、`bitsAllocated`、`samplesPerPixel`、`photometricInterpretation`
   - `imagePlaneModule`：含 `pixelSpacing`、`imageOrientationPatient`、`imagePositionPatient`（可能 US 沒這個 module，因為 US 不一定有 patient coordinate）
   - 對本任務（要 rows/columns），用 `imagePixelModule`

3. **fallback 路徑 `viewport.getImageData()`** 回傳結構是 vtkImageData（VTK.js wrapper）；`dimensions` 是 `[columns, rows, slices]`（slices=1 對 single-frame）。注意順序：第一個是 columns 不是 rows

4. **runtime aspect-ratio 設定**：
   - JS 設 `element.style.aspectRatio = '4 / 3'` 會 override CSS 的 `aspect-ratio` 屬性
   - 動態設置後若元件 unmount → 重 mount，container 是新 element，重新設置即可（StrictMode 場景內建處理）

### Scope 邊界（禁忌）

- ❌ 不可動 backend（`main.py`、`models.py`、`alembic/`、tests）
- ❌ 不可動 `vite.config.ts` server.port = 5173
- ❌ 不可動 `frontend/src/main.tsx` / `frontend/src/cornerstone/setup.ts`
- ❌ 不可寫 API client / AppContext / StudyList / MetadataPanel / AIPanel（task #9）
- ❌ 不可加 zoom / pan / window-level 互動工具
- ❌ 不可加 frame 切換 UI / cine 播放 / frame slider（屬 task #9 / Phase 3）
  - **註**：multi-frame DICOM **仍可上傳並透過本元件顯示**（Cornerstone `wadouri:` scheme 預設載入第 1 frame 不會炸）；只是不做切換 frame 的互動。前端 Agent 不需為 multi-frame 預留 props 或 hook 接口（task #9 引入 AppContext 時才會需要 currentFrame state）
- ❌ 不可寫自訂 image resize / canvas redraw / Image()-based 顯示 hack（會破壞醫療影像保真度，違反「保留原始資料」原則）
- ❌ 不可修改 Cornerstone 內部 image data 或 image cache
- ❌ 不可自行下載 sample DICOM（沿用 `INSTANCE_ID=1`）
- ❌ 不可修 `frontend/PROGRESS.md` lines 5, 64 stale link（主 Agent 已於 commit `0cffff4` 修正、不要重複動）
- ❌ 不可修改本檔
- ❌ **若主路 + 備路都失敗，不可自行擴展到「直接 dcmread DICOM」或「自訂 image loader」**（scope creep）

### Commit 操作

- 與既有所有未 commit 改動一起做**單一 commit**：
  ```
  M  frontend/PROGRESS.md          (Stage C 主體 + Fix-1 + 本 dispatch Fix-2 累積)
  M  frontend/context/SESSION_HISTORY.md
  M  frontend/src/App.tsx          (Stage C 主體)
  M  frontend/src/components/DicomViewer/DicomViewer.tsx       (Stage C + Fix-1 + Fix-2)
  M  frontend/src/components/DicomViewer/DicomViewer.module.css (Stage C + Fix-1 + Fix-2)
  ?? frontend/src/components/      (Stage C 新建)
  ```
- 不要拆 commit
- pre-commit hook 對前端檔不觸發（hook 只看 `main.py` / `models.py` / `alembic/versions/*.py`），但仍會跑 — commit 後 `git status` 確認乾淨

---

## 完成標準

### 必須全部成立

- [ ] `DicomViewer.tsx` 在 `await setStack` 之後、`resetCamera()` 之前，動態取 image rows/columns 設 container `aspectRatio`
- [ ] 含主路 + 備路 + fallback warning log 三層
- [ ] `DicomViewer.module.css` 移除靜態 4/3、保留 `min-height: 400px` + CSS fallback `aspect-ratio: 4/3`
- [ ] `npx tsc -b --noEmit` 通過
- [ ] `npm run dev` 啟動乾淨
- [ ] 瀏覽器以 `INSTANCE_ID=1` 開啟、**影像完整顯示無切割**（工程師肉眼確認）
- [ ] F12 Console 觀察：若走主路、無 warning log；若走備路、看到主路 warning；若 fallback、看到兩個 warning + CSS 4/3 兜底
- [ ] 單一 commit 含 Stage C 全部工作；commit hash 回填 PROGRESS §1 + SESSION_HISTORY B 段
- [ ] PROGRESS §4.4 主段標「已解決於 commit XXX」、加 Fix-2 結果摘要子段；保留 Fix-1 子段不刪
- [ ] 完成驗收後 TaskStop background dev server

### 允許但不強制

- 若你發現 Cornerstone3D v4 的 metaData API 與 dispatch 寫法不一致（如 namespace 不同、moduleType 名稱不同），可調整實作但保持核心邏輯（取 rows/columns → 設 aspectRatio）
- 若主路 + 備路都成功，可只保留主路、簡化程式碼

### 禁止

- ❌ 多個 commit
- ❌ 動 backend / vite.config / main.tsx / setup.ts / DISPATCH.md
- ❌ 改 `INSTANCE_ID` 預設值
- ❌ 自行擴展 metadata 探索範圍（直接 dcmread / 自訂 loader）
- ❌ 開始 task #9 工作（API client / AppContext / 元件）

---

## 驗證步驟（工程師驗收用）

1. 確認 backend 跑著（`http://localhost:8000/health` 回 OK）
2. 確認 instance id 1 仍可用：`curl.exe http://localhost:8000/instances/1`
3. `cd frontend && npm run dev`
4. 瀏覽器開 `http://localhost:5173`
5. **預期**：viewport 顯示完整 DICOM（fan-shape 整張可見、無頂底切割、無左右溢出）
6. F12 → Console 觀察 metadata fallback log
7. F12 → Elements 檢查 `.container` 的 inline style — 應有 `aspect-ratio: <columns> / <rows>`（若主路 / 備路成功）
8. 關掉 dev server、前端 Agent 須在 commit 前 TaskStop background dev server

---

## 回報格式（commit message + PROGRESS §4.4 Fix-2 子段）

- 哪條路徑成功（主路 metaData / 備路 viewport.getImageData / fallback）？
- 該 DICOM 實際 rows × columns 是多少？算出 aspect-ratio 是多少？
- 與工程師驗收主觀感受對照（影像是否真的完整？）
- 任何意外發現（Cornerstone API 細節、metadata 結構等）

---

## 預期下個 dispatch（Phase 2 task #9，主 Agent 規劃中）

- API client (`src/api/`)：含 `VITE_API_BASE_URL` env var 制度
- AppContext (`src/context/AppContext.tsx`)：5 欄位
- 4 業務元件 + 結構元件（`<Layout>` / `<TopBar>` / `<StudyList>` / `<MetadataPanel>` / `<AIPanel>`）
- 屆時 Stage C 的 hardcoded `INSTANCE_ID` 改由 AppContext + StudyList 點選注入
- 後端新 endpoints `/studies/{id}/series` 與 `/series/{id}/instances` 屆時可用（`9967f71` 已上線、工程師已 alembic upgrade）
