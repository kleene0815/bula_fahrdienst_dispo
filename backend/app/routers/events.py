from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.events import broadcaster

router = APIRouter(prefix="/events", tags=["events"])

# EventSource unterstützt keine Custom-Header — Token kommt als Query-Parameter.
@router.get("")
async def sse_stream(
    token: Annotated[str, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Token manuell als Bearer-Credentials übergeben
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    await get_current_user(credentials, db)

    q = broadcaster.subscribe()
    return StreamingResponse(
        broadcaster.stream(q),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
