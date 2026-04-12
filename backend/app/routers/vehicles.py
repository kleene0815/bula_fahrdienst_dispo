import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import DisponentUser
from app.database import get_db
from app.models import Vehicle
from app.schemas.vehicles import VehicleCreate, VehicleOut, VehicleUpdate

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=list[VehicleOut])
async def list_vehicles(
    _: DisponentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    active_only: bool = True,
):
    query = select(Vehicle).order_by(Vehicle.name)
    if active_only:
        query = query.where(Vehicle.active.is_(True))
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    body: VehicleCreate,
    _: DisponentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    vehicle = Vehicle(**body.model_dump())
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


@router.patch("/{vehicle_id}", response_model=VehicleOut)
async def update_vehicle(
    vehicle_id: uuid.UUID,
    body: VehicleUpdate,
    _: DisponentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Fahrzeug nicht gefunden")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(vehicle, field, value)

    await db.commit()
    await db.refresh(vehicle)
    return vehicle
