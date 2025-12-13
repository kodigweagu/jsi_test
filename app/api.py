from fastapi import APIRouter, Request, HTTPException
from datetime import datetime

router = APIRouter()

@router.get("/GetTypes")
def get_types(request: Request):
    return request.app.state.repo.get_types()

@router.post("/TimeFilter")
async def time_filter(request: Request):
    body = await request.json()

    try:
        data_types = body["DataTypes"]
        from_time = datetime.fromisoformat(body["FromTime"])
        to_time = datetime.fromisoformat(body["ToTime"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid request")

    records = request.app.state.repo.filter_by_time(
        data_types, from_time, to_time
    )

    response = []
    for r in records:
        item = r["data"].copy()
        item.update({
            "id": r["id"],
            "communicationType": r["communicationType"],
            "time": r["time"].isoformat()
        })
        response.append(item)

    return response
