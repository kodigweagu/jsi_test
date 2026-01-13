"""Tests for JWT verification."""

import time

import pytest
import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app._auth import verify_jwt, SECRET, ALGORITHM
from tests.utils import make_token, DEFAULT_USERNAME


def _credentials(token: str) -> HTTPAuthorizationCredentials:
    """Wrap a JWT token in FastAPI credentials."""
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


class _FakeUserRepo:  # pylint: disable=too-few-public-methods
    """User repo stub for auth tests."""

    def __init__(self, users):
        self._users = users

    async def get_user(self, username):
        """Return a user by username."""
        return self._users.get(username)


class _FakeRequest:  # pylint: disable=too-few-public-methods
    """Request stub with app.state.user_repo attached."""

    def __init__(self, user_repo):
        self.app = type("App", (), {"state": type("State", (), {"user_repo": user_repo})()})()


def _request_with_users(users):
    """Create a request stub with preset users."""
    return _FakeRequest(_FakeUserRepo(users))


@pytest.mark.asyncio
async def test_verify_jwt_accepts_valid_token():
    """Accept a valid token for the default user."""
    token = make_token(DEFAULT_USERNAME)
    request = _request_with_users(
        {DEFAULT_USERNAME: {"username": DEFAULT_USERNAME, "password_hash": "ignored"}}
    )
    assert await verify_jwt(request, _credentials(token)) == DEFAULT_USERNAME


@pytest.mark.asyncio
async def test_verify_jwt_invalid_token_signature():
    """Reject tokens signed with a different secret."""
    bad_token = make_token(DEFAULT_USERNAME, secret="bad-secret")
    request = _request_with_users(
        {DEFAULT_USERNAME: {"username": DEFAULT_USERNAME, "password_hash": "ignored"}}
    )
    with pytest.raises(HTTPException) as exc:
        await verify_jwt(request, _credentials(bad_token))
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid JWT token"


@pytest.mark.asyncio
async def test_verify_jwt_expired_token():
    """Reject expired tokens."""
    expired = make_token(DEFAULT_USERNAME, expiry=int(time.time()) - 10)
    request = _request_with_users(
        {DEFAULT_USERNAME: {"username": DEFAULT_USERNAME, "password_hash": "ignored"}}
    )
    with pytest.raises(HTTPException) as exc:
        await verify_jwt(request, _credentials(expired))
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid JWT token"


@pytest.mark.asyncio
async def test_verify_jwt_bad_user():
    """Reject tokens for unknown users."""
    token = make_token("bad-user")
    request = _request_with_users(
        {DEFAULT_USERNAME: {"username": DEFAULT_USERNAME, "password_hash": "ignored"}}
    )
    with pytest.raises(HTTPException) as exc:
        await verify_jwt(request, _credentials(token))
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid credentials"


@pytest.mark.asyncio
async def test_verify_jwt_missing_subject():
    """Reject tokens missing the subject claim."""
    token = jwt.encode(
        {"iat": int(time.time()), "exp": int(time.time()) + 3600},
        SECRET,
        algorithm=ALGORITHM,
    )
    request = _request_with_users(
        {DEFAULT_USERNAME: {"username": DEFAULT_USERNAME, "password_hash": "ignored"}}
    )
    with pytest.raises(HTTPException) as exc:
        await verify_jwt(request, _credentials(token))
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid JWT token"
