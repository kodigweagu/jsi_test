"""Tests for API endpoints beyond existing coverage."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import router
from app.repository import UserAlreadyExistsError, UserCreateError, UserLookupError
from tests.utils import make_token, DEFAULT_USERNAME


class _RepoStub:  # pylint: disable=too-few-public-methods
    """Records repo stub for API tests."""

    async def get_types(self):
        """Return known types."""
        return ["Chats"]

    async def filter_by_time(self, data_types, from_time, to_time):
        """Return filtered records."""
        return [{"communicationType": data_types[0]}]

    async def reconcile_types(self):
        """Return reconciled type data."""
        return [{"type": "Chats", "count": 1}]


class _UserRepoStub:  # pylint: disable=too-few-public-methods
    """User repo stub for API tests."""

    def __init__(self, is_admin=True):
        self._is_admin = is_admin
        self.verify_result = True
        self.create_error = None
        self.verify_error = None

    async def get_user(self, username):
        """Return a stubbed user."""
        return {
            "username": username,
            "is_admin": self._is_admin,
            "password_changed_at": 0,
        }

    async def create_user(self, username, password, is_admin=False):
        """Create a user or raise errors."""
        if self.create_error:
            raise self.create_error

    async def verify_password(self, username, password):
        """Verify a password or raise errors."""
        if self.verify_error:
            raise self.verify_error
        return self.verify_result


def _make_app(user_repo):
    """Create a FastAPI app with stubbed state."""
    app = FastAPI()
    app.state.repo = _RepoStub()
    app.state.user_repo = user_repo
    app.include_router(router)
    return app


def test_login_success():
    """Return a token for valid credentials."""
    app = _make_app(_UserRepoStub())
    with TestClient(app) as client:
        response = client.post(
            "/Login", json={"Username": "admin", "Password": "pw"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_get_types_uses_repo_stub():
    """Return types from the repo stub."""
    app = _make_app(_UserRepoStub())
    with TestClient(app) as client:
        response = client.get("/GetTypes")
    assert response.status_code == 200
    assert response.json() == ["Chats"]


def test_time_filter_uses_repo_stub():
    """Return filtered records from the repo stub."""
    app = _make_app(_UserRepoStub())
    token = make_token(DEFAULT_USERNAME)
    with TestClient(app) as client:
        response = client.post(
            "/TimeFilter",
            json={
                "DataTypes": ["Chats"],
                "FromTime": "2021-01-01T00:00",
                "ToTime": "2021-01-02T00:00",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    assert response.json() == [{"communicationType": "Chats"}]


def test_login_invalid_credentials():
    """Reject invalid credentials."""
    user_repo = _UserRepoStub()
    user_repo.verify_result = False
    app = _make_app(user_repo)
    with TestClient(app) as client:
        response = client.post(
            "/Login", json={"Username": "admin", "Password": "bad"})
    assert response.status_code == 401


def test_login_invalid_request():
    """Reject malformed login payloads."""
    app = _make_app(_UserRepoStub())
    with TestClient(app) as client:
        response = client.post("/Login", json={"Username": "admin"})
    assert response.status_code == 400


def test_login_lookup_error():
    """Return 500 when user lookup fails."""
    user_repo = _UserRepoStub()
    user_repo.verify_error = UserLookupError("db down")
    app = _make_app(user_repo)
    with TestClient(app) as client:
        response = client.post(
            "/Login", json={"Username": "admin", "Password": "pw"})
    assert response.status_code == 500


def test_register_user_conflict():
    """Return 409 when user already exists."""
    user_repo = _UserRepoStub()
    user_repo.create_error = UserAlreadyExistsError("exists")
    app = _make_app(user_repo)
    token = make_token(DEFAULT_USERNAME)
    with TestClient(app) as client:
        response = client.post(
            "/RegisterUser",
            json={"Username": "new", "Password": "pw", "IsAdmin": False},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 409


def test_register_user_success():
    """Return created for successful registration."""
    app = _make_app(_UserRepoStub())
    token = make_token(DEFAULT_USERNAME)
    with TestClient(app) as client:
        response = client.post(
            "/RegisterUser",
            json={"Username": "new", "Password": "pw", "IsAdmin": False},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    assert response.json() == {"status": "created"}


def test_register_user_server_error():
    """Return 500 when create_user fails."""
    user_repo = _UserRepoStub()
    user_repo.create_error = UserCreateError("db down")
    app = _make_app(user_repo)
    token = make_token(DEFAULT_USERNAME)
    with TestClient(app) as client:
        response = client.post(
            "/RegisterUser",
            json={"Username": "new", "Password": "pw", "IsAdmin": False},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 500


def test_register_user_invalid_request():
    """Reject malformed registration payloads."""
    app = _make_app(_UserRepoStub())
    token = make_token(DEFAULT_USERNAME)
    with TestClient(app) as client:
        response = client.post(
            "/RegisterUser",
            json={"Username": "new"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 400


def test_register_user_requires_admin():
    """Reject non-admin users for registration."""
    app = _make_app(_UserRepoStub(is_admin=False))
    token = make_token(DEFAULT_USERNAME)
    with TestClient(app) as client:
        response = client.post(
            "/RegisterUser",
            json={"Username": "new", "Password": "pw", "IsAdmin": False},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 403


def test_reconcile_types_admin_only():
    """Require admin token for reconcile."""
    app = _make_app(_UserRepoStub())
    token = make_token(DEFAULT_USERNAME)
    with TestClient(app) as client:
        response = client.post(
            "/ReconcileTypes",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    assert response.json() == [{"type": "Chats", "count": 1}]
