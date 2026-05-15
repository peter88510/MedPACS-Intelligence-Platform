---
issued: 2026-05-15
issued_by: 主 Agent
task_id: phase-2-task-8-stage-c-fit
status: active
---

# 當前任務 — Stage C 收尾：影像尺寸自適應 + 一併 commit

> **本檔機制**：本檔是**當前任務**的單一入口。主 Agent 派發新任務時會**整檔覆蓋**，不累積歷史。歷史請看 `frontend/PROGRESS.md` 的「已完成任務」段與 git commit log。
>
> **前端 Agent 啟動時必讀**（見 `frontend/CLAUDE.md` §1）。
>
> **修改規則**：前端 Agent **不修改本檔**；只讀。新版本由主 Agent 覆寫。

---

## 任務

### 目標

修正 Stage C 驗收時發現的「影像尺寸不完整」缺口（PROGRESS §4.4），讓 DicomViewer 能完整顯示 DICOM 影像，**完成後一併 commit Stage C 完整版**。

### 主 Agent 已拍板的決策

- **處理時機**：立刻修，不延後（不併進 task #9 的「CSS Modules 樣式整理」）
- **Commit 策略**：尺寸修正完成後，與 Stage C 既有未 commit 的 4 個檔案一起做**單一 commit**（commit message 反映 Stage C 完整版，註明含尺寸修正）
- **修正手法**：先試 `viewport.resetCamera()` + 容器 aspect-ratio 雙管齊下；若仍不完整再從 metadata 取尺寸（屬探索範疇）

### 具體工作

1. **修 `frontend/src/components/DicomViewer/DicomViewer.tsx`**
   - 在 `viewport.setStack([imageId])` 之後（async chain 內）呼叫 `viewport.resetCamera()`
   - 然後 `viewport.render()`
   - Cornerstone3D `setStack` 是 promise — 確保 `await` 或 `.then()` 處理
   - StrictMode-safe 既有處理保留（`cancelled` flag、cleanup destroy 不變）

2. **修 `frontend/src/components/DicomViewer/DicomViewer.module.css`**
   - 容器尺寸從固定 `width: 100%; height: 600px;` 改為 aspect-ratio 自適應
   - 建議：`width: 100%; aspect-ratio: 4/3;`（DICOM 大多 4:3 或 1:1）+ 保留 `min-height: 400px` 兜底
   - 黑底 `background-color: #000;` 保留

3. **驗證**（與 Stage C 同樣流程）
   - `npx tsc -b --noEmit` 通過
   - `npm run dev` 乾淨啟動
   - 瀏覽器以 `INSTANCE_ID=1`（`Peter_Quiet_1.dcm`）開啟、確認影像**完整顯示**（無被切、無黑邊溢出）

4. **若 ① + ② 仍不完整**：
   - 先停下、把當下狀態與觀察寫進 PROGRESS §4.4 follow-up
   - 回報主 Agent，**不要**自行進入 metadata-driven 尺寸（會 scope creep）
   - 主 Agent 會評估是否要改派一個「DICOM metadata-aware viewport」dispatch

5. **若 ① + ② 成功**：
   - **單一 commit** 含全部 Stage C 工作（尺寸修正 + 之前未 commit 的 4 檔）
   - Commit message 模板（範例）：
     ```
     feat(frontend): Phase 2 task #8 Stage C — DicomViewer 第一張 DICOM 渲染

     新增：
     - src/components/DicomViewer/DicomViewer.tsx — wadouri scheme + StrictMode-safe
     - src/components/DicomViewer/DicomViewer.module.css — aspect-ratio 自適應
     改寫：
     - src/App.tsx — 取代 Vite scaffold、hardcoded INSTANCE_ID

     驗證：以 INSTANCE_ID=1 (Peter_Quiet_1.dcm) 成功渲染，
     viewport.resetCamera() 後影像完整顯示。

     Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
     ```
   - Commit 後 hash 回填 PROGRESS §1 Stage C 條目 + B 段里程碑

---

## 相關 API

無新 endpoint 呼叫；既有 `GET /instances/{id}/file` 不變。

---

## 相關深入文件

- `frontend/PROGRESS.md` §4.4 — 尺寸缺口紀錄與初步分析
- `frontend/PROGRESS.md` §4.5 — Stage C debug 紀錄（zombie dev server / port 衝突 / instance_id 探測）
- `frontend/context/SESSION_HISTORY.md` A 段「待決定事項」第 1 條 — 可移除（主 Agent 已拍板選 ①）

---

## 注意事項

### Cornerstone3D resetCamera 行為

- `resetCamera()` 會把 viewport 的 zoom / pan / windowing 重設為「能看到完整影像」的預設值
- 必須在 `setStack` **完成 await** 後呼叫（image 還沒 load 完前 resetCamera 沒意義）
- 一般 pattern：
  ```ts
  await viewport.setStack([imageId]);
  viewport.resetCamera();
  viewport.render();
  ```

### Scope 邊界

- ❌ 不可動 backend（含 `main.py`、`models.py`、`alembic/`）
- ❌ 不可動 `vite.config.ts`（同 Stage B/C 限制）
- ❌ 不可動 `frontend/src/main.tsx` 或 `frontend/src/cornerstone/setup.ts`（既有運作良好）
- ❌ 不可加 zoom / pan / window-level 互動工具（task #9 範圍）
- ❌ 不可加 metadata 顯示（task #9 範圍）
- ❌ 不可清 Vite scaffold 殘留（`App.css` / `assets/` / `public/icons.svg`）— 雖 SESSION_HISTORY 標可順手清，但本 dispatch scope 嚴格限縮在尺寸
- ❌ 不可修 `frontend/PROGRESS.md` lines 5, 64 的 `./IMPLEMENTATION.md` stale link（屬另一個 issue，主 Agent 會單獨處理）
- ❌ 不可修改本檔

### Commit 操作

- 與你既有的 4 個未 commit 檔（`src/components/`、`src/App.tsx`、`PROGRESS.md`、`context/SESSION_HISTORY.md`）+ 本次新改的 2 個（DicomViewer.tsx 加 resetCamera、DicomViewer.module.css 改 aspect-ratio）**一次 commit**
- 不要拆成兩個 commit（避免「Stage C 半成品」歷史）
- pre-commit hook 會自動跑（不影響前端檔，但 commit 後 git status 確認乾淨）

---

## 完成標準

### 必須全部成立

- [ ] DicomViewer.tsx 在 `setStack` 後呼叫 `resetCamera()` 再 `render()`
- [ ] DicomViewer.module.css 容器改為 aspect-ratio 自適應
- [ ] `npx tsc -b --noEmit` 通過
- [ ] `npm run dev` 啟動乾淨（無 error / warning）
- [ ] 瀏覽器以 `INSTANCE_ID=1` 開啟、**影像完整顯示無切割**（工程師肉眼確認）
- [ ] 單一 commit 含全部 Stage C 工作（6 個檔：DicomViewer.tsx / DicomViewer.module.css / App.tsx / PROGRESS.md / context/SESSION_HISTORY.md / 任何順手改動）
- [ ] Commit hash 回填 PROGRESS.md §1 Stage C 條目 + SESSION_HISTORY B 段里程碑「Stage C」項
- [ ] PROGRESS.md §4.4「影像尺寸不完整」缺口移除（或標註「已解決於 commit XXX」），維持累積歷史可讀
- [ ] **完成驗收後** 用 `TaskStop` 結束你的 background dev server（避免 PROGRESS §4.5 第 1 點再次發生）

### 允許但不強制

- 若 `aspect-ratio: 4/3` 與某些 DICOM 不匹配，可改為 `1/1` 或其他比例 — 在 PROGRESS §1 Stage C 條目註明所選比例與理由
- DicomViewer.tsx 的 useEffect cleanup 邏輯若需微調以配合新 async flow，可動 — 但保持 StrictMode-safe

### 禁止

- ❌ 拆成兩個以上 commit
- ❌ 動 vite.config.ts / backend / main.tsx / setup.ts
- ❌ 改 INSTANCE_ID 預設值（保留 `1`）
- ❌ 自行擴展 metadata-driven 尺寸（若 ①+② 不夠用、回報主 Agent）

---

## 驗證步驟（工程師驗收用）

1. 確認 backend 跑著（`http://localhost:8000/health` 回 OK）
2. 確認 instance id 1 仍可用：`curl.exe http://localhost:8000/instances/1`
3. `cd frontend && npm run dev`
4. 瀏覽器開 `http://localhost:5173`
5. 預期：viewport 內看到完整 DICOM 影像、無切割、無不必要黑邊
6. F12 → Console 無 red error
7. 關掉 dev server（前端 Agent 須在 commit 前 TaskStop 自己背景的 dev server）

---

## 回報格式（commit message + PROGRESS 更新）

- 改動檔案清單（path + 大致行數）
- 用了哪個 aspect-ratio 與理由
- `viewport.resetCamera()` 放置位置（在 setStack 之後 / await 流程）
- 是否觸及 PROGRESS §4.4 列的任一可能因素
- 任何意外發現

---

## 預期下個 dispatch（Phase 2 task #9，主 Agent 規劃中）

- **依賴**：本 dispatch 完成 + backend 補完（`/studies/{id}/series` 等）— 主 Agent 正在規劃 backend schema 補完範圍（涉及 Instance ↔ Series FK），具體下個 dispatch 內容會等主 Agent 與工程師確認 backend 範圍後派發
