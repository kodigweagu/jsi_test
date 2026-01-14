"""API routes for data and user management."""
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Depends
from app._auth import verify_jwt, verify_admin, create_access_token
from app.repository import UserAlreadyExistsError, UserCreateError, UserLookupError

router = APIRouter()


@router.get("/GetTypes")
async def get_types(request: Request):
    """Return distinct communication types from the data store."""
    return await request.app.state.repo.get_types()


@router.post("/TimeFilter")
async def time_filter(request: Request, _username: str = Depends(verify_jwt)):
    """Filter records by communication type and time range."""
    body = await request.json()

    try:
        data_types = body["DataTypes"]
        from_time = datetime.fromisoformat(body["FromTime"])
        to_time = datetime.fromisoformat(body["ToTime"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid request") from exc

    return await request.app.state.repo.filter_by_time(
        data_types, from_time, to_time
    )


@router.post("/RegisterUser")
async def register_user(request: Request, _username: str = Depends(verify_admin)):
    """Create a new user, restricted to admin callers."""
    body = await request.json()
    try:
        new_username = body["Username"]
        new_password = body["Password"]
        is_admin = bool(body.get("IsAdmin", False))
    except (KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid request") from exc

    try:
        await request.app.state.user_repo.create_user(
            new_username,
            new_password,
            is_admin=is_admin,
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=409, detail="User already exists") from exc
    except UserCreateError as exc:
        raise HTTPException(
            status_code=500, detail="Failed to create user") from exc

    return {"status": "created"}


@router.post("/Login")
async def login(request: Request):
    """Return a JWT for valid user credentials."""
    body = await request.json()
    try:
        username = body["Username"]
        password = body["Password"]
    except (KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid request") from exc

    try:
        if not await request.app.state.user_repo.verify_password(username, password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except UserLookupError as exc:
        raise HTTPException(
            status_code=500, detail="Failed to verify credentials") from exc

    return {"access_token": create_access_token(username)}


@router.post("/ReconcileTypes")
async def reconcile_types(request: Request, _username: str = Depends(verify_admin)):
    """Rebuild the types collection from records."""
    return await request.app.state.repo.reconcile_types()
