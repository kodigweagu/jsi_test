from fastapi.testclient import TestClient

from app.main import app
from tests.utils import make_token, DEFAULT_USERNAME, DEFAULT_PASSWORD


VALID_TOKEN = make_token(DEFAULT_USERNAME, DEFAULT_PASSWORD)


def _time_filter_request(data_types, from_time, to_time, token=VALID_TOKEN):
    with TestClient(app) as client:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return client.post(
            "/TimeFilter",
            json={
                "DataTypes": data_types,
                "FromTime": from_time,
                "ToTime": to_time
            },
            headers=headers or None
        )


def test_time_filter_success():
    response = _time_filter_request(["Chats"], "2021-01-01T08:00", "2021-12-31T10:00")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["communicationType"] == "Chats"


def test_time_filter_multiple_types():
    response = _time_filter_request(["Chats", "Emails"], "2021-01-01T08:00", "2021-12-31T12:00")
    assert response.status_code == 200
    types = set([item["communicationType"] for item in response.json()])
    for type in ["Chats", "Emails"]:
        assert type in types


def test_time_filter_no_results():
    response = _time_filter_request(["Notes"], "2022-01-01T00:00", "2022-01-01T01:00")
    assert response.status_code == 200
    assert response.json() == []


def test_time_filter_invalid_request():
    response = _time_filter_request(["Chats"], "invalid-date", "2021-01-01T10:00")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid request"
