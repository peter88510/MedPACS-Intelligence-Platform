# Storage Backend

## Overview

`storage_backend.py` 是 storage 的抽象層，讓上層程式碼（API endpoint）不需要知道檔案實際存在哪裡。
目前實作 local 檔案系統，未來可無縫替換成 S3 或其他儲存。

## Location

專案根目錄，與 `db.py`、`storage.py` 同層。

```
project-root/
├── storage_backend.py   ← here
├── db.py
├── storage.py
├── main.py
└── ...
```

## Interface

所有 backend 實作都繼承 `StorageBackend`，必須實作三個方法：

| Method | Description |
|--------|-------------|
| `exists(path)` | 確認檔案是否存在 |
| `read_bytes(path)` | 讀取檔案內容，回傳 `bytes` |
| `absolute_path(path)` | 回傳可供 `FileResponse` 使用的絕對路徑（local only） |

`path` 統一使用相對路徑（對應 DB 欄位 `Instance.file_path`），例如 `dicom/xxx.dcm`。

## Current Implementation

### `LocalStorageBackend`

從 `.env` 的 `UPLOAD_STORAGE_PATH` 作為 base directory，與 `file_path` 組合成完整路徑。

初始化位置：`main.py` module level

```python
from storage_backend import LocalStorageBackend
from config import settings

storage = LocalStorageBackend(base_dir=settings.UPLOAD_STORAGE_PATH)
```

## Future: S3 Migration

新增 `S3StorageBackend(StorageBackend)` 並實作三個方法。
`main.py` 只需替換初始化的 backend instance，其餘 endpoint 程式碼不需要修改。

```python
# 切換只需改這一行
storage = S3StorageBackend(bucket=settings.S3_BUCKET)
```

`db_service.py` 和 `models.py` 完全不需要動。

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `UPLOAD_STORAGE_PATH` | Local storage base directory | `./storage` |
| `S3_BUCKET` | S3 bucket name（未來用） | `medpacs-dicom` |