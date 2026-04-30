"""
Day 6-7: Query API tests
Isolated from existing upload/storage tests.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from types import SimpleNamespace

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------
class _FakeRow:
    pass


def make_study(id=1, study_instance_uid="1.2.3"):
    obj = _FakeRow()
    obj.__dict__ = {"id": id, "study_instance_uid": study_instance_uid}
    return obj


def make_series(id=10, study_id=1, series_instance_uid="1.2.3.4"):
    obj = _FakeRow()
    obj.__dict__ = {"id": id, "study_id": study_id, "series_instance_uid": series_instance_uid}
    return obj


def make_instance(id=100, series_id=10, sop_instance_uid="1.2.3.4.5"):
    obj = _FakeRow()
    obj.__dict__ = {"id": id, "series_id": series_id, "sop_instance_uid": sop_instance_uid}
    return obj


# ---------------------------------------------------------------------------
# GET /studies
# ---------------------------------------------------------------------------

class TestListStudies:

    @patch("main.get_all_studies")
    def test_returns_empty_list(self, mock_get):
        mock_get.return_value = []
        response = client.get("/studies")
        assert response.status_code == 200
        assert response.json() == {"studies": []}

    @patch("main.get_all_studies")
    def test_returns_list_of_studies(self, mock_get):
        mock_get.return_value = [make_study(1), make_study(2, "9.8.7")]
        response = client.get("/studies")
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
    def test_returns_series_when_found(self, mock_get):
        mock_get.return_value = make_series(id=10)
        response = client.get("/series/10")
        assert response.status_code == 200
        assert response.json()["id"] == 10

    @patch("main.get_series_by_id")
    def test_returns_404_when_not_found(self, mock_get):
        mock_get.return_value = None
        response = client.get("/series/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("main.get_series_by_id")
    def test_id_passed_correctly(self, mock_get):
        mock_get.return_value = make_series(id=42)
        client.get("/series/42")
        call_args = mock_get.call_args[0]
        assert call_args[1] == 42


# ---------------------------------------------------------------------------
# GET /instances/{id}
# ---------------------------------------------------------------------------

class TestGetInstance:

    @patch("main.get_instance_by_id")
    def test_returns_instance_when_found(self, mock_get):
        mock_get.return_value = make_instance(id=100)
        response = client.get("/instances/100")
        assert response.status_code == 200
        assert response.json()["id"] == 100

    @patch("main.get_instance_by_id")
    def test_returns_404_when_not_found(self, mock_get):
        mock_get.return_value = None
        response = client.get("/instances/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("main.get_instance_by_id")
    def test_id_passed_correctly(self, mock_get):
        mock_get.return_value = make_instance(id=77)
        client.get("/instances/77")
        call_args = mock_get.call_args[0]
        assert call_args[1] == 77
