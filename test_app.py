import pytest
from unittest.mock import patch
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@patch("app.fetch_carpark_data")
@patch("app.parse_carpark_xml")
def test_carparks_api_returns_sorted(mock_parse, mock_fetch, client):
    mock_fetch.return_value = "<xml/>"
    mock_parse.return_value = [
        {
            "name": "栢力停車場",
            "light_vehicle": {"available": 100, "total": 200},
            "heavy_vehicle": {"available": 0, "total": 0},
            "motorcycle": {"available": 10, "total": 20},
            "updated_at": "2026-04-06 10:00:00",
        },
        {
            "name": "栢湖停車場",
            "light_vehicle": {"available": 50, "total": 100},
            "heavy_vehicle": {"available": 0, "total": 0},
            "motorcycle": {"available": 5, "total": 10},
            "updated_at": "2026-04-06 10:00:00",
        },
    ]

    resp = client.get("/api/carparks?lat=22.20&lng=113.54")
    data = resp.get_json()

    assert resp.status_code == 200
    assert "carparks" in data
    assert len(data["carparks"]) == 2
    # 近的應該排前面
    assert data["carparks"][0]["name"] == "栢湖停車場"
    assert data["carparks"][1]["name"] == "栢力停車場"


def test_carparks_api_missing_params(client):
    resp = client.get("/api/carparks")
    assert resp.status_code == 400


@patch("app.fetch_carpark_data")
def test_carparks_api_fetch_error(mock_fetch, client):
    mock_fetch.side_effect = Exception("網絡錯誤")
    resp = client.get("/api/carparks?lat=22.20&lng=113.54")
    assert resp.status_code == 500


@patch("app.fetch_carpark_data")
@patch("app.parse_carpark_xml")
def test_carparks_api_empty_list(mock_parse, mock_fetch, client):
    mock_fetch.return_value = "<xml/>"
    mock_parse.return_value = []
    resp = client.get("/api/carparks?lat=22.20&lng=113.54")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["carparks"] == []
