import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.orders import OrderOut
from app.schemas.vehicles import VehicleOut


class DriverInfo(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class TripOrderOut(BaseModel):
    sort_order: int
    order: OrderOut

    model_config = {"from_attributes": True}


class TripCreate(BaseModel):
    driver_id: uuid.UUID
    vehicle_id: uuid.UUID
    order_ids: list[uuid.UUID]
    notes: str | None = None


class TripUpdate(BaseModel):
    driver_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    order_ids: list[uuid.UUID] | None = None
    notes: str | None = None


class TripOut(BaseModel):
    id: uuid.UUID
    trip_number: int
    status: str
    driver: DriverInfo | None
    vehicle: VehicleOut | None
    qr_token: str
    notes: str | None
    orders: list[TripOrderOut]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_trip(cls, trip) -> "TripOut":
        return cls(
            id=trip.id,
            trip_number=trip.trip_number,
            status=trip.status,
            driver=DriverInfo(id=trip.driver.id, name=trip.driver.name) if trip.driver else None,
            vehicle=VehicleOut.model_validate(trip.vehicle) if trip.vehicle else None,
            qr_token=trip.qr_token,
            notes=trip.notes,
            orders=[
                TripOrderOut(
                    sort_order=to.sort_order,
                    order=OrderOut.model_validate(to.order),
                )
                for to in trip.trip_orders
            ],
            created_at=trip.created_at,
            updated_at=trip.updated_at,
        )
