import uuid
from datetime import datetime

from pydantic import BaseModel, model_validator


class OrderCreate(BaseModel):
    trip_type: str
    destination_type: str
    destination: str
    destination_street: str | None = None
    destination_city: str | None = None
    deadline: datetime
    priority: str = "normal"
    patient_name: str | None = None
    phone: str | None = None
    companion: bool = False
    create_return_order: bool = False
    notes: str | None = None
    requester_station: str | None = None

    @model_validator(mode="after")
    def companion_requires_patient(self):
        if self.companion and not self.patient_name:
            raise ValueError("Begleitperson erfordert einen Patientennamen")
        return self


class OrderUpdate(BaseModel):
    trip_type: str | None = None
    destination_type: str | None = None
    destination: str | None = None
    destination_street: str | None = None
    destination_city: str | None = None
    deadline: datetime | None = None
    priority: str | None = None
    patient_name: str | None = None
    phone: str | None = None
    companion: bool | None = None
    create_return_order: bool | None = None
    notes: str | None = None
    requester_station: str | None = None


class OrderOut(BaseModel):
    id: uuid.UUID
    status: str
    priority: str
    trip_type: str
    destination: str
    destination_street: str | None
    destination_city: str | None
    destination_type: str
    deadline: datetime | None
    patient_name: str | None
    phone: str | None
    companion: bool
    create_return_order: bool
    notes: str | None
    requester_station: str | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
