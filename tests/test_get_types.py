from fastapi.testclient import TestClient
from app.main import app


def test_get_types_returns_200():
    with TestClient(app) as client:
        response = client.get("/GetTypes")
        assert response.status_code == 200


def test_get_types_returns_list():
    with TestClient(app) as client:
        response = client.get("/GetTypes")
        assert isinstance(response.json(), list)


def test_get_types_contains_expected_types():
    with TestClient(app) as client:
        response = client.get("/GetTypes")
        data = response.json()

        assert "Chats" in data
        assert "Emails" in data
        assert "Sms" in data
        assert "Notes" not in data


def test_get_types_has_no_duplicates():
    with TestClient(app) as client:
        data = client.get("/GetTypes").json()
        assert len(data) == len(set(data))
