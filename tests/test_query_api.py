"""
Day 6-7: Query API tests
Isolated from existing upload/storage tests.
"""

import pytest
from unittest.mock import patch, MagicMock
from conftest import make_study, make_series, make_instance


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

    @patch("main.get_instance_by_id")
    def test_returns_queued_status_when_found(self, mock_get, api_client):
        mock_get.return_value = make_instance(id=1)
        response = api_client.post("/ai/segment/1")
        assert response.status_code == 200
        data = response.json()
        assert data["instance_id"] == 1
        assert data["status"] == "queued"

    @patch("main.get_instance_by_id")
    def test_returns_404_when_not_found(self, mock_get, api_client):
        mock_get.return_value = None
        response = api_client.post("/ai/segment/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("main.get_instance_by_id")
    def test_id_passed_correctly(self, mock_get, api_client):
        mock_get.return_value = make_instance(id=7)
        api_client.post("/ai/segment/7")
        call_args = mock_get.call_args[0]
        assert call_args[1] == 7


# ---------------------------------------------------------------------------
# GET /ai/result/{id}
# ---------------------------------------------------------------------------

class TestAiResult:

    @patch("main.get_instance_by_id")
    def test_returns_result_when_found(self, mock_get, api_client):
        mock_get.return_value = make_instance(id=1)
        response = api_client.get("/ai/result/1")
        assert response.status_code == 200
        data = response.json()
        assert data["instance_id"] == 1
        assert data["status"] == "completed"
        assert "result" in data

    @patch("main.get_instance_by_id")
    def test_returns_404_when_not_found(self, mock_get, api_client):
        mock_get.return_value = None
        response = api_client.get("/ai/result/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("main.get_instance_by_id")
    def test_id_passed_correctly(self, mock_get, api_client):
        mock_get.return_value = make_instance(id=33)
        api_client.get("/ai/result/33")
        call_args = mock_get.call_args[0]
        assert call_args[1] == 33


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
