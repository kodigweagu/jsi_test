import time

from fastapi.testclient import TestClient

from app.main import app
from tests.utils import make_token, DEFAULT_USERNAME, DEFAULT_PASSWORD


def _auth_request(token):
    with TestClient(app) as client:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return client.post(
            "/TimeFilter",
            json={
                "DataTypes": ["Chats"],
                "FromTime": "2021-01-01T08:00",
                "ToTime": "2021-12-31T10:00"
            },
            headers=headers or None
        )


def test_time_filter_invalid_token_signature():
    response = _auth_request(make_token(DEFAULT_USERNAME, DEFAULT_PASSWORD, secret="bad-secret"))
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid JWT token"


def test_time_filter_expired_token():
    response = _auth_request(make_token(DEFAULT_USERNAME, DEFAULT_PASSWORD, expiry=int(time.time()) - 10))
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid JWT token"


def test_time_filter_bad_user():
    response = _auth_request(make_token("bad-user", DEFAULT_PASSWORD))
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_time_filter_bad_password():
    response = _auth_request(make_token(DEFAULT_USERNAME, "bad-password"))
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_time_filter_missing_token():
    response = _auth_request(token=None)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
