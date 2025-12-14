import time

import jwt

from app._auth import SECRET, ALGORITHM, USER_DB


DEFAULT_USERNAME, DEFAULT_PASSWORD = next(iter(USER_DB.items()))


def make_token(username: str, password: str, secret: str = SECRET, expiry: int | None = None) -> str:
    payload = {
        "username": username,
        "password": password,
        "exp": expiry or int(time.time()) + 3600
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)
