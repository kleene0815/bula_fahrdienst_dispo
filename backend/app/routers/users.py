import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import CurrentUser, DisponentUser
from app.database import get_db
from app.keycloak_admin import sync_fahrer_from_keycloak
from app.models import User
from app.schemas.users import UserListItem, UserOut, UserPhoneUpdate
from fastapi import Depends

router = APIRouter(prefix="/users", tags=["users"])


def _normalize_phone(phone: str | None) -> str | None:
    if phone is None:
        return None
    phone = phone.strip()
    return phone or None


@router.get("/me", response_model=UserOut)
async def get_me(current_user: CurrentUser):
    return UserOut.from_orm_user(current_user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: UserPhoneUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    current_user.phone = _normalize_phone(body.phone)
    await db.commit()
    await db.refresh(current_user, ["roles"])
    return UserOut.from_orm_user(current_user)


@router.get("", response_model=list[UserListItem])
async def list_drivers(
    _: DisponentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await sync_fahrer_from_keycloak(db)
    result = await db.execute(
        select(User).options(selectinload(User.roles))
    )
    users = result.scalars().all()
    drivers = [u for u in users if any(r.role == "fahrer" for r in u.roles)]
    return [UserListItem.from_orm_user(u) for u in drivers]


@router.patch("/{user_id}", response_model=UserListItem)
async def update_user(
    user_id: uuid.UUID,
    body: UserPhoneUpdate,
    _: DisponentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.roles))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Nutzer nicht gefunden")
    user.phone = _normalize_phone(body.phone)
    await db.commit()
    await db.refresh(user, ["roles"])
    return UserListItem.from_orm_user(user)
