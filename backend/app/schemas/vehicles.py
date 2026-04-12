import uuid
from datetime import datetime

from pydantic import BaseModel


class VehicleCreate(BaseModel):
    name: str
    license_plate: str
    seats: int
    type: str


class VehicleUpdate(BaseModel):
    name: str | None = None
    license_plate: str | None = None
    seats: int | None = None
    type: str | None = None
    active: bool | None = None


class VehicleOut(BaseModel):
    id: uuid.UUID
    name: str
    license_plate: str
    seats: int
    type: str
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
