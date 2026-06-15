from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import DisponentUser
from app.database import get_db
from app.models import AppConfig
from app.schemas.config import AppConfigOut, AppConfigUpdate

router = APIRouter(prefix="/config", tags=["config"])


@router.get("", response_model=AppConfigOut)
async def get_config(
    _: DisponentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    config = await db.get(AppConfig, 1)
    if not config:
        raise HTTPException(status_code=404, detail="Konfiguration nicht gefunden")
    return config


@router.put("", response_model=AppConfigOut)
async def update_config(
    body: AppConfigUpdate,
    _: DisponentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    config = await db.get(AppConfig, 1)
    if not config:
        config = AppConfig(id=1)
        db.add(config)

    for field, value in body.to_db_dict().items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)
    return config
