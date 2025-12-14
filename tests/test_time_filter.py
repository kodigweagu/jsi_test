from fastapi.testclient import TestClient
from app.main import app

def test_time_filter_success():
    with TestClient(app) as client:
        response = client.post(
            "/TimeFilter",
            json={
                "DataTypes": ["Chats"],
                "FromTime": "2021-01-01T08:00",
                "ToTime": "2021-12-31T10:00"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["communicationType"] == "Chats"


def test_time_filter_multiple_types():
    with TestClient(app) as client:
        response = client.post(
            "/TimeFilter",
            json={
                "DataTypes": ["Chats", "Emails"],
                "FromTime": "2021-01-01T08:00",
                "ToTime": "2021-12-31T12:00"
            }
        )

        assert response.status_code == 200
        types = set([item["communicationType"] for item in response.json()])
        for type in ["Chats", "Emails"]:
            assert type in types


def test_time_filter_no_results():
    with TestClient(app) as client:
        response = client.post(
            "/TimeFilter",
            json={
                "DataTypes": ["Notes"],
                "FromTime": "2022-01-01T00:00",
                "ToTime": "2022-01-01T01:00"
            }
        )

        assert response.status_code == 200
        assert response.json() == []


def test_time_filter_invalid_request():
    with TestClient(app) as client:
        response = client.post(
            "/TimeFilter",
            json={
                "DataTypes": ["Chats"],
                "FromTime": "invalid-date",
                "ToTime": "2021-01-01T10:00"
            }
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid request"
