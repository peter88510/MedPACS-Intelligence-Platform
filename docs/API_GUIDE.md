---
docspec: "2.0"
type: API_COMMAND_GUIDE
title: "MedPACS API 指令 Guide（Windows / Linux）"
version: "1.0.0"
status: "active"
---

# MedPACS API 指令 Guide

完整的 API 呼叫指令參考，每個端點同時提供 **Linux/macOS** 與 **Windows** 兩種平台寫法。
端點以 `main.py` 為準（共 11 個）。

> 端點規格的權威來源：[`docs/generated/api_spec.md`](./generated/api_spec.md)（由 `main.py` 自動生成）。
> 本檔聚焦「怎麼用指令呼叫」，README 的 [API Endpoints](../README.md#api-端點api-endpoints) 段聚焦「契約說明」。

---

## 0. 前置需求

1. 後端已啟動（見 [README Step 5](../README.md#step-5執行應用程式)）：

   ```bash
   uvicorn main:app --reload
   ```

   伺服器預設執行於 `http://localhost:8000`。

2. 先確認服務存活（見 [§2 GET /health](#2-get-health)）。

### 工具選擇

| 平台 | 推薦工具 | 備註 |
|---|---|---|
| Linux/macOS | `curl` | 系統內建 |
| Windows | `curl.exe` | Windows 10 1803+ 內建。**注意要打 `curl.exe`**，因為 PowerShell 的 `curl` 是 `Invoke-WebRequest` 的別名，參數語法不同 |
| Windows | `Invoke-RestMethod`（PowerShell） | 會自動把 JSON response 反序列化成物件，適合互動查詢 |

> **JSON 美化**：Linux/macOS 可在 curl 後接 ` | jq`；PowerShell 的 `Invoke-RestMethod` 可接 ` | ConvertTo-Json -Depth 10` 展開巢狀結構。

### 設定 BASE_URL 變數（建議）

_Linux/macOS（bash）：_

```bash
BASE_URL="http://localhost:8000"
```

_Windows（PowerShell）：_

```powershell
$BaseUrl = "http://localhost:8000"
```

後續範例皆使用此變數；若不想設變數，直接把 `$BASE_URL` / `$BaseUrl` 換成完整網址即可。

---

## 1. POST /upload — 上傳並處理 DICOM

multipart 上傳，是跨平台差異最大的端點。

_Linux/macOS（curl）：_

```bash
curl -X POST "$BASE_URL/upload" \
  -F "file=@/path/to/patient_001.dcm"
```

_Windows（curl.exe，最簡單、推薦）：_

```powershell
curl.exe -X POST "$BaseUrl/upload" -F "file=@C:\path\to\patient_001.dcm"
```

_Windows（PowerShell 7+，`Invoke-RestMethod -Form`）：_

```powershell
# 注意：-Form 需要 PowerShell 7+（Core）。Windows PowerShell 5.1 無此參數，請改用上面的 curl.exe
Invoke-RestMethod -Uri "$BaseUrl/upload" -Method Post `
  -Form @{ file = Get-Item "C:\path\to\patient_001.dcm" }
```

**Response（200 OK）：**

```json
{
  "instance_id": 1,
  "filename": "patient_001.dcm",
  "patient_id": "P12345",
  "study_instance_uid": "1.2.3.4.5.6.7",
  "modality": "US",
  "message": "DICOM file uploaded and processed successfully",
  "duplicate": false
}
```

**回傳要點：**

| 情況 | 行為 |
|---|---|
| 全新檔案 | `duplicate: false`，回傳新建的 `instance_id` |
| 相同 SOPInstanceUID + 內容相同 | `duplicate: true`，回傳既有 `instance_id`（idempotent） |
| 相同 SOPInstanceUID 但內容不同 | **409**，含 `existing_hash` / `new_hash` / `suggested_actions`（不靜默覆蓋） |
| 驗證失敗（缺 6 欄位 / 非 US modality） | **400** `{ "error": "..." }` |
| 非 DICOM 檔 | **400** `{ "detail": "Invalid DICOM file" }` |

---

## 2. GET /health — 健康檢查

_Linux/macOS：_

```bash
curl "$BASE_URL/health"
```

_Windows（curl.exe）：_

```powershell
curl.exe "$BaseUrl/health"
```

_Windows（PowerShell）：_

```powershell
Invoke-RestMethod "$BaseUrl/health"
```

**Response（200 OK）：**

```json
{ "status": "ok", "version": "2.0" }
```

---

## 3. GET /studies — 列出所有 study

_Linux/macOS：_

```bash
curl "$BASE_URL/studies" | jq
```

_Windows（PowerShell）：_

```powershell
Invoke-RestMethod "$BaseUrl/studies" | ConvertTo-Json -Depth 10
```

**Response（200 OK）：**

```json
{ "studies": [ { "id": 1, "study_instance_uid": "1.2.840.10008..." } ] }
```

---

## 4. GET /studies/{id}/series — 某 study 的所有 series

把 `1` 換成實際的 study 資料庫 `id`。

_Linux/macOS：_

```bash
curl "$BASE_URL/studies/1/series" | jq
```

_Windows（PowerShell）：_

```powershell
Invoke-RestMethod "$BaseUrl/studies/1/series" | ConvertTo-Json -Depth 10
```

**Response（200 OK）：**

```json
{ "series": [ { "id": 10, "series_instance_uid": "1.2.3.4", "study_instance_uid": "1.2.3" } ] }
```

- 空的 `series: []` 合法（study 尚無 series，例如 2026-05-15 前的舊上傳）
- study 不存在 → **404**

---

## 5. GET /series/{id} — 單一 series

_Linux/macOS：_

```bash
curl "$BASE_URL/series/10" | jq
```

_Windows（PowerShell）：_

```powershell
Invoke-RestMethod "$BaseUrl/series/10" | ConvertTo-Json -Depth 10
```

**Response：** 200 為 series 物件；不存在 → **404** `{ "detail": "Series with id 10 not found" }`

---

## 6. GET /series/{id}/instances — 某 series 的所有 instance

_Linux/macOS：_

```bash
curl "$BASE_URL/series/10/instances" | jq
```

_Windows（PowerShell）：_

```powershell
Invoke-RestMethod "$BaseUrl/series/10/instances" | ConvertTo-Json -Depth 10
```

**Response（200 OK）：**

```json
{ "instances": [ { "id": 100, "sop_instance_uid": "1.2.3.4.5", "series_instance_uid": "1.2.3.4" } ] }
```

- 空的 `instances: []` 合法（舊 instance 的 `series_instance_uid` 為 NULL，無法配對）
- series 不存在 → **404**

---

## 7. GET /instances/{id} — 單一 instance 記錄

_Linux/macOS：_

```bash
curl "$BASE_URL/instances/100" | jq
```

_Windows（PowerShell）：_

```powershell
Invoke-RestMethod "$BaseUrl/instances/100" | ConvertTo-Json -Depth 10
```

**Response：** 200 為 instance 物件；不存在 → **404**

---

## 8. GET /instances/{id}/metadata — instance 的 metadata 欄位

_Linux/macOS：_

```bash
curl "$BASE_URL/instances/100/metadata" | jq
```

_Windows（PowerShell）：_

```powershell
Invoke-RestMethod "$BaseUrl/instances/100/metadata" | ConvertTo-Json -Depth 10
```

**Response（200 OK）：**

```json
{ "id": 100, "sop_instance_uid": "1.2.840...", "series_id": 10 }
```

不存在 → **404**

---

## 9. GET /instances/{id}/file — 下載原始 DICOM 檔

回傳 binary（`application/dicom`），要存成檔案。

_Linux/macOS（curl，`-o` 指定輸出檔名）：_

```bash
curl -o instance_100.dcm "$BASE_URL/instances/100/file"
```

_Windows（curl.exe）：_

```powershell
curl.exe -o instance_100.dcm "$BaseUrl/instances/100/file"
```

_Windows（PowerShell，`-OutFile`）：_

```powershell
Invoke-WebRequest -Uri "$BaseUrl/instances/100/file" -OutFile instance_100.dcm
```

**Response：** 200 為檔案串流；instance 不存在或磁碟上找不到檔案 → **404**

---

## 10. POST /ai/segment/{id} — 跑 AI 橫膈膜量測

同步執行（LEGACY mode），結果寫入 `ai_results`。無 request body。

_Linux/macOS：_

```bash
curl -X POST "$BASE_URL/ai/segment/100" | jq
```

_Windows（curl.exe）：_

```powershell
curl.exe -X POST "$BaseUrl/ai/segment/100"
```

_Windows（PowerShell）：_

```powershell
Invoke-RestMethod -Uri "$BaseUrl/ai/segment/100" -Method Post | ConvertTo-Json -Depth 10
```

**Response（200 OK）：**

```json
{ "instance_id": 100, "ai_result_id": 42, "status": "completed",
  "measurement_type": "excursion", "primary_value": 2.31, "primary_unit": "cm",
  "measurement_count": 1 }
```

**錯誤碼：**

| Status | 時機 |
|---|---|
| 422 | device model 不在 machine-model map（無法解析類型，拒絕猜測） |
| 501 | thickness 量測（前瞻設計，演算法未實作） |
| 503 | AI runtime 相依未安裝（見 [README Step 7](../README.md#step-7選用ai-推論設定phase-3-準備)） |
| 500 | 推論已嘗試但失敗（會記錄一筆 `error` row） |
| 404 | instance 不存在 |

---

## 11. GET /ai/result/{id} — 取最新 AI 結果

_Linux/macOS：_

```bash
curl "$BASE_URL/ai/result/100" | jq
```

_Windows（PowerShell）：_

```powershell
Invoke-RestMethod "$BaseUrl/ai/result/100" | ConvertTo-Json -Depth 10
```

**Response（200 OK）：**

```json
{ "instance_id": 100, "ai_result_id": 42, "status": "completed",
  "measurement_type": "excursion", "model_name": "diaphragm_excursion",
  "model_version": "6139799", "primary_value": 2.31, "primary_unit": "cm",
  "confidence": null, "mask_url": null,
  "result": { "schema_version": 1, "measurements": [], "primary": {} },
  "error_message": null, "created_at": "..." }
```

- 尚未跑過 segment → **404**（提示先 `POST /ai/segment/{id}`）
- instance 不存在 → **404**

---

## 12. 端到端範例流程

上傳一個 DICOM，逐層往下查到 AI 結果。

_Linux/macOS（bash）：_

```bash
BASE_URL="http://localhost:8000"

# 1. 上傳，取出 instance_id
INSTANCE_ID=$(curl -s -X POST "$BASE_URL/upload" \
  -F "file=@/path/to/patient_001.dcm" | jq -r '.instance_id')
echo "instance_id = $INSTANCE_ID"

# 2. 看 metadata
curl -s "$BASE_URL/instances/$INSTANCE_ID/metadata" | jq

# 3. 跑 AI 量測
curl -s -X POST "$BASE_URL/ai/segment/$INSTANCE_ID" | jq

# 4. 取結果
curl -s "$BASE_URL/ai/result/$INSTANCE_ID" | jq
```

_Windows（PowerShell）：_

```powershell
$BaseUrl = "http://localhost:8000"

# 1. 上傳，取出 instance_id（用 curl.exe 上傳，再用 PS 解析 JSON）
$resp = curl.exe -s -X POST "$BaseUrl/upload" -F "file=@C:\path\to\patient_001.dcm" | ConvertFrom-Json
$InstanceId = $resp.instance_id
Write-Host "instance_id = $InstanceId"

# 2. 看 metadata
Invoke-RestMethod "$BaseUrl/instances/$InstanceId/metadata" | ConvertTo-Json -Depth 10

# 3. 跑 AI 量測
Invoke-RestMethod -Uri "$BaseUrl/ai/segment/$InstanceId" -Method Post | ConvertTo-Json -Depth 10

# 4. 取結果
Invoke-RestMethod "$BaseUrl/ai/result/$InstanceId" | ConvertTo-Json -Depth 10
```

---

## 13. 端點 / 錯誤碼速查表

| 方法 | 路徑 | 用途 | 可能錯誤碼 |
|---|---|---|---|
| POST | `/upload` | 上傳 DICOM | 400 / 409 / 500 |
| GET | `/health` | 健康檢查 | — |
| GET | `/studies` | 列所有 study | — |
| GET | `/studies/{id}/series` | study 的 series | 404 |
| GET | `/series/{id}` | 單一 series | 404 |
| GET | `/series/{id}/instances` | series 的 instances | 404 |
| GET | `/instances/{id}` | 單一 instance | 404 |
| GET | `/instances/{id}/metadata` | instance metadata | 404 |
| GET | `/instances/{id}/file` | 下載 DICOM 檔 | 404 |
| POST | `/ai/segment/{id}` | 跑 AI 量測 | 404 / 422 / 500 / 501 / 503 |
| GET | `/ai/result/{id}` | 取 AI 結果 | 404 |

---

## 14. 平台註記

- **看錯誤 response body**：`Invoke-RestMethod` 在 PowerShell 5.1 遇到非 2xx 會 throw 終止錯誤、不易讀到 body。想看完整錯誤 JSON（例如 409 的 `suggested_actions`）時，改用 `curl.exe -i`（含 header）或包 `try { } catch { $_.ErrorDetails.Message }`。
- **`curl` vs `curl.exe`**：在 PowerShell 裡 `curl` 是 `Invoke-WebRequest` 別名，**不**支援 `-F` / `-o` 等 curl 旗標。要用真正的 curl 一律打 `curl.exe`。
- **路徑**：Windows 用反斜線 `C:\path\to\file.dcm`，且 `@` 之後不要有空白；Linux/macOS 用正斜線 `/path/to/file.dcm`。
- **互動式 API 文件**：後端啟動後可直接開 `http://localhost:8000/docs`（Swagger UI）逐一試打，免敲指令。
