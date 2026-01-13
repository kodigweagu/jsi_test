"""JWT auth helpers for FastAPI endpoints."""

import os
import time
import jwt
from fastapi import Depends, HTTPException, Request
from app.repository import UserLookupError
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()

SECRET = os.environ["JWT_SECRET"]
ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = 3600


async def verify_jwt(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Validate a JWT and return the username."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid JWT token") from exc

    username = payload.get("sub")
    issued_at = payload.get("iat")
    if not username or not issued_at:
        raise HTTPException(status_code=401, detail="Invalid JWT token")

    try:
        user = await request.app.state.user_repo.get_user(username)
    except UserLookupError as exc:
        raise HTTPException(status_code=500, detail="Failed to verify credentials") from exc
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    password_changed_at = user.get("password_changed_at")
    if password_changed_at and issued_at < password_changed_at:
        raise HTTPException(status_code=401, detail="Invalid JWT token")

    return username


async def verify_admin(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Validate a JWT and require admin privileges."""
    username = await verify_jwt(request, credentials)
    try:
        user = await request.app.state.user_repo.get_user(username)
    except UserLookupError as exc:
        raise HTTPException(status_code=500, detail="Failed to verify credentials") from exc
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return username


def create_access_token(username: str, expires_in: int = TOKEN_TTL_SECONDS) -> str:
    """Create a signed JWT for the given username."""
    now = int(time.time())
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + expires_in,
    }
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)
