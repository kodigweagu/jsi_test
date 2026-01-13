"""Test helpers for auth tokens."""

import time

import jwt

from app._auth import SECRET, ALGORITHM


DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin-password"


def make_token(
    username: str,
    secret: str = SECRET,
    expiry: int | None = None,
) -> str:
    """Create a signed JWT for testing."""
    now = int(time.time())
    payload = {
        "sub": username,
        "iat": now,
        "exp": expiry or now + 3600,
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)
