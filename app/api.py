from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime

import jwt

router = APIRouter()
security = HTTPBearer()

USER_DB = {
    "admin": "your-secret-key"
}

SECRET = "jwt-signing-secret"
ALGORITHM = "HS256"

def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid JWT token")

    username = payload.get("username")
    password = payload.get("password")

    if USER_DB.get(username) != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return username


@router.get("/GetTypes")
def get_types(request: Request):
    return request.app.state.repo.get_types()

@router.post("/TimeFilter")
async def time_filter(request: Request, username: str = Depends(verify_jwt)):
    body = await request.json()

    try:
        data_types = body["DataTypes"]
        from_time = datetime.fromisoformat(body["FromTime"])
        to_time = datetime.fromisoformat(body["ToTime"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid request")

    return request.app.state.repo.filter_by_time(
        data_types, from_time, to_time
    )
