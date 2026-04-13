from typing import Annotated

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import CurrentUser, DisponentUser
from app.database import get_db
from app.keycloak_admin import sync_fahrer_from_keycloak
from app.models import User
from app.schemas.users import UserListItem, UserOut
from fastapi import Depends

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: CurrentUser):
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
