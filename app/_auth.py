import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


security = HTTPBearer()

USER_DB = {
    "admin": "your-secret-key"
}

SECRET = "jwt-signing-secret"
ALGORITHM = "HS256"


def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        payload = jwt.decode(credentials.credentials, SECRET, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid JWT token")

    username = payload.get("username")
    password = payload.get("password")

    if USER_DB.get(username) != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return username
