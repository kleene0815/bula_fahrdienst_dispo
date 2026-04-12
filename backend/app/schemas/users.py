import uuid
from datetime import datetime

from pydantic import BaseModel


class UserOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    roles: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_user(cls, user) -> "UserOut":
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            roles=[r.role for r in user.roles],
            created_at=user.created_at,
        )


class UserListItem(BaseModel):
    id: uuid.UUID
    name: str
    roles: list[str]

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_user(cls, user) -> "UserListItem":
        return cls(
            id=user.id,
            name=user.name,
            roles=[r.role for r in user.roles],
        )
