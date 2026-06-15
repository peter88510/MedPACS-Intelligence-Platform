---
issued: 2026-06-15
issued_by: 主 Agent
task_id: phase-3-frontend-ai-mask-overlay
status: active
---

# 當前任務 — Phase 3 前端：AI 整合接真實 contract + mask overlay

> **本檔機制**：本檔是**當前任務**的單一入口。主 Agent 派發新任務時會**整檔覆蓋**，不累積歷史。歷史請看 `frontend/PROGRESS.md` 的「已完成任務」段與 git commit log。
>
> **前端 Agent 啟動時必讀**（見 `frontend/CLAUDE.md` §1）。
>
> **修改規則**：前端 Agent **不修改本檔**；只讀。新版本由主 Agent 覆寫。

---

## 任務

### 目標

把 AIPanel 從「舊 stub 形狀 + 顯示 JSON」升級為「接真實 AI contract + 顯示真實量測數字 + mask overlay」。

**背景（重要）**：後端 `/ai/segment`·`/ai/result` 早在 2026-06-10 就從 stub 升為真實實作，2026-06-15 又補上 `GET /ai/result/{id}/mask` 真 PNG endpoint，但**前端從未跟上** —— `src/api/types.ts` 的 `AISegmentResponse` / `AIResultResponse` 仍是舊 stub 形狀（`result: {mask, confidence}`），`AIPanel.tsx` 還在讀 `aiResult.result.confidence`（對真實回應會壞）。本 task 一次補齊。

依賴（全部已就緒，已實機驗證）：
- ✅ `/ai/segment/{id}`、`/ai/result/{id}`、`/ai/result/{id}/mask` 三端點都上線（主 Agent 2026-06-15 對 instance 12 實打驗證：segment 寫入、result 回 envelope、mask 回真 PNG 200）
- ✅ `mask_url` 已接上：有 mask 時 `/ai/result/{id}` 回 `"/ai/result/{id}/mask"`，否則 `null`

### 主 Agent 已拍板的決策

- **先修型別、再做 overlay**：分成 A（contract 對齊）→ B（mask overlay）兩段，A 完成可獨立 commit、先讓數值層正確。
- **mask overlay 互動原則**：① 必須**可開關**（toggle，預設關或開由你定）② 必須**可調透明度**（opacity slider 或至少固定半透明）③ **不可改原 DICOM bytes / 不可 resize 原影像**（與既有渲染原則一致）。
- **overlay 技術選型由你評估**：Cornerstone3D segmentation API vs 簡單 `<img>` 絕對定位疊在 canvas 上（半透明）。MVP 可接受後者，但**對齊正確性優先於技術純度**。
- **狀態碼處理**：AIPanel 要能分辨 422（未知機型）/ 501（thickness 未實作）/ 503（引擎未裝）/ 404（未跑過）/ 500（推論失敗），各給可讀提示，不要一律「Failed」。
- **不動 multi-frame / cine UI**（仍 Phase 3 後續或 realtime demo 範圍）。

### ⚠️ Step 0（必做，先於 A/B）— mask 偵察 + 對齊可行性回報

mask 是 paddleseg `pseudo_color_prediction` 輸出，**與 DicomViewer 目前顯示的影像未必同一座標空間 / 同尺寸**（這是 M-mode 超音波，mask 可能是某 frame 的分割、viewer 顯示的可能是另一種 view）。動手做 overlay 前**先偵察**：

1. 用一個已有結果的 instance（後端有 instance 12，`mask_url` 非 null）：
   - 取 `GET /ai/result/12/mask` 看 PNG 實際長相 + 像素尺寸
   - 取 `GET /instances/12/metadata`（Rows/Columns）+ 看 DicomViewer 目前渲染出來的影像
2. 判斷：mask 的尺寸 / 內容**能不能合理疊在 viewer 現在顯示的影像上**？
   - **能**（同尺寸或可等比對齊、語意對得上）→ 繼續 A → B。
   - **不能 / 不確定**（座標空間根本不同、mask 是裁切後區域、或 viewer 顯示的不是 mask 對應的那張）→ **停下、把發現寫成「後端需求清單 / 設計疑問」回報主 Agent**，先別硬疊。A 段（contract 對齊 + 數值顯示）仍可照做，B 段 overlay 暫緩等主 Agent 裁示。

> 這一步是為了避免「疊出來但對不齊還以為做完了」。寧可先回報。

### A 段：AI contract 對齊（數值層）

1. **修 `src/api/types.ts`**（換成真實後端形狀，見下方「相關 API」）：
   - `AISegmentResponse`：`{ instance_id, ai_result_id, status, measurement_type, primary_value, primary_unit, measurement_count }`
   - `AIResultResponse`：完整真實形狀（含 `mask_url: string | null` + `result` envelope + `measurements[]` + `primary`）
   - 新增 `Measurement` / envelope 子型別。
2. **修 `src/components/AIPanel/AIPanel.tsx`**：
   - 移除對 `aiResult.result.confidence` 的依賴（真實 envelope 沒這欄；`confidence` 在頂層、目前恆 null）。
   - 顯示真實 headline：`measurement_type` / `primary_value` + `primary_unit` / `measurement_count`。
   - 完整 `measurements[]` 可摺疊顯示（不必全攤）。
   - 狀態碼分支提示（422/501/503/404/500）。
3. **`src/context/AppContext.tsx`**：`aiResult` 型別與 `runAi()` 配合新 contract 調整（runAi 走 `triggerSegmentation` → `getResult`）。
4. **commit**：`feat(frontend): AIPanel 接真實 AI contract — 量測數值 + 狀態碼分支`

### B 段：mask overlay（Step 0 判定可行才做）

1. `src/api/ai.ts` 加 mask URL builder：`getMaskUrl(instanceId)` → 純 URL（`${API_BASE}/ai/result/${id}/mask`），給 `<img>` / loader 用。
2. overlay 渲染（技術選型你定，守上方「互動原則」三條）：
   - mask `mask_url` 非 null 時才提供 overlay 開關。
   - toggle 控制顯示 / 隱藏；opacity 可調。
   - DicomViewer 原影像不動。
3. AIPanel 的「Mask 渲染待 Phase 3」字樣移除、換成真實 overlay 控制。
4. **commit**：`feat(frontend): mask overlay 渲染 + toggle/opacity 控制`

---

## 相關 API

完整 spec 見 `docs/generated/api_spec.md`（12 routes）。本 task 用到的 AI 三端點**真實形狀**（取代前端舊 stub）：

**`POST /ai/segment/{id}`** — 觸發量測、寫入 ai_results：

| 情境 | HTTP | 回傳 / 意義 |
|---|---|---|
| 成功 | 200 | `{instance_id, ai_result_id, status:"completed", measurement_type, primary_value, primary_unit, measurement_count}` |
| 未知機型（resolver 解不出） | 422 | `{detail}`（device model 不在 machine-model map） |
| thickness（尚未實作） | 501 | `{detail}` |
| 引擎未裝（缺 paddle/weights） | 503 | `{detail}` |
| 推論失敗 | 500 | `{detail}`（已留 error 結果列） |
| instance 不存在 | 404 | `{detail}` |

**`GET /ai/result/{id}`** — 回最新一筆：

```jsonc
{ "instance_id": 12, "ai_result_id": 7, "status": "completed",
  "measurement_type": "excursion", "model_name": "diaphragm_excursion",
  "model_version": "5adfeaa", "primary_value": 1.13, "primary_unit": "cm",
  "confidence": null,
  "mask_url": "/ai/result/12/mask",          // 有 mask 時；否則 null
  "result": {                                  // envelope
    "schema_version": 1, "measurement_type": "excursion", "pipeline_mode": "legacy",
    "model_name": "diaphragm_excursion", "model_version": "5adfeaa",
    "measurements": [
      { "batch_index": 0, "excursion_cm": 1.13, "excursion_pixel": 23,
        "time_pixel": 182, "time_sec": null, "velocity": null,
        "crest": [631,293], "trough": [450,315] }
      // ... N 筆
    ],
    "primary": { "label": "excursion_cm", "value": 1.13, "unit": "cm" }
  },
  "error_message": null, "created_at": "2026-06-15T03:28:42.261962" }
```
- 尚未跑過 → 404（提示先 segment）。

**`GET /ai/result/{id}/mask`** —（2026-06-15 新增）回 mask PNG：

| 情境 | HTTP | 回傳 |
|---|---|---|
| 有 mask | 200 | `Content-Type: image/png`、影像 binary |
| instance 不存在 / 無結果 / 結果無 mask / 檔案遺失 | 404 | `{detail}` |

- **mask 與原 DICOM 未必同尺寸**（見 Step 0）。

詳見 `frontend/context/HANDOFF.md` §3.3（AI 三端點補充說明）+ §6 / §7（endpoint 狀態 + 2026-06-15 changelog）。

---

## 相關深入文件

- **必查**：`frontend/context/HANDOFF.md` §3.3（AI 端點補充）/ §6 / §7
- **必查**：`docs/generated/api_spec.md`（API 權威來源）
- **按需**：`frontend/docs/IMPLEMENTATION.md`（AIPanel / DicomViewer 元件設計、Cornerstone 整合）— 做 overlay 時查 Cornerstone 整合段
- **背景**：`frontend/PROGRESS.md`（AIPanel 現況、Stage C 渲染歷史）

---

## 注意事項

### Scope 邊界（禁忌）

- ❌ 不可動 backend / `main.py` / DB / 根目錄文件
- ❌ 不可動 `vite.config.ts` 的 `server.port`（5173，CORS 對齊）
- ❌ 不可改既有 DicomViewer 的 Cornerstone 渲染核心邏輯（metadata-aware aspect-ratio / setStack / destroy+recreate）— overlay 應**疊加**，不重寫渲染
- ❌ 不可 resize / 改原 DICOM 影像 bytes
- ❌ 不可引入 Redux / Zustand / UI framework / 新 HTTP library
- ❌ 不可做 multi-frame / cine UI、upload UI
- ❌ 不可修改本檔 / `frontend/CLAUDE.md`
- ❌ Step 0 判定 overlay 對不齊時，**不可硬疊裝作完成** → 回報主 Agent

### 渲染原則（重申）

- 等比縮放、保留原始資料；mask overlay 為半透明疊層、可開關
- overlay 對齊以「視覺正確」為準，不確定先回報

---

## 完成標準

### A 段（必須）

- [ ] `src/api/types.ts` 的 `AISegmentResponse` / `AIResultResponse` 換成真實形狀 + `Measurement`/envelope 子型別
- [ ] `AIPanel.tsx` 不再讀 `aiResult.result.confidence`；顯示 `measurement_type` / `primary_value`+`primary_unit` / `measurement_count`
- [ ] `measurements[]` 可摺疊檢視
- [ ] 狀態碼分支提示（422/501/503/404/500 各有可讀訊息）
- [ ] `AppContext` 的 `aiResult` / `runAi` 對齊新 contract
- [ ] `npx tsc -b --noEmit` 通過、`npm run dev` 乾淨

### Step 0 + B 段

- [ ] **Step 0 偵察結果有結論**：mask 可對齊 → 做 B；不可 → 回報主 Agent、B 暫緩（在 PROGRESS / 回報中明確寫出哪一種）
- [ ] （若做 B）`getMaskUrl(instanceId)` URL builder
- [ ] （若做 B）mask overlay：toggle + opacity，`mask_url` 非 null 才提供，原影像不動
- [ ] （若做 B）AIPanel 移除「待 Phase 3」字樣、換真實 overlay 控制
- [ ] End-to-end 瀏覽器驗收：選 instance → Run AI → 看到真實量測數字（→ 若做 B：開 overlay 看到 mask 半透明疊上）

### 文件

- [ ] `frontend/PROGRESS.md`：已完成段加本 task（含 commit hash）；若 Step 0 判 overlay 不可行，加「已知缺口 / 後端需求清單」
- [ ] `frontend/context/SESSION_HISTORY.md`：更新結尾狀態（commit 序列、Step 0 結論、意外發現）

---

## 驗證步驟（工程師驗收用）

1. backend 跑著（`conda activate medpacs_gpu` → uvicorn），DB 有已跑過 AI 的 instance（instance 12 已有結果）
2. `cd frontend && npm run dev` → 開 `http://localhost:5173`
3. 選到 instance 12（或任何已 segment 過的）→ AIPanel 應顯示 `excursion` / `primary_value ~1.13 cm` / `measurement_count`
4. 對沒跑過的 instance 按 Run AI → 觀察 segment 流程 + 狀態碼提示是否正確
5. （若做 B）開 mask overlay toggle → mask 半透明疊在影像上、調 opacity 有效、關掉恢復原影像
6. F12 Console 無 red error；Network 的 AI 請求走 `http://localhost:8000`

---

## 回報格式

每個 commit message：
```
feat(frontend): <段> — <one-line>

<2-3 行 what + why>
```

最後總結（寫進 `frontend/context/SESSION_HISTORY.md` B 段）：
- commit hash 序列（A 段 / B 段）
- **Step 0 結論**：mask 與 viewer 影像對齊可行 / 不可行（附尺寸與發現）
- overlay 技術選型（Cornerstone seg API / `<img>` 疊層）與原因
- 任何後端需求 / 設計疑問（若 Step 0 判不可行，這裡是重點）

---

## 注意：本任務需互動迭代

mask overlay 對齊需要在瀏覽器裡看一張、調一次。**請在專屬前端 `claude` session 執行**（新 session 才讀得到本 DISPATCH，避免快取舊版）。遇到對齊 / 設計分歧 → 依 `frontend/CLAUDE.md` §4 回報主 Agent。
