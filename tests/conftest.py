"""
tests/conftest.py
=================
專案共用測試工具集中定義處。

規則（所有貢獻者必須遵守）：
- _FakeRow、make_*() 工廠函式只能定義在這裡
- 測試檔案必須從這裡 import，不得在各自檔案中重複定義
- 新增 model 對應的工廠函式時，統一加在本檔案「ORM 工廠函式」區塊
- make_mock_*() 系列（MagicMock 物件）同樣集中在這裡
"""
import pytest
from fastapi.testclient import TestClient
from main import app, get_db
from unittest.mock import MagicMock

# --- 遷移自 test_dicom_service.py ---
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# Use in-memory SQLite for tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_client():
    """每個測試獨立的 TestClient，fixture 結束後自動清理 dependency_overrides。"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def db():
    db = TestingSessionLocal()
    yield db
    db.close()


# query_api 測試專用：無需 DB override，純 mock 測試

@pytest.fixture
def api_client():
    with TestClient(app) as client:
        yield client


# ---------------------------------------------------------------------------
# 私有基礎類別
# ---------------------------------------------------------------------------

class _FakeRow:
    """
    最小化假 ORM 物件。

    用途：
      - 在 API 測試中作為 mock service 函式的回傳值
      - 模擬 SQLAlchemy model instance 的屬性存取行為

    限制：
      - 僅供 API 測試（test_*_api.py）使用
      - 不得用於整合測試（整合測試使用真實 model instance）
      - 不得觸發 SQLAlchemy relationship / lazy loading
    """
    pass


# ---------------------------------------------------------------------------
# ORM 工廠函式
# 命名規則：make_<model 名稱小寫>()
# 所有參數必須有預設值，新增欄位加在最後，不得破壞現有呼叫方式
# ---------------------------------------------------------------------------

def make_study(id=1, study_instance_uid="1.2.3"):
    """
    建立假 Study ORM 物件。

    預設值：
      id                = 1
      study_instance_uid = "1.2.3"

    範例：
      make_study()                          → id=1,  uid="1.2.3"
      make_study(id=2, study_instance_uid="9.8.7")  → id=2,  uid="9.8.7"
    """
    obj = _FakeRow()
    obj.__dict__ = {
        "id": id,
        "study_instance_uid": study_instance_uid,
    }
    return obj


def make_series(id=10, study_id=1, series_instance_uid="1.2.3.4"):
    """
    建立假 Series ORM 物件。

    預設值：
      id                  = 10
      study_id            = 1
      series_instance_uid = "1.2.3.4"

    範例：
      make_series()                   → id=10, study_id=1
      make_series(id=42, study_id=2)  → id=42, study_id=2
    """
    obj = _FakeRow()
    obj.__dict__ = {
        "id": id,
        "study_id": study_id,
        "series_instance_uid": series_instance_uid,
    }
    return obj


def make_instance(id=100, series_id=10, sop_instance_uid="1.2.3.4.5"):
    """
    建立假 Instance ORM 物件。

    預設值：
      id               = 100
      series_id        = 10
      sop_instance_uid = "1.2.3.4.5"

    範例：
      make_instance()          → id=100, series_id=10
      make_instance(id=77)     → id=77,  series_id=10
    """
    obj = _FakeRow()
    obj.__dict__ = {
        "id": id,
        "series_id": series_id,
        "sop_instance_uid": sop_instance_uid,
    }
    return obj


# ---------------------------------------------------------------------------
# MagicMock 工廠函式
# 命名規則：make_mock_<外部物件名稱小寫>()
# 用於模擬外部 library 物件（pydicom 等），不適用 _FakeRow
# ---------------------------------------------------------------------------

def make_mock_ds(patient_id="P001", study_uid="1.2.3", modality="US"):
    """
    建立假 pydicom FileDataset MagicMock 物件。

    用途：
      - 測試 DICOM validation 邏輯
      - 測試 /upload endpoint 的 dcmread 行為（搭配 patch）

    預設值：
      patient_id = "P001"
      study_uid  = "1.2.3"
      modality   = "US"   （預設為允許的 modality）

    範例：
      make_mock_ds()                         → 合法的 US DICOM
      make_mock_ds(modality="CT")            → 應被 validator 拒絕的 modality
      make_mock_ds(patient_id="")            → 應被 validator 拒絕的空 PatientID
    """
    ds = MagicMock()
    ds.PatientID = patient_id
    ds.StudyInstanceUID = study_uid
    ds.Modality = modality
    return ds
