# COMMIT_GUIDE.md — 標準 Commit 流程規範

> **文件定位**：本檔規範本專案的 **Git workflow 與 commit 流程**。
> 所有工程師與 AI coding agent 進行 commit 前必須完整遵守本文件。
>
> **與其他文件的關係**：
> - [CLAUDE.md](./CLAUDE.md) — AI 行為約束（為什麼這樣做）
> - [PROGRESS.md](./PROGRESS.md) — 專案現況（做到哪了）
> - **本檔** — 怎麼把改動 commit 進去（怎麼做）

---

## 目錄

1. [核心原則](#1-核心原則)
2. [標準開發 → Commit 流程（七步法）](#2-標準開發--commit-流程七步法)
3. [Branch 命名規範](#3-branch-命名規範)
4. [Commit Message 規範（Conventional Commits）](#4-commit-message-規範conventional-commits)
5. [Commit 前 Checklist（醫療系統強制）](#5-commit-前-checklist醫療系統強制)
6. [PROGRESS.md 更新時機（含 6.0 同步門檻分級）](#6-progressmd-更新時機)
7. [常見情境範例（含 7.5 Commit 拆解技巧）](#7-常見情境範例end-to-end)
8. [禁止行為（四級分類，含 .gitignore 強制清單）](#8-禁止行為四級分類)
9. [誤操作救援](#9-誤操作救援)
10. [未來擴充規範（占位：Migration / CI / 測試分層）](#10-未來擴充規範占位)
11. [文件維護](#11-文件維護)

---

## 1. 核心原則

```
1. 測試沒過 → 不准 commit
2. 一個 commit 做一件事
3. Commit message 要讓三個月後的自己看得懂
4. PROGRESS.md 必須與 commit 同步更新
5. 醫療系統沒有「應該沒問題」，commit 前必須驗證
6. 不可逆的破壞性操作（force push、reset --hard、clean -fdx）一律先停手確認
```

---

## 2. 標準開發 → Commit 流程（七步法）

每次開發完成後，依序執行以下七步：

### Step 1 — 建立 / 切換 branch

```bash
# 從最新的 master 開始
git checkout master
git pull origin master

# 切到新 branch（命名規則見第 3 節）
git checkout -b feature/add-series-query
```

### Step 2 — 開發與本地測試

```bash
# 開發過程中隨時跑測試
pytest tests/ -v

# 只跑某個檔案
pytest tests/test_query_api.py -v
```

### Step 3 — 跑完整測試套件（**必須全部通過**）

```bash
pytest tests/ -v
```

> ⚠️ **任一測試失敗即不可進入 Step 4。**
> 失敗時的處理優先序：
> 1. 修程式碼讓測試通過（首選）
> 2. 修測試讓它符合正確預期（需在 commit message 明確說明為何修測試）
> 3. **禁止** skip 測試或註解測試以求通過

### Step 4 — 完成 Commit 前 Checklist

依照 [第 5 節 Checklist](#5-commit-前-checklist醫療系統強制) 逐項確認，全部 ✅ 才繼續。

### Step 5 — 同步更新 PROGRESS.md

依照 [第 6 節 更新時機](#6-progressmd-更新時機)，更新對應區塊。

> 💡 PROGRESS.md 的更新通常**與功能 commit 同一個 commit**，或**緊接其後的獨立 docs commit**。詳見第 7 節範例。

### Step 6 — Stage 與 Commit

```bash
# 明確列出要 commit 的檔案（避免 git add . 誤抓敏感檔）
git add db_service.py models.py tests/test_dicom_service.py PROGRESS.md

# 確認暫存內容（必看）
git status
git diff --cached

# Commit（格式見第 4 節）
git commit -m "feat(query): 新增以 Study UID 列出 series 的查詢端點"
```

### Step 7 — Push（必要時開 PR）

```bash
# 第一次 push 用 -u 設定 upstream
git push -u origin feature/add-series-query

# 後續 push
git push

# 如需 PR
gh pr create --title "feat(query): 新增以 Study UID 列出 series 的查詢端點" --body "..."
```

---

## 3. Branch 命名規範

### 格式

```
<type>/<short-kebab-case-description>
```

### Type 對照表

| Type | 用途 | 範例 |
|---|---|---|
| `feature/` | 新增功能 | `feature/ai-segmentation-impl` |
| `fix/` | 修 bug | `fix/upsert-race-condition` |
| `docs/` | 純文件變更 | `docs/update-progress` |
| `refactor/` | 重構（不改行為） | `refactor/storage-backend-abstraction` |
| `test/` | 純測試新增 / 修改 | `test/add-validator-edge-cases` |
| `chore/` | 雜務（依賴升級、設定調整） | `chore/bump-pydicom-2.4.5` |
| `hotfix/` | production 緊急修復 | `hotfix/upload-500-error` |

### 命名規則

- 使用 **kebab-case**（小寫 + 連字號）
- 描述使用**英文**，**不超過 50 字元**
- 避免人名、日期、ticket id（這些放 commit message / PR description）
- 一個 branch **對應一個明確任務**

### ❌ 不良範例

```
feat-add-stuff           # 缺斜線分隔
feature/Update_API       # 用了底線與大寫
feature/peter-fix-bug    # 含人名
fix/2026-05-08-issue     # 含日期
feature/新增上傳功能       # branch 名稱用中文（檔案系統與 CI 相容性差）
```

### ✅ 良好範例

```
feature/dicom-multi-modality-support
fix/instance-404-on-empty-uid
docs/add-commit-guide
refactor/db-service-extract-helpers
```

---

## 4. Commit Message 規範（Conventional Commits）

### 4.1 語言規則（本專案標準）

> **`type(scope):` 一律用英文；subject 與 body 一律用繁體中文。**
>
> 此規則對齊本專案既有 git log 慣例（如 `test(refactor): 重構 FastAPI...`、`docs(quickstart): 更新測試執行指令路徑...`），請維持一致。

### 4.2 格式

```
<type>(<scope>): <繁體中文 subject>

[optional 繁體中文 body]

[optional footer]
```

### 4.3 Type 對照表

| Type | 用途 |
|---|---|
| `feat` | 新功能（對應 branch `feature/`） |
| `fix` | bug 修復（對應 `fix/`、`hotfix/`） |
| `docs` | 純文件變更 |
| `refactor` | 重構（行為不變） |
| `test` | 測試新增 / 修改 |
| `chore` | 雜務、設定、依賴 |
| `perf` | 效能優化 |
| `style` | 格式調整（不影響邏輯） |
| `build` | 建置系統 |
| `ci` | CI/CD 變更 |

### 4.4 Scope（建議）

對應本專案模組：

```
api          - main.py / 路由
service      - db_service.py / storage.py
model        - models.py
db           - db.py / migration
validation   - validation/
storage      - storage_backend.py
test         - tests/
config       - config.py / .env
docs         - 文件
progress     - PROGRESS.md 專屬
```

### 4.5 Subject 規範

- 使用**繁體中文**
- 用**動詞開頭**（新增 / 修正 / 更新 / 移除 / 重構）
- **不超過 70 字元**（含中文字元）
- 結尾**不加句號**
- 簡述「做了什麼」，**不寫過程**

### 4.6 Body 規範（多行 commit）

- 與 subject 中間隔**一行空行**
- 使用**繁體中文**
- 解釋 **為什麼改**，而非 **改了什麼**（diff 已說明）
- 醫療系統建議列出三項影響評估：API contract / DB schema / 測試
- 若該 commit 屬於「強制同步 PROGRESS.md」類型（見 [第 6.0 節](#60-progressmd-同步門檻分級)），需於 body 末尾說明同步內容

### 4.7 Footer 規範

- Breaking change：`BREAKING CHANGE: <繁中描述>`
- 關聯 issue：`Closes #123`
- AI 協作標註（若適用）：`Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`

### 4.8 ✅ 良好範例

**單行 commit**：
```
feat(api): 新增以 Study UID 列出 series 的查詢端點
fix(service): 修正 instance upsert 在重試時建立重複資料的問題
docs(progress): 將 AI 分割功能標記為進行中
test(validation): 補上缺漏 Modality tag 的邊界測試案例
refactor(storage): 抽出 storage 路徑解析邏輯為獨立 helper
chore(deps): 升級 pydicom 至 2.4.5
```

**多行 commit**：
```
feat(validation): 擴充 Modality 白名單以支援 CT 與 MR

原因：
- 既有白名單僅允許 US,擋住臨床端 CT/MR 上傳請求
- 臨床團隊提出多模態支援需求

影響評估:
- API contract: 不變
- DB schema: 不變
- 測試: 新增 4 個案例於 test_validators.py

PROGRESS.md 已同步更新:
- 6.6 多 Modality 缺口移除
- 1. 已完成功能新增此項
```

**含 Breaking Change**：
```
feat(api)!: 將 /studies 回應格式改為分頁結構

BREAKING CHANGE: GET /studies 改回傳
{ "items": [...], "total": N }, 原為陣列直接回傳

遷移方式: client 端需從 response.items 讀取資料
PROGRESS.md 已同步更新
```

### 4.9 ❌ 不良範例

```
update                                          # 沒 type、沒 scope、沒內容
fix bug                                         # 沒說明哪個 bug
feat: 加了一些東西                                # 太模糊
WIP                                             # 不可進主幹
test 測試通過                                    # 不是動詞開頭、語意空洞
修了 upsert.                                    # 缺 type/scope、用了句號
feat(api): Add new endpoint for listing series  # 違反語言規則(subject 應為繁中)
```

---

## 5. Commit 前 Checklist（醫療系統強制）

> ⚠️ 本專案是**醫療影像系統**，資料錯誤可能影響診斷。**每次 commit 前必須逐項確認**。

### A. 測試與品質

- [ ] `pytest tests/ -v` **全部通過**（無 fail、無 error、無 skip 未說明）
- [ ] 新增 / 修改的函數**有對應測試**
- [ ] 測試使用 **anonymized DICOM**,無真實患者資料
- [ ] 沒有為了讓測試通過而修改測試預期值（除非有正當理由並於 commit message 說明）

### B. API Contract（🔴 最高保護）

- [ ] **未修改**現有 endpoint 路徑
- [ ] **未修改** response schema 既有欄位的名稱或型別（新增欄位 OK）
- [ ] **未修改** HTTP status code 行為（200 / 400 / 404 / 500）
- [ ] **未修改** error response 格式

### C. DB Schema（🔴 最高保護）

- [ ] **無破壞性 migration**（DROP COLUMN / DROP TABLE / RENAME COLUMN）
- [ ] **未修改** SQLAlchemy model 既有欄位名稱
- [ ] 新增欄位**設為 `nullable=True`** 或提供 `server_default`
- [ ] **未變更** patient / study / series / instance 的 upsert 邏輯（除非任務明確要求）
- [ ] **未移除** unique constraint 或 index

### D. DICOM 處理

- [ ] DICOM tag 存取使用 `.get()` fallback,**未使用直接屬性存取**（避免 KeyError）
- [ ] **未修改** UID 提取邏輯（SOP / Study / Series InstanceUID）
- [ ] DICOM parsing 失敗有明確 log + error response,**未靜默吞掉 exception**

### E. 安全與隱私

- [ ] Log 中**未包含** patient 姓名、完整 UID、檔案絕對路徑
- [ ] 未在 API response 中暴露內部 DB 欄位（如自增 `id`、內部 FK）
- [ ] 資料庫查詢使用 ORM 或 parameterized query,**無字串拼接 SQL**
- [ ] **未 commit** `.env`、credentials、private key、token 等敏感檔
- [ ] **未 commit** 真實患者 DICOM 資料

### F. 依賴與設定

- [ ] **未升級** `requirements.txt` 套件版本（除非任務明確要求）
- [ ] **未新增** 大型依賴（Celery / Redis / 其他）而無說明
- [ ] **未移除** 既有依賴

### G. 文件同步

- [ ] 若該 commit type 屬於「**強制同步**」（見 [第 6.0 節](#60-progressmd-同步門檻分級)），**PROGRESS.md 已同步更新**
- [ ] 若新增端點,已更新 PROGRESS.md 的 API 端點狀態表
- [ ] 若修改架構,已更新 IMPLEMENTATION.md
- [ ] 若修改 API 行為,已更新 README.md / QUICKSTART.md

### H. Git 衛生

- [ ] `git status` 確認沒有意外的 untracked 檔
- [ ] `git diff --cached` 確認暫存內容只包含**本次任務**的變更
- [ ] **未使用** `git add .` / `git add -A`（容易誤抓 `.env`、`__pycache__`、大檔）
- [ ] commit message 符合第 4 節規範（type/scope 英文 + subject/body 繁中）

### I. Commit 粒度（單一變更原則）

- [ ] 本 commit **未混合** feat 與 refactor
- [ ] 本 commit **未混合** formatting 變更與邏輯變更
- [ ] 本 commit **未混合** 依賴升級與功能 / bug 變更
- [ ] 本 commit **未包含** 多個無關的 fix
- [ ] 若以上有混合需求，已用 [第 7.5 節 Commit 拆解技巧](#75-commit-拆解技巧) 拆開

> 💡 **逐項打勾**而非整體掃過。任何一項 ❌ → 不可 commit。

---

## 6. PROGRESS.md 更新時機

PROGRESS.md 的狀態流轉為：

```
已知缺口 ──→ 下一步 ──→ 進行中 ──→ 已完成
   (6)        (5)         (4)        (1)
```

### 6.0 PROGRESS.md 同步門檻分級

> ⚠️ **重要設計理由**：強制每個 commit 都更新 PROGRESS.md 會導致 friction 過高，
> 長期會出現「亂寫」或「乾脆不寫」的失控狀態。
> 因此採**分級制**：高層級狀態變更**強制同步**，低層級事務性變更**不強制**。

#### 強制同步（必須更新 PROGRESS.md，否則不可 commit）

| Commit 類型 | 強制更新區塊 |
|---|---|
| `feat` 新功能 | 1. 已完成功能 + 2. API 端點狀態表（若新增端點） |
| `feat!` / `fix!` / Breaking change | 上述 + 文件中標註 `BREAKING` |
| Architecture change（影響分層 / 跨模組重構） | 1. + 7. 目錄結構（若檔案結構改變） |
| Roadmap state change（任務開始 / 完成 / 取消 / 排序） | 4. 進行中 / 5. 下一步 / 6. 已知缺口（依情境） |

#### 建議同步（視情況更新，非強制）

| Commit 類型 | 建議時機 |
|---|---|
| 中型 `refactor`（≥ 3 檔或跨模組） | 影響架構理解時，更新 7. 目錄結構說明 |
| 中大型 `fix`（修正行為或對外可見的錯誤） | bug 在已知缺口列出時，需移除對應條目 |

#### 不需強制同步

| Commit 類型 | 說明 |
|---|---|
| 小 `fix`（typo / 內部錯誤訊息 / 非業務邏輯） | 但若該 bug 在 6. 已知缺口列出，必須移除對應條目 |
| `docs`（非 PROGRESS.md 之文件） | — |
| `test`（純測試新增 / 修改） | 大型測試補齊可選擇更新「3. 測試覆蓋簡況」 |
| `chore`（依賴升級、設定調整） | — |
| `style`（格式調整，無邏輯變動） | — |
| `perf`（純效能優化，無行為變更） | — |
| `ci` / `build`（CI 與建置變更） | — |

> 💡 **快速判斷法**：問自己「**三個月後別人讀 PROGRESS.md 想知道這次改動嗎？**」
> 是 → 強制同步；否 → 不強制。

---

### 6.1 開始新任務時

**動作**：將項目從「下一步」搬到「進行中」

**範例 patch**：
```diff
## 4. 進行中

- > **目前無進行中項目。**
+ - **AI 分割端點實作** — 開始於 2026-05-10,預計 5/20 完成
+   - 範圍：實作 `/ai/segment/{id}` 與 `/ai/result/{id}` 真實邏輯
+   - 對應 branch:`feature/ai-segmentation-impl`

## 5. 下一步（短期、已排程）

- - AI 分割端點實作
  - ...
```

**對應 commit**：
```
docs(progress): 將 AI 分割功能標記為進行中
```

---

### 6.2 完成功能時

**動作**：
1. 從「進行中」移除
2. 加入「已完成功能」對應區塊
3. 若有對應「已知缺口」項目,從第 6 節移除
4. 若新增 / 變更端點,更新 API 端點狀態表

**範例 patch**：
```diff
## 1. 已完成功能

### 核心業務
+ - [x] AI 分割（POST /ai/segment/{id}、GET /ai/result/{id}）

## 2. API 端點狀態表

- | POST | `/ai/segment/{id}` | 觸發 AI 分割 | ⚠️ Stub | 僅回傳 ... |
+ | POST | `/ai/segment/{id}` | 觸發 AI 分割 | ✅ 完整 | 整合 model X |

## 4. 進行中

+ > **目前無進行中項目。**
- - **AI 分割端點實作** — 開始於 ...

## 6. 已知缺口

- ### 6.1 AI 分割功能（業務）
- - **缺什麼**：...
```

**對應 commit**（與功能 commit 同一個 PR 內）：
```
feat(api): 實作 AI 分割端點 /ai/segment 與 /ai/result

docs(progress): 將 AI 分割功能標記為已完成
```

---

### 6.3 發現新缺口時

**動作**：在「已知缺口」新增條目

**範例 patch**：
```diff
## 6. 已知缺口

+ ### 6.11 DICOM Pixel Data 驗證
+ - **缺什麼**：目前驗證層僅檢查 metadata,未驗證 pixel data 完整性
+ - **什麼時候會痛**：上傳了損毀但 metadata 完整的 DICOM 時
+ - **相依**：pydicom pixel_array 解析 + 檢驗策略
```

**對應 commit**：
```
docs(progress): 新增 pixel data 驗證至已知缺口
```

---

### 6.4 更新觸發條件總表

| 情境 | 更新區塊 | Commit type |
|---|---|---|
| 開始新任務 | 4. 進行中 | `docs(progress)` |
| 完成功能 | 1. + 2. + 4. + 6.（多處） | 與功能 commit 同 PR |
| 發現缺口 | 6. 已知缺口 | `docs(progress)` |
| 改變優先序 | 5. 下一步 | `docs(progress)` |
| 任務取消 | 4. → 6.（搬回缺口） | `docs(progress)` |

---

## 7. 常見情境範例（End-to-End）

### 情境 A：新增功能（含測試）

```bash
# 1. 切 branch
git checkout master && git pull
git checkout -b feature/series-query-by-modality

# 2. 開發 + 測試
# ... 改 db_service.py / main.py / tests/test_query_api.py ...
pytest tests/ -v

# 3. 完成 Checklist（第 5 節 A~H 全項）
# 4. 更新 PROGRESS.md（已完成功能 + API 端點狀態表）
# 5. Commit
git add db_service.py main.py tests/test_query_api.py PROGRESS.md
git commit -m "feat(api): 新增以 Modality 過濾 series 的查詢功能

原因:
- 臨床端需依 Modality 批次審閱 series
- 既有實作需先撈全部再 client 端過濾,效能不佳

影響評估:
- API contract: 新增 query param ?modality=US（向後相容,非 breaking）
- DB schema: 不變
- 測試: 新增 3 個案例於 test_query_api.py

PROGRESS.md 已同步更新:
- 1. 已完成功能新增此項
- 2. API 端點狀態表更新"

# 6. Push
git push -u origin feature/series-query-by-modality
```

---

### 情境 B：Bug 修復

```bash
git checkout -b fix/upsert-duplicate-instance

# ... 修 bug + 寫 regression test ...
pytest tests/ -v

git add db_service.py tests/test_dicom_service.py
git commit -m "fix(service): 修正同 SOP UID 並發上傳產生重複資料的問題

原因:
- 兩個 request 同時上傳同一 SOP UID 時,DB unique constraint 雖會擋下,
  但錯誤訊息直接洩漏到 client,且部分檔案已寫入 storage 未 rollback

修正:
- INSERT 前加上 existence check
- 寫入失敗時 rollback storage 檔案
- 新增 regression test test_upsert_duplicate_instance

影響評估:
- API contract: 不變
- DB schema: 不變
- 行為差異: 重複上傳改回傳 200(idempotent),原為 500"
```

---

### 情境 C：純文件變更

```bash
git checkout -b docs/update-progress-q2

# ... 編輯 PROGRESS.md ...

git add PROGRESS.md
git commit -m "docs(progress): 將 AI 分割功能標記為進行中"
```

---

### 情境 D：測試補齊

```bash
git checkout -b test/validator-edge-cases

# ... 新增測試 ...
pytest tests/test_validators.py -v

git add tests/test_validators.py
git commit -m "test(validation): 補上空 UID 與超長 tag 的邊界測試"
```

---

### 7.5 Commit 拆解技巧

> 當你發現本地修改混合了多種類型（feat + refactor + docs 全擠在一起），**禁止直接 commit**。
> 使用以下三種方式之一拆開（對應 [第 5 節 Checklist I](#i-commit-粒度單一變更原則)）。

#### 方式 1：`git stash` + 分次 commit（最常用）

```bash
# 暫存所有變更
git stash

# 取出後分次 add 不同類型
git stash pop

# 第一個 commit：只 add 功能相關檔案
git add main.py db_service.py
git commit -m "feat(api): 新增 series 查詢端點"

# 第二個 commit：再 add 重構相關檔案
git add storage.py
git commit -m "refactor(storage): 抽出路徑解析 helper"

# 第三個 commit：最後 add 測試
git add tests/test_query_api.py
git commit -m "test(api): 補上 series 查詢測試"
```

#### 方式 2：`git add -p` 互動式選 hunk（同檔案內混合時）

當**同一個檔案**內混了 feat 與 refactor 時：

```bash
git add -p main.py
# 互動選項：
#   y = stage 此 hunk
#   n = 不 stage
#   s = 切割成更小的 hunk
#   e = 手動編輯要 stage 的內容
#   q = 離開
```

stage 完一類後 commit，再用同樣方式處理剩下的。

#### 方式 3：開始工作前先規劃

於 branch 描述或 PR description 先列出預計的 commit 結構：

```
PR scope (feature/series-query-by-modality):
- commit 1: feat(api): 新增端點與 service 層邏輯
- commit 2: test(api): 對應測試案例
- commit 3: docs(progress): PROGRESS.md 同步
```

工作時依序提交，避免事後拆解的麻煩。

#### ⚠️ AI agent 規範

若 AI agent 一次完成了**跨多種類型**的變更，**stage 前必須主動詢問工程師**：

```
「本次修改包含 X 個 feat / Y 個 refactor / Z 個 docs，
 建議拆成 N 個 commit，請確認順序與粒度。」
```

**不可自行決定全合一 commit**。

---

## 8. 禁止行為（四級分類）

> 本節對齊 [CLAUDE.md 第 5 節](./CLAUDE.md#5-禁止行為清單),並擴充 git workflow 專屬規則。
>
> 分四級：**8.1 強制禁止 / 8.2 需明確授權 / 8.3 內容層面 / 8.4 流程層面**。

---

### 8.1 Git 危險操作（強制禁止 — 任何情況不可執行）

| 操作 | 風險 | 替代方案 |
|---|---|---|
| `git push --force` 到 `master` / `main` / `release/*` | 覆蓋 production 歷史,無法復原 | 開新 branch + revert PR |
| `git push --force`（不加 `--force-with-lease`） | 直接覆蓋他人 push,無安全網 | 用 `--force-with-lease` 並先確認 upstream |
| `git filter-branch` / `git filter-repo` 重寫已 push 的歷史 | 整個 repo 歷史錯亂,所有 clone 失效 | 出問題的 commit 用新 commit revert |
| `git commit --no-verify` 跳過 pre-commit hook | 繞過品質檢查,可能引入未測試的程式碼 | 修正 hook 報的問題 |
| `git rebase -i` 重寫**已 push** 的歷史 | 等同 force push,協作者基於舊歷史會錯亂 | 只在**未 push** 的本地 commit 上使用 |
| 直接在 `master` / `main` 上 commit | 跳過 PR review,違反 medical system 變更紀錄要求 | 切 branch + 開 PR |
| `git push --tags --force` | 覆蓋已發布的 tag,版本追蹤錯亂 | 新增 tag 不要覆蓋 |

---

### 8.2 Git 危險操作（需明確授權 — 工程師確認後才可執行）

> 這些操作**有正當使用情境**,但會丟失工作或誤覆蓋,執行前必須：
> 1. 確認自己在做什麼
> 2. 必要時備份（`git stash` 或開臨時 branch）
> 3. 對於 AI agent:**必須先停手詢問工程師,不可自行執行**

| 操作 | 風險 | 安全使用方式 |
|---|---|---|
| `git reset --hard <ref>` | **丟失所有未 commit 的工作**,reflog 也救不回未 staged 的修改 | 先 `git stash`、確認沒有未存檔工作再執行 |
| `git checkout .` / `git restore .` | 蓋掉所有未 staged 修改,**無法復原** | 改用 `git stash` 暫存後再操作 |
| `git clean -fd` / `git clean -fdx` | 刪除所有 untracked 檔,可能含 `.env` / 患者資料 / 未加進 git 的工作 | 先 `git clean -nd` dry-run 看會刪什麼 |
| `git branch -D <branch>` 強刪未 merge branch | 丟失該 branch 上未 push / 未 merge 的工作 | 先確認已 merge 或已 push;優先用 `-d`(safe delete) |
| `git commit --amend` **已 push** 的 commit | 等同 force push,協作者會錯亂 | 只在**未 push** 的本地 commit 上 amend;若需修正已 push 的內容,改用新 commit |
| 在共享 feature branch 上 `git rebase` | 重寫他人也在用的歷史,push 時被擋,force push 又會覆蓋對方工作 | 共享 branch 用 `git merge`,僅個人 branch 用 rebase |
| `git push --force-with-lease` 到自己的 feature branch | 若有人 base 在你 branch 上,會覆蓋對方工作 | 先確認 branch 沒有其他協作者 |
| `git stash drop` / `git stash clear` | 永久刪除 stash,reflog 不保留 | 改用 `git stash pop`(成功後自動移除) |

---

### 8.3 內容層面（敏感檔案與資料）

#### 8.3.1 `.gitignore` 強制包含項

`.gitignore` **必須**包含以下項目，缺漏視同違反規範：

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
build/
dist/

# 虛擬環境
.venv/
venv/
env/

# IDE
.idea/
.vscode/

# OS
.DS_Store
Thumbs.db

# 測試與快取
.pytest_cache/
.coverage
htmlcov/

# 環境變數與機敏
.env
.env.local
.env.*.local
*.pem
*.key

# 醫療資料（本專案專屬）🔴
storage/                  # 本地 DICOM 儲存目錄（runtime 產生，不可進 git）
*.dcm                     # DICOM 檔不可進 git
test_dicom_files/         # 既有規則保留

# Log
*.log
logs/
```

> ⚠️ **醫療系統專屬保護**：`storage/` 與 `*.dcm` **必須永遠在 .gitignore 中**。
> 一旦真實 DICOM 檔案進入 git 歷史，等同 patient data 外洩，需走 [第 9.6 節事故處理流程](#96-env--敏感資料誤-commit-並-push-出去)。

#### 8.3.2 禁止內容

- ❌ **禁止** commit 真實患者 DICOM 資料（必須使用 anonymized 測試檔）
- ❌ **禁止** commit `.env`、credentials、token、private key、API key
- ❌ **禁止** commit `.venv/`、`__pycache__/`、`.pytest_cache/`、IDE 設定
- ❌ **禁止** commit 大檔（> 10 MB）未經工程師確認
- ❌ **禁止** 在 commit message / code comment 中寫入患者姓名、ID、UID
- ❌ **禁止** silent behavior change（行為改了但 commit message 沒提）

---

### 8.4 流程層面

#### 8.4.1 流程禁止項

- ❌ **禁止** 測試未通過就 commit（含 skip 未說明）
- ❌ **禁止** 該 commit type 屬於「強制同步」但 PROGRESS.md 不同步（見 [6.0 節](#60-progressmd-同步門檻分級)）
- ❌ **禁止** commit message 帶 `WIP`、`TODO`、`xxx` 進主幹
- ❌ **禁止** AI agent 自行修改 [CLAUDE.md](./CLAUDE.md)（CLAUDE.md 限工程師發起）
- ❌ **禁止** AI agent 自行執行 8.1 / 8.2 的危險操作（必須先停手詢問）
- ❌ **禁止** 跳過 PR 直接 merge 到 master（除非 hotfix 並事後補 PR）

#### 8.4.2 Commit 粒度禁止項

> 對齊 [第 5 節 Checklist I](#i-commit-粒度單一變更原則) 與 [第 7.5 節 Commit 拆解技巧](#75-commit-拆解技巧)。

- ❌ **禁止** 一個 commit 混雜 `feat` + `refactor`
- ❌ **禁止** 一個 commit 混雜 formatting / style 變更與 logic 變更
- ❌ **禁止** 一個 commit 混雜依賴升級（`chore(deps)`）與功能 / bug 變更
- ❌ **禁止** 一個 commit 包含多個**無關**的 fix（同一個 bug 的多檔修正可以一起）
- ❌ **禁止** 一個 commit 混雜多個無關變更（feat + refactor + chore + docs 全擠在一起）
- ❌ **禁止** 在無「拆解規劃」的情況下啟動跨多個變更類型的開發

---

## 9. 誤操作救援

> 「**做錯事先別慌,Git 多數情況救得回來**」
>
> 但有三種情況**永遠救不回來**：
> 1. 未 commit 的工作被 `reset --hard` / `checkout .` 蓋掉
> 2. 未 add 的 untracked 檔被 `clean -fd` 刪掉
> 3. 已 push 到 public 的敏感資料(必須改密碼,而非靠 git 清除)

---

### 9.1 救回 `git reset --hard` 後消失的 commit

**前提**：commit 已存在過(已 commit 但被 reset 蓋掉)

```bash
# 查看所有 HEAD 移動紀錄(包含被 reset 的 commit)
git reflog

# 範例輸出:
# abc1234 HEAD@{0}: reset: moving to HEAD~3
# def5678 HEAD@{1}: commit: feat(api): 新增端點   ← 這個是要救的
# ...

# 救回方式
git reset --hard def5678

# 或建立新 branch 指到該 commit
git checkout -b recovery def5678
```

---

### 9.2 救回誤刪的 branch

```bash
git reflog
# 找到該 branch 最後的 commit hash
git checkout -b <branch-name> <hash>
```

---

### 9.3 救回 `git commit --amend` 之前的版本

```bash
git reflog
# 找到 amend 之前的 commit hash(通常是 HEAD@{1})
git reset --hard HEAD@{1}
```

---

### 9.4 救回誤 merge / 誤 rebase

```bash
# Merge 救援
git reflog
git reset --hard <merge 之前的 hash>

# Rebase 救援(rebase 過程中可用)
git rebase --abort

# Rebase 完成後才發現有問題
git reflog
git reset --hard <rebase 之前的 hash>
```

---

### 9.5 救援未 staged 的修改 — **救不回來**

以下操作會**永久消滅未 staged 的工作**,reflog 完全幫不上忙：

- `git reset --hard`(會清掉 working tree)
- `git checkout .` / `git checkout -- <file>`
- `git restore .` / `git restore <file>`
- `git stash drop` 後

**唯一的預防方式**：操作前先 `git stash` 或 `git add` + 暫時 commit。

---

### 9.6 `.env` / 敏感資料誤 commit 並 push 出去

> ⚠️ **這是醫療系統最嚴重的事故,必須當作 credential 已外洩處理。**

**正確處理流程**：

1. **立刻** rotate 所有外洩的 credential(改密碼、撤銷 token、重新發 key)
2. 通知工程主管與資安窗口
3. 從 git 歷史移除(僅是降低後續暴露,**不可視為已修復**)：
   ```bash
   # 使用 git filter-repo(需團隊全員配合 re-clone)
   git filter-repo --path .env --invert-paths
   git push --force-with-lease
   ```
4. 更新 `.gitignore` 防止再次發生
5. 事後寫 incident report

> ❌ **錯誤心態**:「我 force push 把它移除就沒事了」— 一旦 push 過,假設已被爬蟲/協作者 clone,**credential 必須當已外洩**。

---

### 9.7 緊急救援流程(SOP)

任何時候發現「我剛才好像做錯了」,依此順序處理：

```
1. 停手 — 不要再下任何 git 指令
2. git reflog — 看清楚做了什麼、什麼還在
3. 評估 — 哪些工作可救?哪些已永久消失?
4. 在新 branch 操作 — 不要直接覆蓋當前 branch
5. 必要時尋求協助 — 醫療系統不要單獨硬上
```

> 💡 **AI agent 特別注意**：執行 8.1 / 8.2 的指令前必須停手確認,即使工程師口頭授權,也要顯示具體指令並再次確認。

---

## 10. 未來擴充規範（占位）

> 以下章節對應 [PROGRESS.md 已知缺口](./PROGRESS.md#6-已知缺口中長期未排程)，
> 將在對應功能 / 基礎設施導入時，由獨立 PR 補齊內容。
> **目前僅占位，相關規範尚未生效。**

### 10.1 DB Migration 規範（待 Alembic 導入後新增）

- **計畫範圍**：
  - Migration 命名規範
  - Migration rollback 機制
  - Migration review 流程
  - Backward compatibility strategy（rename column 兩階段、nullable→non-nullable plan）
  - Production migration 前必須備份
- **觸發條件**：導入 Alembic 之 PR
- **對應 PROGRESS.md 缺口**：6.2 Database Migration 框架

### 10.2 CI / PR Gate 規範（待 CI 導入後新增）

- **計畫範圍**：
  - PR merge 必須通過：pytest 全綠、lint 全綠、type check 全綠
  - Branch protection rules（master 禁止直接 push、要求 review、要求 status check）
  - Pre-commit hook 整合（pytest / black / mypy）
  - PR 觸發測試範圍策略
- **觸發條件**：建立 `.github/workflows/` 之 PR
- **目前狀態**：所有 enforcement 靠**人工自律 + 本檔 Checklist**

### 10.3 測試分層規範（待測試重組 PR 完成後新增）

- **計畫範圍**：
  - `tests/unit/` / `tests/integration/` / `tests/e2e/` 目錄結構
  - 各層測試的隔離邊界與 fixture 範圍
  - PR 觸發策略：本地最少跑 unit + integration、CI 跑全套
  - 跑全套測試耗時控制目標
- **觸發條件**：`tests/` 結構重組之 PR
- **目前狀態**：33 個測試集中在 `tests/` 下，無分層

---

## 11. 文件維護

| 項目 | 說明 |
|---|---|
| 文件版本 | v1.2 |
| 建立日期 | 2026-05-08 |
| 最後修訂 | 2026-05-08 |
| 修訂紀錄 | v1.0 初版 → v1.1 補齊 force push 風險與誤操作救援 → v1.2 PROGRESS.md 同步分級、Commit 粒度規範、`.gitignore` 強制清單、Commit 拆解技巧、第 10 節未來擴充占位 |
| 適用對象 | 所有工程師、AI coding agent |
| 強制力 | **本檔規則為強制標準**，違反需於 commit message 明確說明理由 |
| 更新觸發條件 | 工作流程變更、新增 commit type、PROGRESS.md 結構調整、新發現的 git 風險、未來占位章節升格為正式規範 |
| 更新方式 | PR + 工程師 review，AI agent 可在工程師指示下協助修改 |

> ⚠️ **未來所有 commit 流程依此文件執行。**
>
> 如本檔與既有實踐衝突，以本檔為準；
> 如本檔與 [CLAUDE.md](./CLAUDE.md) 衝突，**以 CLAUDE.md 為準**（CLAUDE.md 為最高層級規範）。
