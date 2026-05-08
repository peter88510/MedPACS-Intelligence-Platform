# CLAUDE.md — AI 操作規範文件

> **文件定位**：這是本 repository 的 **AI Operating Contract**。
> 所有 AI coding agent（Claude、GPT、Cursor、Copilot 等）在此專案中執行任何操作前，**必須完整閱讀並遵守本文件**。
> 本文件不是需求文件，也不是功能規格書，而是 **AI 行為約束與開發規範**。

---

## 目錄

1. [專案背景與系統定位](#1-專案背景與系統定位)
2. [核心原則](#2-核心原則)
3. [最小修改原則](#3-最小修改原則)
4. [Patch-First 開發模式](#4-patch-first-開發模式)
5. [禁止行為清單](#5-禁止行為清單)
6. [架構保護規範](#6-架構保護規範)
7. [醫療系統特殊約束](#7-醫療系統特殊約束)
8. [輸出規範（每次修改必須遵守）](#8-輸出規範每次修改必須遵守)
9. [安全性與穩定性規範](#9-安全性與穩定性規範)
10. [AI 行為控制規範](#10-ai-行為控制規範)
11. [測試規範](#11-測試規範)
12. [資料庫操作規範](#12-資料庫操作規範)
13. [DICOM 處理規範](#13-dicom-處理規範)
14. [錯誤處理與 Logging 規範](#14-錯誤處理與-logging-規範)
15. [擴充區塊（保留）](#15-擴充區塊保留)

---

## 1. 專案背景與系統定位

```
系統類型：醫療影像（DICOM）處理 API + Lightweight PACS Backend
技術核心：FastAPI + PostgreSQL + SQLAlchemy + Pydantic
儲存架構：Local file storage（DICOM 檔案）+ PostgreSQL（structured metadata）
狀態：已上線系統，有用戶依賴的 API contract 與 DB schema
```

### 關鍵保護對象（Critical Protected Assets）

以下對象受到最高層級保護，**任何修改都需要明確說明理由與風險**：

| 保護對象 | 保護層級 | 說明 |
|---|---|---|
| PostgreSQL DB schema | 🔴 最高 | 已上線，不可破壞性變更 |
| 對外 API contract（endpoint / response format） | 🔴 最高 | 有用戶依賴 |
| DICOM parsing / metadata pipeline | 🔴 最高 | 核心業務邏輯 |
| DB upsert logic（patient / study / instance） | 🔴 最高 | 資料一致性關鍵 |
| File storage structure | 🟠 高 | 影響現有檔案可讀性 |
| Upload flow behavior | 🟠 高 | 影響用戶端整合 |
| Error response format consistency | 🟠 高 | 用戶端 error handling 依賴 |
| Test fixtures & integration tests | 🟡 中 | 不可靜默修改 |
| Logging & exception handling rules | 🟡 中 | 可擴充，不可刪除 |

---

## 2. 核心原則

```
1. 做最少的事，做對的事
2. 不確定就問，不猜測就停
3. 醫療系統沒有「小改動」，每個修改都可能影響資料完整性
4. 可讀性 > 聰明度 > 效能
5. 每一次修改都要可以 revert
```

---

## 3. 最小修改原則

### ✅ 應該做的

- 僅修改完成任務**直接需要**的程式碼
- 優先在現有函數內進行行為修正，而非重寫整個函數
- 新增功能時，優先以新增函數/方法的方式擴充，避免改動現有邏輯
- 保持現有縮排風格、命名慣例、import 順序

### ❌ 不應該做的

- 不可趁機「順便」重構無關的程式碼
- 不可為了讓程式碼「更漂亮」而更動未被要求的部分
- 不可在完成任務的同時靜默改變函數的副作用（side effects）
- 不可刪除「看起來沒用」的程式碼（可能是刻意保留的 fallback）

### 判斷基準

```
問自己：「這行修改是任務要求的，還是我認為比較好？」
如果是後者 → 不要改，或明確列在「建議」區塊讓工程師決定。
```

---

## 4. Patch-First 開發模式

### 修改既有檔案

- **一律使用 patch / diff 格式**呈現修改，清楚標示 `- 移除` 與 `+ 新增`
- 禁止對既有檔案輸出完整檔案內容（除非是新建檔案或明確被要求整檔輸出）
- 每個 patch 必須附上**修改理由**

```diff
# 正確示範
- def get_patient(db: Session, patient_id: str):
-     return db.query(Patient).filter(Patient.id == patient_id).first()
+ def get_patient(db: Session, patient_id: str) -> Optional[Patient]:
+     """根據 patient_id 查詢病患，不存在回傳 None"""
+     return db.query(Patient).filter(Patient.patient_id == patient_id).first()
```

### 新增檔案

- 新檔案才可完整輸出
- 新檔案必須說明：檔案用途、放置位置、與現有模組的關係

### 優先順序

```
1. 修改既有函數（patch）
2. 在既有檔案新增函數
3. 新建檔案
4. 新建模組（需要最多說明）
```

---

## 5. 禁止行為清單

以下行為**在任何情況下都不允許**，即使工程師要求也必須先警告再確認：

### 架構層面

- ❌ 禁止修改整體系統架構（API layer → Service layer → Model layer → DB layer）
- ❌ 禁止將 business logic 移入或移出 service layer
- ❌ 禁止改變 `db.py` session management 機制（除非明確被要求修復 bug）
- ❌ 禁止改變 FastAPI dependency injection 的結構

### API Contract 層面

- ❌ 禁止修改現有 API endpoint 路徑
- ❌ 禁止修改 response schema 的欄位名稱或型別（可以新增欄位）
- ❌ 禁止將 200 回傳改為其他 status code（或反之）而不說明
- ❌ 禁止靜默移除 response 中的任何欄位

### 資料庫層面

- ❌ 禁止執行破壞性 migration（DROP COLUMN、DROP TABLE、RENAME COLUMN）
- ❌ 禁止修改現有 SQLAlchemy model 欄位名稱
- ❌ 禁止改變 upsert logic 的行為（patient / study / series / instance）
- ❌ 禁止移除資料庫層的 unique constraints 或 indexes

### 依賴套件層面

- ❌ 禁止任意升級 `requirements.txt` 中的套件版本
- ❌ 禁止新增大型依賴（如 Celery、Redis）而不說明必要性
- ❌ 禁止移除現有依賴（即使看起來沒被使用）

### 行為層面

- ❌ 禁止 silent behavior change（改了行為但沒有說明）
- ❌ 禁止修改 error message 格式而不標注（client 可能有 string match）
- ❌ 禁止改變 logging 的 level 或 format 而不說明

---

## 6. 架構保護規範

### 現有分層結構（不可破壞）

```
┌─────────────────────────────────┐
│  API Layer                      │  main.py / routes / endpoints
│  - 接收 HTTP request            │
│  - 參數驗證（Pydantic）          │
│  - 呼叫 service layer           │
├─────────────────────────────────┤
│  Service Layer                  │  db_service.py / storage.py
│  - Business logic               │
│  - 跨 model 操作                 │
│  - 非 HTTP 概念（不知道 request）│
├─────────────────────────────────┤
│  Model Layer                    │  SQLAlchemy models
│  - 資料結構定義                  │
│  - Relationship 定義             │
├─────────────────────────────────┤
│  DB Layer                       │  db.py
│  - Session management           │
│  - Connection pool               │
└─────────────────────────────────┘
```

### 跨層規範

- API layer **不可直接操作 DB**，必須透過 service layer
- Service layer **不可 import FastAPI** 相關模組（Request / Response / HTTPException 除外）
- Model layer **不可包含 business logic**
- DB layer **不可包含 query logic**

---

## 7. 醫療系統特殊約束

> 這是醫療影像系統，資料錯誤可能影響診斷結果。以下約束為醫療系統強制要求。

### DICOM 資料完整性

- **禁止**在未確認 DICOM tag 存在的情況下直接存取 tag 值（必須有 `.get()` fallback）
- **禁止**靜默丟棄 DICOM parsing error（必須 log 並回傳明確錯誤）
- **禁止**修改 UID 生成邏輯（SOPInstanceUID / StudyInstanceUID / SeriesInstanceUID）
- Patient ID、Study UID、Series UID 的 uniqueness constraint **不可鬆動**

### 資料隔離

- 不同 patient 的資料在 storage path 與 DB record 上必須保持隔離
- 禁止任何可能導致 patient 資料交叉污染的修改

### Audit & Traceability

- 任何會修改資料庫記錄的操作，**必須保留 log**
- 不可移除現有的 operation logging

---

## 8. 輸出規範（每次修改必須遵守）

每次 AI 提出程式碼修改時，**必須按照以下結構輸出**，不可省略任何區塊：

```markdown
## 📋 分析
- 問題根因或需求理解
- 受影響的範圍（哪些檔案、哪些函數）
- 不受影響但需要注意的相關程式碼

## 📝 修改計畫
- 步驟 1：...
- 步驟 2：...
- （按優先順序排列，說明每步驟的目的）

## 📁 修改檔案清單
| 檔案 | 操作類型 | 說明 |
|------|----------|------|
| db_service.py | PATCH | 新增 get_series_by_uid 函數 |
| models.py | PATCH | 新增 series_description 欄位 |
| test_api.py | PATCH | 新增對應測試案例 |

## 💻 程式碼變更
（使用 diff 格式，patch-first）

## ⚠️ 風險說明
- 對 API contract 的影響：無 / 有（說明）
- 對 DB schema 的影響：無 / 有（說明）
- 對現有測試的影響：無 / 有（說明）
- 需要 migration 嗎？是 / 否
- 建議驗證步驟：...

## 💡 建議（可選）
（不在本次任務範圍內，但值得注意的改進點）
```

---

## 9. 安全性與穩定性規範

### Input Validation

- 所有外部輸入**必須透過 Pydantic schema 驗證**，不可繞過
- DICOM 檔案上傳必須驗證：file size、content type、DICOM magic bytes
- Path 相關參數必須經過 sanitization，防止 path traversal
- 資料庫查詢參數**必須使用 SQLAlchemy ORM 或 parameterized query**，禁止字串拼接 SQL

### 防止 Injection

```python
# ❌ 禁止
query = f"SELECT * FROM patients WHERE id = '{patient_id}'"
db.execute(query)

# ✅ 正確
db.query(Patient).filter(Patient.patient_id == patient_id).first()
```

### 資料庫安全

- 禁止在 API response 中暴露內部 DB 欄位（如 `id` 自增欄位、內部 FK）
- Exception 訊息不可包含完整 SQL query 或 stack trace（production 環境）
- 禁止在 log 中記錄完整的 DICOM pixel data 或敏感 metadata

### 檔案系統安全

- 上傳的 DICOM 檔案儲存路徑**必須在設定的 base directory 內**
- 禁止讓用戶端控制完整的儲存路徑

---

## 10. AI 行為控制規範

### 不確定時的行為

```
如果不確定某個行為是否符合規範：
→ 停下來，說明假設，詢問確認，而不是猜測後繼續
```

- 遇到不理解的業務邏輯（如特定 DICOM workflow）→ **說明假設並請工程師確認**
- 遇到不確定的 DB 關係 → **先描述理解，請工程師確認後再修改**
- 遇到多種解法都合理 → **列出選項與 trade-off，讓工程師決定**

### 禁止的 AI 行為

- ❌ 禁止編造不存在的函數、模組、或 API endpoint
- ❌ 禁止假設 `requirements.txt` 中未列出的套件已安裝
- ❌ 禁止假設 DB 中某個欄位存在（必須先確認 model 定義）
- ❌ 禁止以「這樣更好」為理由進行不被要求的重構
- ❌ 禁止省略 `## ⚠️ 風險說明` 區塊
- ❌ 禁止在沒有測試計畫的情況下修改 service layer 核心邏輯

### 必要時提出問題

以下情境 AI **必須先提問，不可直接輸出程式碼**：

1. 任務描述會導致修改 API response schema
2. 任務描述會導致 DB migration（schema 變更）
3. 任務描述的範圍不明確（超過 3 個檔案受影響）
4. 發現任務描述與現有程式碼邏輯有矛盾

---

## 11. 測試規範

### 測試覆蓋要求

- 每次新增函數，**必須附上對應的測試案例**
- 修改現有函數行為，**必須更新對應測試並說明變更**
- Bug fix 必須附上**能重現該 bug 的 regression test**

### 測試風格規範

- 使用 `pytest` + `TestClient`（FastAPI testing）
- Test fixtures 不可隨意修改（影響所有測試）
- Integration test 與 unit test 分開管理
- DICOM 相關測試需使用 **anonymized test DICOM files**，不可使用真實患者資料

### 測試修改規範

- 禁止為了讓測試通過而修改測試預期值（應修改程式碼讓其符合正確預期）
- 禁止 skip 測試而不說明原因
- 禁止刪除測試（標記 `@pytest.mark.skip` 並附理由，由工程師決定是否移除）

---

## 12. 資料庫操作規範

### Migration 規範

- **任何 schema 變更都必須透過 migration script**（Alembic 或手動 SQL，視現有慣例）
- Migration 必須包含 `upgrade()` 與 `downgrade()`
- **只能新增欄位（ADD COLUMN）**，不可進行破壞性操作
- 新增欄位必須設定 `nullable=True` 或提供 `server_default`

### 安全的 Schema 變更（允許）

```sql
-- ✅ 允許
ALTER TABLE studies ADD COLUMN referring_physician VARCHAR(255);
CREATE INDEX idx_studies_date ON studies(study_date);
```

### 禁止的 Schema 變更

```sql
-- ❌ 禁止（破壞性）
ALTER TABLE patients DROP COLUMN patient_name;
ALTER TABLE instances RENAME COLUMN sop_instance_uid TO instance_uid;
DROP TABLE series;
```

### Upsert Logic 保護

Patient / Study / Series / Instance 的 upsert logic 是系統核心，修改前必須：

1. 完整說明現有 upsert 邏輯的理解
2. 說明修改後的行為差異
3. 提供對應的 integration test
4. 工程師確認後才可執行

---

## 13. DICOM 處理規範

### DICOM Tag 存取

```python
# ❌ 禁止（KeyError 風險）
patient_name = ds.PatientName

# ✅ 正確（安全存取）
patient_name = str(ds.get("PatientName", "")) or None
```

### UID 處理

- SOPInstanceUID、StudyInstanceUID、SeriesInstanceUID 是系統識別核心
- **禁止**修改 UID 的提取邏輯
- **禁止**對 UID 進行 normalization 或 transformation（除非明確被要求）
- UID uniqueness 違反時必須回傳明確錯誤，**不可靜默覆蓋**

### 檔案儲存

- DICOM 檔案路徑結構（如 `/{patient_id}/{study_uid}/{series_uid}/{instance_uid}.dcm`）**不可修改**
- 儲存失敗必須 rollback DB transaction
- 禁止在 DB transaction commit 前移動或刪除已存在的 DICOM 檔案

---

## 14. 錯誤處理與 Logging 規範

### Error Response 格式

現有的 error response 格式為 client 端所依賴，**不可靜默修改結構**：

```python
# 修改 error response 前，必須說明：
# 1. 現有格式是什麼
# 2. 哪些 client 可能依賴此格式
# 3. 是否為 breaking change
```

### Logging 規範

- 不可降低現有 log level（如將 `logger.error` 改為 `logger.warning`）
- 不可移除現有 log 語句
- 新增功能時，關鍵操作（資料庫寫入、檔案儲存、DICOM parsing）**必須有 log**
- Log 中**禁止**記錄：patient 姓名、完整 UID 列表（過長）、檔案完整路徑（可用相對路徑）

### Exception Handling

```python
# ✅ 正確：明確捕捉，明確處理
try:
    ds = pydicom.dcmread(file_path)
except pydicom.errors.InvalidDicomError as e:
    logger.error(f"Invalid DICOM file: {file_path}, error: {e}")
    raise HTTPException(status_code=400, detail="Invalid DICOM file format")

# ❌ 禁止：靜默吞掉 exception
try:
    ds = pydicom.dcmread(file_path)
except Exception:
    pass
```

---

## 15. 擴充區塊（保留）

> 以下區塊為未來擴充保留，工程師可依需求填入。

### 15.1 Agent Behavior Rules（保留）

```
# TODO: 未來可在此定義不同 AI agent 的行為差異
# 例如：review-only agent vs. code-writing agent 的不同約束
```

### 15.2 Dev Workflow Rules（保留）

```
# TODO: 未來可在此定義：
# - Branch naming convention
# - PR review checklist for AI-generated code
# - How to verify AI-generated migrations before applying
```

### 15.3 Domain-Specific Rules（保留）

```
# TODO: 未來可在此定義：
# - DICOM conformance statement 相關約束
# - PACS interoperability 規範
# - HL7 / FHIR 整合規範（如有）
```

### 15.4 Additional Protected Modules（保留）

```
# TODO: 隨系統成長，在此列出新增的關鍵保護模組
```

---

## 文件維護

| 項目 | 說明 |
|---|---|
| 文件版本 | v1.0 |
| 建立日期 | 2026-05-07 |
| 適用對象 | 所有 AI coding agents 與參與此 repo 的工程師 |
| 更新觸發條件 | 架構變更、新增關鍵模組、規範調整 |
| 更新方式 | PR + 工程師 review，不可由 AI 自行修改本文件 |

> ⚠️ **本文件本身亦受保護**：AI agent 不可自行修改 CLAUDE.md，所有修改必須由工程師發起並 review。
