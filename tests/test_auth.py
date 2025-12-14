import time

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app._auth import verify_jwt
from tests.utils import make_token, DEFAULT_USERNAME, DEFAULT_PASSWORD


def _credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_verify_jwt_accepts_valid_token():
    token = make_token(DEFAULT_USERNAME, DEFAULT_PASSWORD)
    assert verify_jwt(_credentials(token)) == DEFAULT_USERNAME


def test_verify_jwt_invalid_token_signature():
    bad_token = make_token(DEFAULT_USERNAME, DEFAULT_PASSWORD, secret="bad-secret")
    with pytest.raises(HTTPException) as exc:
        verify_jwt(_credentials(bad_token))
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid JWT token"


def test_verify_jwt_expired_token():
    expired = make_token(DEFAULT_USERNAME, DEFAULT_PASSWORD, expiry=int(time.time()) - 10)
    with pytest.raises(HTTPException) as exc:
        verify_jwt(_credentials(expired))
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid JWT token"


def test_verify_jwt_bad_user():
    token = make_token("bad-user", DEFAULT_PASSWORD)
    with pytest.raises(HTTPException) as exc:
        verify_jwt(_credentials(token))
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid credentials"


def test_verify_jwt_bad_password():
    token = make_token(DEFAULT_USERNAME, "bad-password")
    with pytest.raises(HTTPException) as exc:
        verify_jwt(_credentials(token))
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid credentials"
