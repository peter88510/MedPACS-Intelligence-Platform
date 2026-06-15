"""
Day 6-7: Query API tests
Isolated from existing upload/storage tests.
"""

import pytest
from unittest.mock import patch, MagicMock
from conftest import make_study, make_series, make_instance

from main import app
from services.ai_engine import (
    EngineResult,
    EngineUnavailableError,
    Measurement,
    get_engine,
)
from services.measurement_type import MeasurementType


class _FakeEngine:
    """注入用 fake 引擎：完全不碰 paddle / AI source。"""

    model_name = "fake-engine"
    model_version = "test"

    def __init__(self, result=None, exc=None):
        self._result = result
        self._exc = exc

    def analyze(self, image_path, measurement_type, save_mask_dir=None):
        if self._exc is not None:
            raise self._exc
        return self._result


def _override_engine(engine):
    app.dependency_overrides[get_engine] = lambda: engine


def _clear_engine_override():
    app.dependency_overrides.pop(get_engine, None)


def _make_instance_with_device(id=1, device_model="C62"):
    inst = make_instance(id=id)
    inst.device_manufacturer = "AnyVendor"
    inst.device_model = device_model
    return inst


# ---------------------------------------------------------------------------
# GET /studies
# ---------------------------------------------------------------------------

class TestListStudies:

    @patch("main.get_all_studies")
    def test_returns_empty_list(self, mock_get, api_client):
        mock_get.return_value = []
        response = api_client.get("/studies")
        assert response.status_code == 200
        assert response.json() == {"studies": []}

    @patch("main.get_all_studies")
    def test_returns_list_of_studies(self, mock_get, api_client):
        mock_get.return_value = [make_study(1), make_study(2, "9.8.7")]
        response = api_client.get("/studies")
        assert response.status_code == 200
        data = response.json()
        assert len(data["studies"]) == 2
        assert data["studies"][0]["id"] == 1
        assert data["studies"][1]["study_instance_uid"] == "9.8.7"


# ---------------------------------------------------------------------------
# GET /series/{id}
# ---------------------------------------------------------------------------

class TestGetSeries:

    @patch("main.get_series_by_id")
    def test_returns_series_when_found(self, mock_get, api_client):
        mock_get.return_value = make_series(id=10)
        response = api_client.get("/series/10")
        assert response.status_code == 200
        assert response.json()["id"] == 10

    @patch("main.get_series_by_id")
    def test_returns_404_when_not_found(self, mock_get, api_client):
        mock_get.return_value = None
        response = api_client.get("/series/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("main.get_series_by_id")
    def test_id_passed_correctly(self, mock_get, api_client):
        mock_get.return_value = make_series(id=42)
        api_client.get("/series/42")
        call_args = mock_get.call_args[0]
        assert call_args[1] == 42


# ---------------------------------------------------------------------------
# GET /instances/{id}
# ---------------------------------------------------------------------------

class TestGetInstance:

    @patch("main.get_instance_by_id")
    def test_returns_instance_when_found(self, mock_get, api_client):
        mock_get.return_value = make_instance(id=100)
        response = api_client.get("/instances/100")
        assert response.status_code == 200
        assert response.json()["id"] == 100

    @patch("main.get_instance_by_id")
    def test_returns_404_when_not_found(self, mock_get, api_client):
        mock_get.return_value = None
        response = api_client.get("/instances/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("main.get_instance_by_id")
    def test_id_passed_correctly(self, mock_get, api_client):
        mock_get.return_value = make_instance(id=77)
        api_client.get("/instances/77")
        call_args = mock_get.call_args[0]
        assert call_args[1] == 77


# ---------------------------------------------------------------------------
# GET /instances/{id}/file
# ---------------------------------------------------------------------------

class TestGetInstanceFile:
    @patch("main.get_instance_file_path")
    @patch("os.path.exists")
    def test_returns_file_when_found(self, mock_exists, mock_get_path, api_client):
        mock_get_path.return_value = "/fake/path/test.dcm"
        mock_exists.return_value = True
        with patch("main.FileResponse") as mock_fr:
            mock_fr.return_value = MagicMock(status_code=200)
            response = api_client.get("/instances/1/file")
        assert response.status_code == 200

    @patch("main.get_instance_file_path")
    def test_returns_404_when_instance_not_found(self, mock_get_path, api_client):
        mock_get_path.return_value = None
        response = api_client.get("/instances/999/file")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("main.get_instance_file_path")
    @patch("os.path.exists")
    def test_returns_404_when_file_missing_on_disk(self, mock_exists, mock_get_path, api_client):
        mock_get_path.return_value = "/fake/path/missing.dcm"
        mock_exists.return_value = False
        response = api_client.get("/instances/1/file")
        assert response.status_code == 404
        assert "disk" in response.json()["detail"].lower()

    @patch("main.get_instance_file_path")
    @patch("os.path.exists")
    def test_id_passed_correctly(self, mock_exists, mock_get_path, api_client):
        mock_get_path.return_value = "/fake/path/test.dcm"
        mock_exists.return_value = True
        with patch("main.FileResponse", return_value=MagicMock(status_code=200)):
            api_client.get("/instances/55/file")
        call_args = mock_get_path.call_args[0]
        assert call_args[1] == 55


# ---------------------------------------------------------------------------
# GET /instances/{id}/metadata
# ---------------------------------------------------------------------------

class TestGetInstanceMetadata:

    @patch("main.get_instance_metadata")
    def test_returns_metadata_when_found(self, mock_get, api_client):
        mock_get.return_value = {"id": 1, "sop_instance_uid": "1.2.3"}
        response = api_client.get("/instances/1/metadata")
        assert response.status_code == 200
        assert response.json()["id"] == 1

    @patch("main.get_instance_metadata")
    def test_returns_404_when_not_found(self, mock_get, api_client):
        mock_get.return_value = None
        response = api_client.get("/instances/999/metadata")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("main.get_instance_metadata")
    def test_id_passed_correctly(self, mock_get, api_client):
        mock_get.return_value = {"id": 42, "sop_instance_uid": "9.8.7"}
        api_client.get("/instances/42/metadata")
        call_args = mock_get.call_args[0]
        assert call_args[1] == 42


# ---------------------------------------------------------------------------
# POST /ai/segment/{id}
# ---------------------------------------------------------------------------

class TestAiSegment:
    """真實實作（取代 stub）：resolver 分支 + 引擎注入。所有 DB / 引擎皆 mock，
    不碰 paddle 或 production DB。"""

    def teardown_method(self):
        _clear_engine_override()

    @patch("main.get_instance_by_id")
    def test_unknown_model_returns_422(self, mock_get, api_client):
        # make_instance 無 device_model → resolver 回 UNKNOWN → 422
        mock_get.return_value = make_instance(id=1)
        response = api_client.post("/ai/segment/1")
        assert response.status_code == 422
        assert "measurement type" in response.json()["detail"].lower()

    @patch("main.get_instance_by_id")
    def test_thickness_model_returns_501(self, mock_get, api_client):
        mock_get.return_value = _make_instance_with_device(id=1, device_model="L154")
        response = api_client.post("/ai/segment/1")
        assert response.status_code == 501
        assert "thickness" in response.json()["detail"].lower()

    @patch("main.create_ai_result")
    @patch("main.get_instance_file_path")
    @patch("main.get_instance_by_id")
    def test_excursion_success_writes_result(
        self, mock_get, mock_path, mock_create, api_client
    ):
        mock_get.return_value = _make_instance_with_device(id=1, device_model="C62")
        mock_path.return_value = "P001/study/img.dcm"
        mock_create.return_value = MagicMock(id=42)
        engine = _FakeEngine(result=EngineResult(
            measurement_type=MeasurementType.EXCURSION,
            model_name="diaphragm_excursion",
            model_version="6139799",
            pipeline_mode="legacy",
            measurements=[Measurement(batch_index=0, excursion_cm=2.31,
                                      excursion_pixel=120, time_pixel=45,
                                      crest=[320, 110], trough=[365, 230])],
        ))
        _override_engine(engine)
        with patch("main.storage") as mock_storage:
            mock_storage.exists.return_value = True
            mock_storage.absolute_path.return_value = "/abs/P001/study/img.dcm"
            response = api_client.post("/ai/segment/1")
        assert response.status_code == 200
        data = response.json()
        assert data["instance_id"] == 1
        assert data["ai_result_id"] == 42
        assert data["status"] == "completed"
        assert data["measurement_type"] == "excursion"
        assert data["primary_value"] == 2.31
        assert data["primary_unit"] == "cm"
        assert data["measurement_count"] == 1
        # 寫入 ai_results 帶正確 envelope
        _, kwargs = mock_create.call_args
        assert kwargs["measurement_type"] == "excursion"
        assert kwargs["result_json"]["schema_version"] == 1
        assert kwargs["primary_value"] == 2.31

    @patch("main.create_ai_result")
    @patch("main.get_instance_file_path")
    @patch("main.get_instance_by_id")
    def test_engine_unavailable_returns_503(
        self, mock_get, mock_path, mock_create, api_client
    ):
        mock_get.return_value = _make_instance_with_device(id=1, device_model="C62")
        mock_path.return_value = "P001/study/img.dcm"
        _override_engine(_FakeEngine(exc=EngineUnavailableError("paddle missing")))
        with patch("main.storage") as mock_storage:
            mock_storage.exists.return_value = True
            mock_storage.absolute_path.return_value = "/abs/img.dcm"
            response = api_client.post("/ai/segment/1")
        assert response.status_code == 503
        # 引擎不可用 → 不應寫任何 ai_results
        mock_create.assert_not_called()

    @patch("main.get_instance_by_id")
    def test_returns_404_when_not_found(self, mock_get, api_client):
        mock_get.return_value = None
        response = api_client.post("/ai/segment/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# GET /ai/result/{id}
# ---------------------------------------------------------------------------

class TestAiResult:

    @patch("main.get_latest_ai_result_by_instance")
    @patch("main.get_instance_by_id")
    def test_returns_result_when_exists(self, mock_get, mock_latest, api_client):
        mock_get.return_value = make_instance(id=1)
        mock_latest.return_value = MagicMock(
            id=7, status="completed", measurement_type="excursion",
            model_name="diaphragm_excursion", model_version="6139799",
            primary_value=2.31, primary_unit="cm", confidence=None,
            mask_path=None,
            result_json={"schema_version": 1}, error_message=None, created_at=None,
        )
        response = api_client.get("/ai/result/1")
        assert response.status_code == 200
        data = response.json()
        assert data["instance_id"] == 1
        assert data["status"] == "completed"
        assert data["measurement_type"] == "excursion"
        assert data["primary_value"] == 2.31
        assert data["result"]["schema_version"] == 1
        assert data["mask_url"] is None  # 無 mask → mask_url None

    @patch("main.get_latest_ai_result_by_instance")
    @patch("main.get_instance_by_id")
    def test_mask_url_set_when_mask_exists(self, mock_get, mock_latest, api_client):
        mock_get.return_value = make_instance(id=1)
        mock_latest.return_value = MagicMock(
            id=7, status="completed", measurement_type="excursion",
            model_name="diaphragm_excursion", model_version="6139799",
            primary_value=2.31, primary_unit="cm", confidence=None,
            mask_path="P001/study/masks/inst1/pseudo_color_prediction/img.png",
            result_json={"schema_version": 1}, error_message=None, created_at=None,
        )
        response = api_client.get("/ai/result/1")
        assert response.status_code == 200
        assert response.json()["mask_url"] == "/ai/result/1/mask"

    @patch("main.get_latest_ai_result_by_instance")
    @patch("main.get_instance_by_id")
    def test_status_filter_passed_and_mask_url_carries_status(
        self, mock_get, mock_latest, api_client
    ):
        mock_get.return_value = make_instance(id=1)
        mock_latest.return_value = MagicMock(
            id=7, status="completed", measurement_type="excursion",
            model_name="diaphragm_excursion", model_version="6139799",
            primary_value=2.31, primary_unit="cm", confidence=None,
            mask_path="P001/study/m.png",
            result_json={"schema_version": 1}, error_message=None, created_at=None,
        )
        response = api_client.get("/ai/result/1?status=completed")
        assert response.status_code == 200
        # status 透傳給 db_service
        assert mock_latest.call_args.kwargs["status"] == "completed"
        # mask_url 帶上同一 status，讓 mask endpoint 撈到同一筆
        assert response.json()["mask_url"] == "/ai/result/1/mask?status=completed"

    @patch("main.get_latest_ai_result_by_instance")
    @patch("main.get_instance_by_id")
    def test_status_filter_no_match_returns_404(
        self, mock_get, mock_latest, api_client
    ):
        mock_get.return_value = make_instance(id=1)
        mock_latest.return_value = None
        response = api_client.get("/ai/result/1?status=completed")
        assert response.status_code == 404
        assert "completed" in response.json()["detail"].lower()

    @patch("main.get_latest_ai_result_by_instance")
    @patch("main.get_instance_by_id")
    def test_returns_404_when_no_result_yet(self, mock_get, mock_latest, api_client):
        mock_get.return_value = make_instance(id=1)
        mock_latest.return_value = None
        response = api_client.get("/ai/result/1")
        assert response.status_code == 404
        assert "no ai result" in response.json()["detail"].lower()

    @patch("main.get_instance_by_id")
    def test_returns_404_when_instance_not_found(self, mock_get, api_client):
        mock_get.return_value = None
        response = api_client.get("/ai/result/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# GET /ai/result/{id}/mask  (added 2026-06-15)
# ---------------------------------------------------------------------------

class TestAiResultMask:

    @patch("main.get_latest_ai_result_by_instance")
    @patch("main.get_instance_by_id")
    def test_returns_png_when_mask_exists(
        self, mock_get, mock_latest, api_client, tmp_path
    ):
        png = tmp_path / "mask.png"
        png.write_bytes(b"\x89PNG\r\n\x1a\n")  # minimal PNG magic bytes
        mock_get.return_value = make_instance(id=1)
        mock_latest.return_value = MagicMock(id=7, mask_path="P001/study/m.png")
        with patch("main.storage") as mock_storage:
            mock_storage.exists.return_value = True
            mock_storage.absolute_path.return_value = str(png)
            response = api_client.get("/ai/result/1/mask")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    @patch("main.get_latest_ai_result_by_instance")
    @patch("main.get_instance_by_id")
    def test_returns_404_when_result_has_no_mask(
        self, mock_get, mock_latest, api_client
    ):
        mock_get.return_value = make_instance(id=1)
        mock_latest.return_value = MagicMock(id=7, mask_path=None)
        response = api_client.get("/ai/result/1/mask")
        assert response.status_code == 404
        assert "no mask" in response.json()["detail"].lower()

    @patch("main.get_latest_ai_result_by_instance")
    @patch("main.get_instance_by_id")
    def test_returns_404_when_mask_file_missing(
        self, mock_get, mock_latest, api_client
    ):
        mock_get.return_value = make_instance(id=1)
        mock_latest.return_value = MagicMock(id=7, mask_path="P001/study/gone.png")
        with patch("main.storage") as mock_storage:
            mock_storage.exists.return_value = False
            response = api_client.get("/ai/result/1/mask")
        assert response.status_code == 404
        assert "missing on disk" in response.json()["detail"].lower()

    @patch("main.get_latest_ai_result_by_instance")
    @patch("main.get_instance_by_id")
    def test_returns_404_when_no_result_yet(self, mock_get, mock_latest, api_client):
        mock_get.return_value = make_instance(id=1)
        mock_latest.return_value = None
        response = api_client.get("/ai/result/1/mask")
        assert response.status_code == 404
        assert "no ai result" in response.json()["detail"].lower()

    @patch("main.get_instance_by_id")
    def test_returns_404_when_instance_not_found(self, mock_get, api_client):
        mock_get.return_value = None
        response = api_client.get("/ai/result/999/mask")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("main.get_latest_ai_result_by_instance")
    @patch("main.get_instance_by_id")
    def test_status_filter_passed_to_db(self, mock_get, mock_latest, api_client):
        mock_get.return_value = make_instance(id=1)
        mock_latest.return_value = MagicMock(id=7, mask_path="P001/study/m.png")
        with patch("main.storage") as mock_storage:
            mock_storage.exists.return_value = False  # 檔案不在 → 404；只驗 status 透傳
            api_client.get("/ai/result/1/mask?status=completed")
        assert mock_latest.call_args.kwargs["status"] == "completed"


# ---------------------------------------------------------------------------
# GET /studies/{id}/series  (added 2026-05-15)
# ---------------------------------------------------------------------------

class TestListSeriesForStudy:

    @patch("main.get_series_by_study_id")
    def test_returns_series_list_when_study_exists(self, mock_get, api_client):
        mock_get.return_value = [
            make_series(id=10, series_instance_uid="1.2.3.4"),
            make_series(id=11, series_instance_uid="1.2.3.5"),
        ]
        response = api_client.get("/studies/1/series")
        assert response.status_code == 200
        data = response.json()
        assert len(data["series"]) == 2
        assert data["series"][0]["id"] == 10
        assert data["series"][1]["series_instance_uid"] == "1.2.3.5"

    @patch("main.get_series_by_study_id")
    def test_returns_empty_list_when_study_has_no_series(self, mock_get, api_client):
        mock_get.return_value = []
        response = api_client.get("/studies/1/series")
        assert response.status_code == 200
        assert response.json() == {"series": []}

    @patch("main.get_series_by_study_id")
    def test_returns_404_when_study_not_found(self, mock_get, api_client):
        mock_get.return_value = None
        response = api_client.get("/studies/999/series")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("main.get_series_by_study_id")
    def test_id_passed_correctly(self, mock_get, api_client):
        mock_get.return_value = []
        api_client.get("/studies/42/series")
        call_args = mock_get.call_args[0]
        assert call_args[1] == 42


# ---------------------------------------------------------------------------
# GET /series/{id}/instances  (added 2026-05-15)
# ---------------------------------------------------------------------------

class TestListInstancesForSeries:

    @patch("main.get_instances_by_series_id")
    def test_returns_instances_list_when_series_exists(self, mock_get, api_client):
        mock_get.return_value = [
            make_instance(id=100),
            make_instance(id=101),
        ]
        response = api_client.get("/series/10/instances")
        assert response.status_code == 200
        data = response.json()
        assert len(data["instances"]) == 2
        assert data["instances"][0]["id"] == 100

    @patch("main.get_instances_by_series_id")
    def test_returns_empty_list_when_series_has_no_instances(self, mock_get, api_client):
        mock_get.return_value = []
        response = api_client.get("/series/10/instances")
        assert response.status_code == 200
        assert response.json() == {"instances": []}

    @patch("main.get_instances_by_series_id")
    def test_returns_404_when_series_not_found(self, mock_get, api_client):
        mock_get.return_value = None
        response = api_client.get("/series/999/instances")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("main.get_instances_by_series_id")
    def test_id_passed_correctly(self, mock_get, api_client):
        mock_get.return_value = []
        api_client.get("/series/77/instances")
        call_args = mock_get.call_args[0]
        assert call_args[1] == 77
