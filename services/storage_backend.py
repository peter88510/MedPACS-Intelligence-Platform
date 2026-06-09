# storage_backend.py
import os
from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    def read_bytes(self, path: str) -> bytes:
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        pass

    @abstractmethod
    def absolute_path(self, path: str) -> str:
        """For FileResponse — local only"""
        pass


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def read_bytes(self, path: str) -> bytes:
        with open(self.absolute_path(path), "rb") as f:
            return f.read()

    def exists(self, path: str) -> bool:
        return os.path.exists(self.absolute_path(path))

    def absolute_path(self, path: str) -> str:
        return os.path.join(self.base_dir, path)

# Future: S3StorageBackend(StorageBackend) — 只需實作這三個方法
# storage_backend.py 新增
# import boto3
#
# class S3StorageBackend(StorageBackend):
#     def __init__(self, bucket: str):
#         self.bucket = bucket
#         self.client = boto3.client("s3")
#
#     def exists(self, path: str) -> bool:
#         try:
#             self.client.head_object(Bucket=self.bucket, Key=path)
#             return True
#         except:
#             return False
#
#     def read_bytes(self, path: str) -> bytes:
#         obj = self.client.get_object(Bucket=self.bucket, Key=path)
#         return obj["Body"].read()
#
#     def absolute_path(self, path: str) -> str:
#         raise NotImplementedError("S3 backend uses StreamingResponse, not FileResponse")
