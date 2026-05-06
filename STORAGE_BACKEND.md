---
docspec: "2.0"
type: ARCHITECTURE
title: "Storage Backend 設計文件"
version: "2.0.0"
status: "approved"
---

# Storage Backend 設計文件

## 概述

`storage_backend.py` 是 storage 的抽象層，讓上層程式碼（API endpoint）不需要知道檔案實際存在哪裡。目前實作 local 檔案系統，未來可無縫替換成 S3 或其他儲存服務。

## 檔案位置

`storage_backend.py` 位於專案根目錄，與 `db.py`、`storage.py` 同層：

```text
project-root/
├── storage_backend.py   ← here
├── db.py
├── storage.py
├── main.py
└── ...
```

## 介面定義

所有 backend 實作都繼承 `StorageBackend`，並且必須實作以下三個方法：

| 方法 | 說明 |
|---|---|
| `exists(path)` | 確認檔案是否存在 |
| `read_bytes(path)` | 讀取檔案內容，回傳 `bytes` |
| `absolute_path(path)` | 回傳可供 `FileResponse` 使用的絕對路徑（僅限 local） |

`path` 統一使用相對路徑，對應資料庫欄位 `Instance.file_path`，例如 `dicom/xxx.dcm`。

## 目前實作

### LocalStorageBackend

以 `.env` 中的 `UPLOAD_STORAGE_PATH` 作為 base directory，並與 `file_path` 組合成完整路徑。

初始化位置：`main.py` module level

```python
from storage_backend import LocalStorageBackend
from config import settings

storage = LocalStorageBackend(base_dir=settings.UPLOAD_STORAGE_PATH)
```

## 未來擴充：S3 遷移

新增 `S3StorageBackend(StorageBackend)` 並實作上述三個方法。`main.py` 只需替換初始化的 backend instance，其餘 endpoint 程式碼不需要修改。

```python
# 切換只需改這一行
storage = S3StorageBackend(bucket=settings.S3_BUCKET)
```

`db_service.py` 和 `models.py` 完全不需要修改。

## 環境變數

| 變數名稱 | 說明 | 範例值 |
|---|---|---|
| `UPLOAD_STORAGE_PATH` | Local storage base directory | `./storage` |
| `S3_BUCKET` | S3 bucket 名稱（未來使用） | `medpacs-dicom` |
